"""
Database Module for RAG System

Provides SQLite-based persistence for documents, chunks, and embeddings.
This module manages all data storage and retrieval operations for the RAG system,
including document metadata, text chunks, and vector embeddings.

Key Features:
- Document deduplication using MD5 hashing
- Efficient chunk storage with embedding blobs
- Status tracking for async processing
- Query operations for retrieval and analysis
- Statistics and monitoring capabilities

Database Schema:
- documents table: Stores document metadata and processing status
- chunks table: Stores text chunks with their embeddings
- Indexes for efficient querying by status and document_id

Typical usage:
    db = DocumentDatabase()
    doc_id = db.add_document(filename, file_path, file_size, num_pages)
    db.add_chunks(doc_id, chunks_with_embeddings)
    embeddings_df = db.get_chunks_df(doc_id)
"""

import sqlite3
import hashlib
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd
import numpy as np

class DocumentDatabase:
    """
    Manages SQLite database operations for document and embedding storage.
    
    This class provides a complete persistence layer for the RAG system,
    handling document metadata, chunk storage, and embedding management.
    """
    def __init__(self, db_path: str = "documents.db"):
        """
        Initialize the document database.
        
        Args:
            db_path: Path to SQLite database file (default: "documents.db")
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """
        Create database tables and indexes if they don't exist.
        
        Sets up:
        - documents table: Stores document metadata and processing status
        - chunks table: Stores text chunks with embeddings
        - Indexes for efficient querying
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    file_hash TEXT UNIQUE NOT NULL,
                    original_path TEXT,
                    file_size INTEGER,
                    num_pages INTEGER,
                    total_chunks INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP,
                    error_message TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id INTEGER,
                    chunk_id INTEGER,
                    text TEXT NOT NULL,
                    token_count INTEGER,
                    start_sentence INTEGER,
                    end_sentence INTEGER,
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents (id),
                    UNIQUE(document_id, chunk_id)
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_document_status ON documents(status);
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_document ON chunks(document_id);
            """)
    
    def get_file_hash(self, file_path: str) -> str:
        """
        Calculate MD5 hash of a file for deduplication.
        
        Args:
            file_path: Path to the file to hash
        
        Returns:
            str: MD5 hash hex digest of the file contents
        """
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()
    
    def add_document(self, filename: str, file_path: str, file_size: int, num_pages: int) -> int:
        """
        Add a new document to the database or return existing document ID.
        
        Uses file hash for deduplication - if the same file is uploaded twice,
        returns the existing document ID without creating a duplicate.
        
        Args:
            filename: Name of the document file
            file_path: Full path to the document file
            file_size: Size of the file in bytes
            num_pages: Number of pages in the document
        
        Returns:
            int: Document ID (either new or existing)
        """
        file_hash = self.get_file_hash(file_path)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                INSERT OR IGNORE INTO documents 
                (filename, file_hash, original_path, file_size, num_pages, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (filename, file_hash, file_path, file_size, num_pages))
            
            if cursor.rowcount == 0:
                # Document already exists
                result = conn.execute(
                    "SELECT id FROM documents WHERE file_hash = ?", (file_hash,)
                ).fetchone()
                return result[0]
            
            return cursor.lastrowid
    
    def update_document_status(self, doc_id: int, status: str, error_message: str = None):
        """
        Update the processing status of a document.
        
        Args:
            doc_id: Document ID to update
            status: New status ('pending', 'processing', 'completed', 'failed')
            error_message: Optional error message if status is 'failed'
        
        Note:
            Sets processed_at timestamp when status is 'completed'
        """
        with sqlite3.connect(self.db_path) as conn:
            if status == 'completed':
                conn.execute("""
                    UPDATE documents 
                    SET status = ?, processed_at = CURRENT_TIMESTAMP, error_message = ?
                    WHERE id = ?
                """, (status, error_message, doc_id))
            else:
                conn.execute("""
                    UPDATE documents 
                    SET status = ?, error_message = ?
                    WHERE id = ?
                """, (status, error_message, doc_id))
    
    def add_chunks(self, doc_id: int, chunks: List[Dict]):
        """
        Store text chunks and their embeddings for a document.
        
        Args:
            doc_id: Document ID the chunks belong to
            chunks: List of dictionaries containing:
                - chunk_id: Sequential chunk identifier
                - text: The chunk text content
                - token_count: Number of tokens in the chunk
                - start_sentence: Starting sentence index
                - end_sentence: Ending sentence index
                - embedding: Optional numpy array of the embedding vector
        
        Note:
            - Embeddings are stored as binary blobs for efficiency
            - Updates the document's total_chunks count after insertion
        """
        with sqlite3.connect(self.db_path) as conn:
            for chunk in chunks:
                embedding_blob = None
                if 'embedding' in chunk and chunk['embedding'] is not None:
                    embedding_blob = np.array(chunk['embedding']).tobytes()
                
                conn.execute("""
                    INSERT OR REPLACE INTO chunks 
                    (document_id, chunk_id, text, token_count, start_sentence, end_sentence, embedding)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    doc_id,
                    chunk['chunk_id'],
                    chunk['text'],
                    chunk['token_count'],
                    chunk.get('start_sentence'),
                    chunk.get('end_sentence'),
                    embedding_blob
                ))
            
            # Update total chunks count
            conn.execute("""
                UPDATE documents 
                SET total_chunks = (
                    SELECT COUNT(*) FROM chunks WHERE document_id = ?
                )
                WHERE id = ?
            """, (doc_id, doc_id))
    
    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """
        Retrieve document metadata by ID.
        
        Args:
            doc_id: Document ID to retrieve
        
        Returns:
            Dict with document metadata or None if not found
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            result = conn.execute("""
                SELECT * FROM documents WHERE id = ?
            """, (doc_id,)).fetchone()
            
            if result:
                return dict(result)
            return None
    
    def get_documents(self, status: str = None) -> List[Dict]:
        """
        Retrieve all documents, optionally filtered by status.
        
        Args:
            status: Optional status filter ('pending', 'processing', 'completed', 'failed')
        
        Returns:
            List of document dictionaries ordered by creation date (newest first)
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if status:
                results = conn.execute("""
                    SELECT * FROM documents WHERE status = ? ORDER BY created_at DESC
                """, (status,)).fetchall()
            else:
                results = conn.execute("""
                    SELECT * FROM documents ORDER BY created_at DESC
                """).fetchall()
            
            return [dict(row) for row in results]
    
    def get_chunks_df(self, doc_id: int) -> pd.DataFrame:
        """
        Retrieve all chunks and embeddings for a document as a DataFrame.
        
        This is the primary method for loading processed document data
        for RAG operations.
        
        Args:
            doc_id: Document ID to retrieve chunks for
        
        Returns:
            pd.DataFrame with columns:
                - chunk_id: Sequential chunk identifier
                - text: Chunk text content
                - token_count: Number of tokens
                - start_sentence: Starting sentence index
                - end_sentence: Ending sentence index
                - embedding: Numpy array of the embedding vector
        
        Note:
            Returns empty DataFrame if no chunks found
        """
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT chunk_id, text, token_count, start_sentence, end_sentence, embedding
                FROM chunks 
                WHERE document_id = ? 
                ORDER BY chunk_id
            """
            
            results = conn.execute(query, (doc_id,)).fetchall()
            
            if not results:
                return pd.DataFrame()
            
            data = []
            for row in results:
                chunk_data = {
                    'chunk_id': row[0],
                    'text': row[1],
                    'token_count': row[2],
                    'start_sentence': row[3],
                    'end_sentence': row[4]
                }
                
                if row[5]:  # embedding blob exists
                    embedding = np.frombuffer(row[5], dtype=np.float64)
                    chunk_data['embedding'] = embedding
                
                data.append(chunk_data)
            
            return pd.DataFrame(data)
    
    def delete_document(self, doc_id: int):
        """
        Delete a document and all associated chunks.
        
        Args:
            doc_id: Document ID to delete
        
        Note:
            Cascades to delete all associated chunks
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM chunks WHERE document_id = ?", (doc_id,))
            conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    
    def get_stats(self) -> Dict:
        """
        Get database statistics for monitoring.
        
        Returns:
            Dict containing:
                - {status}_documents: Count of documents by status
                - total_chunks: Total number of chunks across all documents
                - avg_processing_time_minutes: Average time to process completed docs
        """
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            # Document counts by status
            results = conn.execute("""
                SELECT status, COUNT(*) FROM documents GROUP BY status
            """).fetchall()
            
            for status, count in results:
                stats[f"{status}_documents"] = count
            
            # Total chunks
            result = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()
            stats['total_chunks'] = result[0]
            
            # Average processing time for completed docs
            result = conn.execute("""
                SELECT AVG(julianday(processed_at) - julianday(created_at)) * 24 * 60 
                FROM documents 
                WHERE status = 'completed' AND processed_at IS NOT NULL
            """).fetchone()
            
            if result[0]:
                stats['avg_processing_time_minutes'] = round(result[0], 2)
            
            return stats
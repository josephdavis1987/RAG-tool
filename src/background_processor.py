"""
Background Processing Module for Asynchronous Document Handling

Provides multi-threaded document processing capabilities to handle
PDF ingestion, chunking, and embedding generation without blocking
the main application thread.

Key Features:
- Asynchronous document processing queue
- Multi-threaded worker pool for parallel processing
- Progress tracking with callback notifications
- Automatic error recovery and status updates
- Database persistence for processed documents
- Document deduplication to avoid reprocessing

Architecture:
- Uses Python's threading and queue modules
- Worker threads process documents from a shared queue
- Progress callbacks provide real-time status updates
- SQLite database for persistent storage

Processing Pipeline:
1. Document queued with metadata
2. Worker thread picks up job
3. PDF text extraction
4. Text chunking with overlap
5. Embedding generation via OpenAI API
6. Storage in SQLite database
7. Status update and callback notification

Typical usage:
    processor = get_processor()  # Get singleton instance
    doc_id = processor.queue_document(file_path, filename, callback)
    status = processor.get_document_status(doc_id)
    embeddings_df = processor.get_embeddings_df(doc_id)
"""

import threading
import queue
import time
from typing import Dict, Callable, Optional
import logging
from datetime import datetime
from .pdf_loader import PDFLoader
from .embed_and_store import DocumentEmbedder
from .database import DocumentDatabase
from openai import OpenAI
import config
import os

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BackgroundProcessor:
    """
    Manages asynchronous document processing with worker threads.
    
    Provides a queue-based system for processing documents in the background,
    allowing the UI to remain responsive during lengthy embedding operations.
    """
    def __init__(self, max_workers: int = 1):
        """
        Initialize the background processor.
        
        Args:
            max_workers: Number of worker threads (default: 1)
        
        Note:
            Single worker recommended to avoid OpenAI rate limits
        """
        self.db = DocumentDatabase()
        self.pdf_loader = PDFLoader()
        self.client = OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
        self.embedder = DocumentEmbedder(self.client) if self.client else None
        
        self.max_workers = max_workers
        self.job_queue = queue.Queue()
        self.workers = []
        self.running = False
        
        # Progress callbacks
        self.progress_callbacks: Dict[int, Callable] = {}
        
        # Start workers
        self.start()
    
    def start(self):
        """
        Start worker threads for processing.
        
        Spawns daemon threads that process jobs from the queue.
        Safe to call multiple times (no-op if already running).
        """
        if self.running:
            return
            
        self.running = True
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, name=f"Worker-{i}")
            worker.daemon = True
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"Started {self.max_workers} background workers")
    
    def stop(self):
        """
        Stop all worker threads gracefully.
        
        Sends sentinel values to stop workers and waits for completion.
        Times out after 5 seconds per worker if they don't respond.
        """
        self.running = False
        
        # Add sentinel values to stop workers
        for _ in range(self.max_workers):
            self.job_queue.put(None)
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        
        logger.info("Stopped background workers")
    
    def _worker_loop(self):
        """
        Main worker thread loop.
        
        Continuously processes jobs from the queue until stopped.
        Handles exceptions gracefully to prevent thread death.
        """
        while self.running:
            try:
                job = self.job_queue.get(timeout=1)
                if job is None:  # Sentinel to stop worker
                    break
                
                self._process_job(job)
                self.job_queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def _process_job(self, job: Dict):
        """
        Process a single document job.
        
        Executes the complete pipeline:
        1. Load PDF and extract text
        2. Chunk text into overlapping segments
        3. Generate embeddings for each chunk
        4. Store in database
        5. Update status and notify callbacks
        
        Args:
            job: Dictionary containing:
                - document_id: Database document ID
                - file_path: Path to PDF file
                - filename: Original filename
        """
        doc_id = job['document_id']
        file_path = job['file_path']
        
        logger.info(f"Processing document {doc_id}: {file_path}")
        
        try:
            # Update status to processing
            self.db.update_document_status(doc_id, 'processing')
            self._notify_progress(doc_id, 'processing', 0, "Starting document processing...")
            
            # Load PDF
            self._notify_progress(doc_id, 'processing', 10, "Loading PDF...")
            with open(file_path, 'rb') as f:
                document_text = self.pdf_loader.load_pdf(f)
            
            if not document_text:
                raise Exception("Failed to extract text from PDF")
            
            # Chunk text
            self._notify_progress(doc_id, 'processing', 30, "Chunking text...")
            chunks = self.embedder.chunk_text(document_text)
            logger.info(f"Created {len(chunks)} chunks for document {doc_id}")
            
            # Generate embeddings
            self._notify_progress(doc_id, 'processing', 40, f"Generating embeddings for {len(chunks)} chunks...")
            embeddings_data = []
            
            for i, chunk in enumerate(chunks):
                try:
                    response = self.client.embeddings.create(
                        model=config.EMBEDDING_MODEL,
                        input=chunk['text']
                    )
                    
                    embedding = response.data[0].embedding
                    chunk['embedding'] = embedding
                    embeddings_data.append(chunk)
                    
                    # Update progress
                    progress = 40 + int((i + 1) / len(chunks) * 50)
                    self._notify_progress(doc_id, 'processing', progress, 
                                        f"Generated embedding {i+1}/{len(chunks)}")
                    
                except Exception as e:
                    logger.error(f"Error generating embedding for chunk {i}: {e}")
                    # Continue with other chunks
                    continue
            
            if not embeddings_data:
                raise Exception("Failed to generate any embeddings")
            
            # Store in database
            self._notify_progress(doc_id, 'processing', 90, "Saving to database...")
            self.db.add_chunks(doc_id, embeddings_data)
            
            # Mark as completed
            self.db.update_document_status(doc_id, 'completed')
            self._notify_progress(doc_id, 'completed', 100, 
                                f"Processing complete! Generated {len(embeddings_data)} embeddings.")
            
            logger.info(f"Successfully processed document {doc_id}")
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error processing document {doc_id}: {error_msg}")
            self.db.update_document_status(doc_id, 'failed', error_msg)
            self._notify_progress(doc_id, 'failed', 0, f"Processing failed: {error_msg}")
    
    def _notify_progress(self, doc_id: int, status: str, progress: int, message: str):
        """
        Send progress update to registered callback.
        
        Args:
            doc_id: Document ID
            status: Current status ('processing', 'completed', 'failed')
            progress: Progress percentage (0-100)
            message: Status message
        """
        if doc_id in self.progress_callbacks:
            try:
                self.progress_callbacks[doc_id](doc_id, status, progress, message)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")
    
    def queue_document(self, file_path: str, filename: str = None, 
                      progress_callback: Callable = None) -> int:
        """
        Queue a document for background processing.
        
        Adds document to database and processing queue. If document
        was already processed (same hash), returns immediately.
        
        Args:
            file_path: Path to PDF file
            filename: Display name (defaults to basename)
            progress_callback: Function called with (doc_id, status, progress, message)
        
        Returns:
            int: Document ID for tracking
        
        Raises:
            Exception: If OpenAI client not configured or file not found
        """
        if not self.client:
            raise Exception("OpenAI client not configured")
        
        if not os.path.exists(file_path):
            raise Exception(f"File not found: {file_path}")
        
        filename = filename or os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # Get document info
        with open(file_path, 'rb') as f:
            doc_info = self.pdf_loader.get_document_info(f)
            num_pages = doc_info.get('num_pages', 0)
        
        # Add to database
        doc_id = self.db.add_document(filename, file_path, file_size, num_pages)
        
        # Check if already processed
        doc = self.db.get_document_by_id(doc_id)
        if doc and doc['status'] == 'completed':
            logger.info(f"Document {doc_id} already processed")
            if progress_callback:
                progress_callback(doc_id, 'completed', 100, "Document already processed")
            return doc_id
        
        # Register progress callback
        if progress_callback:
            self.progress_callbacks[doc_id] = progress_callback
        
        # Queue for processing
        job = {
            'document_id': doc_id,
            'file_path': file_path,
            'filename': filename
        }
        
        self.job_queue.put(job)
        logger.info(f"Queued document {doc_id} for processing")
        
        return doc_id
    
    def get_document_status(self, doc_id: int) -> Optional[Dict]:
        """
        Get current status of a document.
        
        Args:
            doc_id: Document ID
        
        Returns:
            Dict with document metadata and status, or None if not found
        """
        return self.db.get_document_by_id(doc_id)
    
    def get_embeddings_df(self, doc_id: int):
        """
        Retrieve processed embeddings for a document.
        
        Args:
            doc_id: Document ID
        
        Returns:
            pd.DataFrame with chunks and embeddings
        """
        return self.db.get_chunks_df(doc_id)
    
    def get_queue_size(self) -> int:
        """
        Get number of jobs waiting in queue.
        
        Returns:
            int: Number of pending jobs
        """
        return self.job_queue.qsize()
    
    def list_documents(self, status: str = None):
        """
        List all documents, optionally filtered by status.
        
        Args:
            status: Filter by status ('pending', 'processing', 'completed', 'failed')
        
        Returns:
            List of document dictionaries
        """
        return self.db.get_documents(status)
    
    def delete_document(self, doc_id: int):
        """
        Delete a document and its associated data.
        
        Args:
            doc_id: Document ID to delete
        
        Note:
            Also removes from progress callbacks if registered
        """
        # Remove from progress callbacks
        if doc_id in self.progress_callbacks:
            del self.progress_callbacks[doc_id]
        
        return self.db.delete_document(doc_id)
    
    def get_stats(self):
        """
        Get system statistics.
        
        Returns:
            Dict containing:
                - Document counts by status
                - Total chunks
                - Queue size
                - Active worker count
        """
        stats = self.db.get_stats()
        stats['queue_size'] = self.get_queue_size()
        stats['workers_running'] = len([w for w in self.workers if w.is_alive()])
        return stats

# Global processor instance
_processor = None

def get_processor() -> BackgroundProcessor:
    """
    Get or create the singleton BackgroundProcessor instance.
    
    Returns:
        BackgroundProcessor: Global processor instance
    """
    global _processor
    if _processor is None:
        _processor = BackgroundProcessor()
    return _processor

def shutdown_processor():
    """
    Shutdown the global processor instance.
    
    Stops all workers and cleans up resources.
    """
    global _processor
    if _processor:
        _processor.stop()
        _processor = None
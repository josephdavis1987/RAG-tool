"""
Document Embedding and Retrieval Module

Handles text chunking, embedding generation, and similarity search operations.
This module is the core of the RAG system's retrieval capabilities.

Key Features:
- Semantic-aware text chunking with configurable overlap
- OpenAI embedding generation for each chunk
- Cosine similarity search with neighbor context inclusion
- Token counting for context window management

Chunking Strategy:
- Splits text at sentence boundaries to preserve meaning
- Maintains overlap between chunks for context continuity
- Tracks token counts to stay within model limits
- Preserves sentence indices for citation purposes

Typical usage:
    embedder = DocumentEmbedder(openai_client)
    chunks = embedder.chunk_text(document_text)
    embeddings_df = embedder.generate_embeddings(chunks)
    similar = embedder.find_similar_chunks(query, embeddings_df)
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
import tiktoken
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity
import streamlit as st
import config

class DocumentEmbedder:
    """
    Manages document chunking, embedding generation, and similarity search.
    
    This class provides the retrieval component of the RAG system,
    converting documents into searchable vector representations.
    """
    def __init__(self, openai_client: OpenAI):
        """
        Initialize the DocumentEmbedder with OpenAI client.
        
        Args:
            openai_client: Configured OpenAI client for API calls
        
        Note:
            Uses configuration from config.py for model and chunk settings
        """
        self.client = openai_client
        self.encoding = tiktoken.encoding_for_model(config.EMBEDDING_MODEL)
        self.chunk_size = config.CHUNK_SIZE
        self.overlap = config.CHUNK_OVERLAP
        
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None) -> List[Dict]:
        """
        Split text into overlapping chunks at sentence boundaries.
        
        Implements semantic-aware chunking that respects sentence boundaries
        to preserve meaning and context. Includes configurable overlap to
        maintain continuity between chunks.
        
        Args:
            text: Document text to chunk
            chunk_size: Maximum tokens per chunk (default: config.CHUNK_SIZE)
            overlap: Token overlap between chunks (default: config.CHUNK_OVERLAP)
        
        Returns:
            List of dictionaries containing:
                - chunk_id: Sequential identifier
                - text: Chunk text content
                - token_count: Number of tokens in chunk
                - start_sentence: Index of first sentence
                - end_sentence: Index of last sentence
        
        Note:
            Overlap is approximated by including ~overlap/50 sentences
            from the previous chunk
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.overlap
        
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        current_tokens = 0
        chunk_id = 0
        
        for i, sentence in enumerate(sentences):
            sentence_tokens = len(self.encoding.encode(sentence))
            
            if current_tokens + sentence_tokens > chunk_size and current_chunk:
                chunks.append({
                    'chunk_id': chunk_id,
                    'text': current_chunk.strip(),
                    'token_count': current_tokens,
                    'start_sentence': i - len(current_chunk.split('. ')) + 1,
                    'end_sentence': i - 1
                })
                
                overlap_sentences = current_chunk.split('. ')[-max(1, overlap // 50):]
                current_chunk = '. '.join(overlap_sentences) + '. ' + sentence + '. '
                current_tokens = len(self.encoding.encode(current_chunk))
                chunk_id += 1
            else:
                current_chunk += sentence + '. '
                current_tokens += sentence_tokens
        
        if current_chunk.strip():
            chunks.append({
                'chunk_id': chunk_id,
                'text': current_chunk.strip(),
                'token_count': current_tokens,
                'start_sentence': len(sentences) - len(current_chunk.split('. ')),
                'end_sentence': len(sentences) - 1
            })
        
        return chunks
    
    def generate_embeddings(self, chunks: List[Dict]) -> pd.DataFrame:
        """
        Generate OpenAI embeddings for text chunks.
        
        Processes chunks through OpenAI's embedding API to create
        vector representations for similarity search.
        
        Args:
            chunks: List of chunk dictionaries from chunk_text()
        
        Returns:
            pd.DataFrame with columns:
                - chunk_id: Sequential identifier
                - text: Chunk text content
                - token_count: Number of tokens
                - start_sentence: Starting sentence index
                - end_sentence: Ending sentence index
                - embedding: Vector representation (1536 dimensions)
        
        Note:
            - Shows progress bar in Streamlit UI
            - Continues processing even if individual chunks fail
            - Uses text-embedding-3-small model by default
        """
        embeddings_data = []
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, chunk in enumerate(chunks):
            try:
                response = self.client.embeddings.create(
                    model=config.EMBEDDING_MODEL,
                    input=chunk['text']
                )
                
                embedding = response.data[0].embedding
                
                embeddings_data.append({
                    'chunk_id': chunk['chunk_id'],
                    'text': chunk['text'],
                    'token_count': chunk['token_count'],
                    'start_sentence': chunk['start_sentence'],
                    'end_sentence': chunk['end_sentence'],
                    'embedding': embedding
                })
                
                progress = (i + 1) / len(chunks)
                progress_bar.progress(progress)
                status_text.text(f"Generating embeddings: {i+1}/{len(chunks)} chunks processed")
                
            except Exception as e:
                st.error(f"Error generating embedding for chunk {i}: {str(e)}")
                continue
        
        progress_bar.empty()
        status_text.empty()
        
        return pd.DataFrame(embeddings_data)
    
    def find_similar_chunks(self, query: str, embeddings_df: pd.DataFrame, 
                          top_k: int = 5, include_neighbors: bool = True) -> List[Dict]:
        """
        Find chunks most similar to a query using cosine similarity.
        
        Performs semantic search by comparing query embedding with
        document chunk embeddings. Optionally includes neighboring
        chunks for additional context.
        
        Args:
            query: User's question or search query
            embeddings_df: DataFrame with chunk embeddings
            top_k: Number of most similar chunks to retrieve
            include_neighbors: Whether to include adjacent chunks (±1)
        
        Returns:
            List of dictionaries containing:
                - chunk_id: Chunk identifier
                - text: Chunk text content
                - similarity: Cosine similarity score (0-1)
                - token_count: Number of tokens
            Sorted by similarity score (highest first)
        
        Note:
            Including neighbors helps maintain document flow and context,
            especially important for legislative texts where provisions
            may span multiple chunks.
        """
        try:
            query_response = self.client.embeddings.create(
                model=config.EMBEDDING_MODEL,
                input=query
            )
            query_embedding = np.array(query_response.data[0].embedding).reshape(1, -1)
            
            chunk_embeddings = np.vstack(embeddings_df['embedding'].values)
            
            similarities = cosine_similarity(query_embedding, chunk_embeddings)[0]
            
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            selected_chunks = set(top_indices)
            
            if include_neighbors:
                for idx in top_indices:
                    chunk_id = embeddings_df.iloc[idx]['chunk_id']
                    
                    neighbor_before = embeddings_df[embeddings_df['chunk_id'] == chunk_id - 1]
                    neighbor_after = embeddings_df[embeddings_df['chunk_id'] == chunk_id + 1]
                    
                    if not neighbor_before.empty:
                        selected_chunks.add(neighbor_before.index[0])
                    if not neighbor_after.empty:
                        selected_chunks.add(neighbor_after.index[0])
            
            results = []
            for idx in sorted(selected_chunks):
                row = embeddings_df.iloc[idx]
                results.append({
                    'chunk_id': row['chunk_id'],
                    'text': row['text'],
                    'similarity': similarities[idx],
                    'token_count': row['token_count']
                })
            
            return sorted(results, key=lambda x: x['similarity'], reverse=True)
            
        except Exception as e:
            st.error(f"Error finding similar chunks: {str(e)}")
            return []
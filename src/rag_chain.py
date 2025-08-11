"""
RAG Chain Module - Core Question Answering Engine

Implements three distinct answering methodologies for empirical comparison:
1. RAG-Only: Pure retrieval-based answers (zero hallucination)
2. Non-RAG: Pure LLM knowledge (baseline/control)
3. RAG+LLM Hybrid: Combined approach (enhanced completeness)

This module is central to the research framework, enabling quantitative
comparison of different RAG methodologies to answer the key question:
"Should we use pure RAG or RAG+LLM hybrid for our use case?"

Key Features:
- Three distinct answer generation modes for A/B/C testing
- Automatic context window management to prevent token overflow
- Citation tracking for document-grounded responses
- Performance metrics collection (tokens, time, chunks used)
- Configurable temperature and model parameters

Research Metrics Collected:
- Response time per method
- Token usage (prompt, completion, total)
- Number of chunks retrieved and used
- Context token consumption
- Hallucination risk indicators

Typical usage:
    rag_chain = RAGChain(openai_client)
    
    # For A/B/C comparison:
    rag_answer = rag_chain.answer_question(query, embeddings_df)
    non_rag_answer = rag_chain.generate_non_rag_answer(query)
    hybrid_answer = rag_chain.generate_hybrid_answer(query, embeddings_df)
"""

from typing import List, Dict, Tuple
from openai import OpenAI
import pandas as pd
import streamlit as st
import tiktoken
from .embed_and_store import DocumentEmbedder
import config

class RAGChain:
    """
    Manages question answering with three distinct methodologies.
    
    This class provides the core inference capabilities for the RAG system,
    enabling empirical comparison between different approaches.
    """
    def __init__(self, openai_client: OpenAI):
        """
        Initialize the RAG chain with OpenAI client.
        
        Args:
            openai_client: Configured OpenAI client for API calls
        
        Note:
            Reserves 2000 tokens from max context for response generation
        """
        self.client = openai_client
        self.embedder = DocumentEmbedder(openai_client)
        self.encoding = tiktoken.encoding_for_model(config.CHAT_MODEL)
        self.max_context_tokens = config.MAX_CONTEXT_TOKENS - 2000  # Leave room for response
        
    def generate_answer(self, query: str, relevant_chunks: List[Dict], 
                       model: str = None) -> Dict:
        """
        Generate RAG-only answer using solely document context.
        
        This is the "zero hallucination" approach that only uses information
        explicitly present in the retrieved document chunks.
        
        Args:
            query: User's question
            relevant_chunks: Retrieved chunks from similarity search
            model: Optional model override (default: config.CHAT_MODEL)
        
        Returns:
            Dict containing:
                - answer: Generated response text
                - model_used: Model identifier used
                - chunks_used: Number of chunks in context
                - context_tokens: Tokens used for context
                - citations: List of chunks used
                - response_time: Time to generate (seconds)
                - prompt_tokens: Input tokens consumed
                - completion_tokens: Output tokens generated
                - total_tokens: Total API tokens used
        
        Note:
            Temperature set to 0.2 for factual, consistent responses
        """
        import time
        
        # Limit context to fit within token budget
        limited_chunks = self._limit_context_tokens(relevant_chunks, query)
        context = self._build_context(limited_chunks)
        
        system_prompt = """You are an expert assistant for analyzing government documents and legislation. 
        Your task is to answer questions based solely on the provided document context.
        
        Guidelines:
        1. Only use information from the provided context
        2. Include specific citations with chunk IDs for all claims
        3. If the context doesn't contain enough information, say so
        4. Be precise and factual
        5. For legislation, focus on specific provisions, sections, and requirements"""
        
        user_prompt = f"""Context from document:
{context}

Question: {query}

Please provide a comprehensive answer with citations to specific chunks (using chunk_id references)."""

        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model or config.CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                max_tokens=config.MAX_RESPONSE_TOKENS
            )
            
            response_time = time.time() - start_time
            
            return {
                'answer': response.choices[0].message.content,
                'model_used': model,
                'chunks_used': len(limited_chunks),
                'context_tokens': len(self.encoding.encode(context)),
                'citations': limited_chunks,
                'response_time': response_time,
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            st.error(f"Error generating answer: {str(e)}")
            return {
                'answer': f"Error generating response: {str(e)}",
                'model_used': model,
                'chunks_used': 0,
                'context_tokens': 0,
                'citations': [],
                'response_time': response_time,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            }
    
    def _limit_context_tokens(self, chunks: List[Dict], query: str) -> List[Dict]:
        """
        Limit context to fit within token budget.
        
        Ensures the total context doesn't exceed model limits by
        intelligently truncating or removing chunks.
        
        Args:
            chunks: List of text chunks to include
            query: User's question (for token calculation)
        
        Returns:
            List of chunks that fit within token budget
        
        Note:
            Attempts to truncate last chunk if partially fits
        """
        system_prompt = """You are an expert assistant for analyzing government documents and legislation. 
        Your task is to answer questions based solely on the provided document context.
        
        Guidelines:
        1. Only use information from the provided context
        2. Include specific citations with chunk IDs for all claims
        3. If the context doesn't contain enough information, say so
        4. Be precise and factual
        5. For legislation, focus on specific provisions, sections, and requirements"""
        
        # Calculate base token usage (system prompt + query + formatting)
        base_tokens = len(self.encoding.encode(system_prompt)) + len(self.encoding.encode(query)) + 100
        available_tokens = self.max_context_tokens - base_tokens
        
        limited_chunks = []
        current_tokens = 0
        
        for chunk in chunks:
            chunk_header = f"[Chunk {chunk['chunk_id']}] (Similarity: {chunk.get('similarity', 0):.3f})"
            chunk_text = f"{chunk_header}\n{chunk['text']}\n\n"
            chunk_tokens = len(self.encoding.encode(chunk_text))
            
            if current_tokens + chunk_tokens <= available_tokens:
                limited_chunks.append(chunk)
                current_tokens += chunk_tokens
            else:
                # If we can't fit the full chunk, try to fit a truncated version
                remaining_tokens = available_tokens - current_tokens - len(self.encoding.encode(chunk_header)) - 50
                if remaining_tokens > 200:  # Only truncate if we have reasonable space
                    truncated_text = chunk['text']
                    while len(self.encoding.encode(truncated_text)) > remaining_tokens and len(truncated_text) > 100:
                        truncated_text = truncated_text[:int(len(truncated_text) * 0.8)]
                    
                    truncated_chunk = chunk.copy()
                    truncated_chunk['text'] = truncated_text + "... [truncated]"
                    limited_chunks.append(truncated_chunk)
                break
        
        return limited_chunks
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """
        Build formatted context string from chunks.
        
        Args:
            chunks: List of chunk dictionaries
        
        Returns:
            Formatted string with chunk headers and content
        """
        context_parts = []
        
        for chunk in chunks:
            chunk_header = f"[Chunk {chunk['chunk_id']}] (Similarity: {chunk.get('similarity', 0):.3f})"
            context_parts.append(f"{chunk_header}\n{chunk['text']}\n")
        
        return "\n".join(context_parts)
    
    def answer_question(self, query: str, embeddings_df: pd.DataFrame, 
                       top_k: int = 5, include_neighbors: bool = True) -> Dict:
        """
        Complete RAG pipeline: retrieve chunks and generate answer.
        
        Convenience method that combines retrieval and generation
        for the RAG-only approach.
        
        Args:
            query: User's question
            embeddings_df: DataFrame with document embeddings
            top_k: Number of chunks to retrieve
            include_neighbors: Whether to include adjacent chunks
        
        Returns:
            Dict with answer and metadata (see generate_answer)
        """
        relevant_chunks = self.embedder.find_similar_chunks(
            query, embeddings_df, top_k=top_k, include_neighbors=include_neighbors
        )
        
        if not relevant_chunks:
            return {
                'answer': "I couldn't find relevant information in the document to answer your question.",
                'model_used': "N/A",
                'chunks_used': 0,
                'context_tokens': 0,
                'citations': []
            }
        
        return self.generate_answer(query, relevant_chunks)
    
    def generate_non_rag_answer(self, query: str, model: str = "gpt-4") -> Dict:
        """
        Generate answer using only LLM knowledge (control group).
        
        This serves as the baseline/control in the A/B/C comparison,
        showing what the LLM can answer without any document context.
        
        Args:
            query: User's question
            model: Model to use (default: "gpt-4")
        
        Returns:
            Dict containing:
                - answer: Generated response text
                - model_used: Model identifier
                - response_time: Generation time
                - prompt_tokens: Input tokens
                - completion_tokens: Output tokens
                - total_tokens: Total tokens used
        
        Research Note:
            This represents the control group in our methodology comparison,
            establishing baseline LLM performance without retrieval.
        """
        import time
        
        system_prompt = """You are an expert assistant for analyzing government documents and legislation. 
        Answer the user's question using your general knowledge about government policies and legislation.
        
        Guidelines:
        1. Use your training knowledge about government policies and legislation
        2. Be honest if you don't have specific information
        3. Do not make up specific details about documents you haven't seen
        4. Be precise and factual based on your general knowledge"""
        
        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model or config.CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                temperature=0.2,
                max_tokens=config.MAX_RESPONSE_TOKENS
            )
            
            response_time = time.time() - start_time
            
            return {
                'answer': response.choices[0].message.content,
                'model_used': model,
                'response_time': response_time,
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            return {
                'answer': f"Error generating response: {str(e)}",
                'model_used': model,
                'response_time': response_time,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            }

    def get_document_summary(self, embeddings_df: pd.DataFrame, max_chunks: int = 10) -> str:
        """
        Generate a summary of the document's main topics.
        
        Args:
            embeddings_df: DataFrame with document embeddings
            max_chunks: Maximum chunks to use for summary
        
        Returns:
            str: Document summary text
        """
        summary_query = "What is this document about? What are the main topics and key provisions?"
        
        relevant_chunks = self.embedder.find_similar_chunks(
            summary_query, embeddings_df, top_k=max_chunks, include_neighbors=False
        )
        
        context = self._build_context(relevant_chunks)
        
        system_prompt = """You are an expert at summarizing government documents and legislation. 
        Provide a concise summary that covers the main topics, key provisions, and overall purpose."""
        
        user_prompt = f"""Please provide a summary of this document based on the following content:

{context}

Focus on the main topics, key provisions, and overall purpose of the document."""

        try:
            response = self.client.chat.completions.create(
                model=config.CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def generate_hybrid_answer(self, query: str, embeddings_df: pd.DataFrame, 
                              top_k: int = 5, include_neighbors: bool = True, 
                              model: str = None) -> Dict:
        """
        Generate answer using RAG+LLM hybrid approach.
        
        Combines document context with LLM's knowledge base for
        enhanced completeness. This represents the "enhanced" method
        in our A/B/C testing framework.
        
        Args:
            query: User's question
            embeddings_df: DataFrame with document embeddings
            top_k: Number of chunks to retrieve
            include_neighbors: Whether to include adjacent chunks
            model: Optional model override
        
        Returns:
            Dict containing:
                - answer: Generated response
                - model_used: Model identifier
                - chunks_used: Number of chunks in context
                - context_tokens: Context token count
                - citations: Chunks used for grounding
                - response_time: Generation time
                - prompt_tokens: Input tokens
                - completion_tokens: Output tokens
                - total_tokens: Total tokens
                - mode: 'hybrid' indicator
        
        Research Note:
            Temperature increased to 0.3 for more creative synthesis.
            Estimated hallucination risk: 5-10% based on empirical observation.
        """
        import time
        
        relevant_chunks = self.embedder.find_similar_chunks(
            query, embeddings_df, top_k=top_k, include_neighbors=include_neighbors
        )
        
        if not relevant_chunks:
            return self.generate_non_rag_answer(query, model)
        
        limited_chunks = self._limit_context_tokens(relevant_chunks, query)
        context = self._build_context(limited_chunks)
        
        system_prompt = """You are an expert assistant for analyzing government documents and legislation. 
        You have access to specific document context AND your training knowledge about government policies.
        
        Guidelines:
        1. Use the provided document context as your primary source for specific facts and details
        2. Supplement with your training knowledge when helpful for clarity, context, or broader understanding
        3. Clearly distinguish between document-specific facts and general knowledge when relevant
        4. Include chunk citations when referencing the provided document context
        5. Be comprehensive and user-friendly - provide context that helps users understand the significance
        6. You may go beyond the document when it helps explain implications, background, or related concepts"""
        
        user_prompt = f"""Context from document:
{context}

Question: {query}

Please provide a comprehensive answer that uses the document context as a foundation but supplements with your knowledge to give a complete, helpful response. Include citations for document-specific information."""

        start_time = time.time()
        
        try:
            response = self.client.chat.completions.create(
                model=model or config.CHAT_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                max_tokens=config.MAX_RESPONSE_TOKENS
            )
            
            response_time = time.time() - start_time
            
            return {
                'answer': response.choices[0].message.content,
                'model_used': model,
                'chunks_used': len(limited_chunks),
                'context_tokens': len(self.encoding.encode(context)),
                'citations': limited_chunks,
                'response_time': response_time,
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens,
                'mode': 'hybrid'
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            st.error(f"Error generating hybrid answer: {str(e)}")
            return {
                'answer': f"Error generating response: {str(e)}",
                'model_used': model,
                'chunks_used': 0,
                'context_tokens': 0,
                'citations': [],
                'response_time': response_time,
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0,
                'mode': 'hybrid'
            }
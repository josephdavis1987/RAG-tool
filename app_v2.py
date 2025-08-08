import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from background_processor import get_processor, shutdown_processor
from rag_chain import RAGChain
from openai import OpenAI
import config

def initialize_openai_client():
    if not config.OPENAI_API_KEY:
        st.error("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
        st.stop()
    
    return OpenAI(api_key=config.OPENAI_API_KEY)

def progress_callback(doc_id, status, progress, message):
    if 'progress_info' not in st.session_state:
        st.session_state.progress_info = {}
    
    st.session_state.progress_info[doc_id] = {
        'status': status,
        'progress': progress,
        'message': message,
        'timestamp': datetime.now()
    }

def main():
    st.set_page_config(
        page_title="RAG PDF Intelligence Assistant v2",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 RAG-Powered PDF Intelligence Assistant v2")
    st.markdown("**Background Processing Edition** - Upload documents and query instantly!")
    
    # Initialize
    client = initialize_openai_client()
    processor = get_processor()
    rag_chain = RAGChain(client)
    
    # Initialize session state
    if 'selected_doc_id' not in st.session_state:
        st.session_state.selected_doc_id = None
    if 'progress_info' not in st.session_state:
        st.session_state.progress_info = {}
    if 'ab_results' not in st.session_state:
        st.session_state.ab_results = None
    
    # Sidebar
    with st.sidebar:
        st.header("📤 Document Upload")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file", 
            type="pdf",
            help="Upload government bills, policy documents, or other large PDFs"
        )
        
        if uploaded_file is not None:
            if st.button("Queue for Processing", type="primary"):
                # Create uploads directory if it doesn't exist
                uploads_dir = "uploads"
                os.makedirs(uploads_dir, exist_ok=True)
                
                # Save uploaded file permanently in uploads directory
                file_path = os.path.join(uploads_dir, uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                
                try:
                    doc_id = processor.queue_document(
                        file_path, 
                        uploaded_file.name,
                        progress_callback=progress_callback
                    )
                    st.success(f"Document queued with ID: {doc_id}")
                    st.session_state.selected_doc_id = doc_id
                        
                except Exception as e:
                    st.error(f"Error queueing document: {str(e)}")
                    # Clean up file only on error
                    if os.path.exists(file_path):
                        os.remove(file_path)
        
        st.divider()
        
        # Document Library
        st.header("📚 Document Library")
        docs = processor.list_documents()
        
        if docs:
            for doc in docs:
                status_emoji = {
                    'pending': '⏳',
                    'processing': '🔄', 
                    'completed': '✅',
                    'failed': '❌'
                }.get(doc['status'], '❓')
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    if st.button(
                        f"{status_emoji} {doc['filename'][:25]}...",
                        key=f"doc_{doc['id']}",
                        help=f"Status: {doc['status']}, Chunks: {doc.get('total_chunks', 0)}"
                    ):
                        st.session_state.selected_doc_id = doc['id']
                
                with col2:
                    if st.button("🗑️", key=f"del_{doc['id']}", help="Delete"):
                        processor.delete_document(doc['id'])
                        st.rerun()
        else:
            st.info("No documents uploaded yet")
        
        st.divider()
        
        # System Stats
        st.header("📊 System Stats")
        stats = processor.get_stats()
        for key, value in stats.items():
            if key.endswith('_documents'):
                status = key.replace('_documents', '')
                st.metric(f"{status.title()} Docs", value)
            elif key == 'total_chunks':
                st.metric("Total Chunks", value)
            elif key == 'queue_size':
                st.metric("Queue Size", value)
    
    # Main content
    if st.session_state.selected_doc_id:
        doc_id = st.session_state.selected_doc_id
        doc = processor.get_document_status(doc_id)
        
        if not doc:
            st.error("Document not found")
            st.session_state.selected_doc_id = None
            st.rerun()
        
        st.subheader(f"📄 {doc['filename']}")
        
        # Compact document status
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        with col1:
            status_color = {
                'pending': 'orange',
                'processing': 'blue',
                'completed': 'green', 
                'failed': 'red'
            }.get(doc['status'], 'gray')
            st.markdown(f":{status_color}[{doc['status'].title()}]")
        
        with col2:
            if doc.get('total_chunks'):
                st.markdown(f"**{doc['total_chunks']:,}** chunks")
        
        with col3:
            if doc['status'] == 'completed' and doc.get('processed_at'):
                st.markdown("**Ready!** ⚡")
        
        with col4:
            # Quick stats preview
            embeddings_df = processor.get_embeddings_df(doc_id)
            if not embeddings_df.empty and 'token_count' in embeddings_df.columns:
                total_tokens = embeddings_df['token_count'].sum()
                if total_tokens > 1000000:
                    st.markdown(f"**{total_tokens/1000000:.1f}M** tokens")
                elif total_tokens > 1000:
                    st.markdown(f"**{total_tokens/1000:.0f}K** tokens")
                else:
                    st.markdown(f"**{total_tokens:,}** tokens")
        
        # Progress tracking for processing documents
        if doc['status'] == 'processing' and doc_id in st.session_state.progress_info:
            progress_info = st.session_state.progress_info[doc_id]
            
            progress_bar = st.progress(progress_info['progress'] / 100)
            st.text(progress_info['message'])
            
            # Auto-refresh for processing documents
            time.sleep(1)
            st.rerun()
        
        # Error display
        if doc['status'] == 'failed' and doc.get('error_message'):
            st.error(f"Processing failed: {doc['error_message']}")
        
        # Q&A Interface for completed documents
        if doc['status'] == 'completed':
            st.divider()
            st.subheader("💬 Ask Questions")
            
            # Load embeddings
            embeddings_df = processor.get_embeddings_df(doc_id)
            
            if embeddings_df.empty:
                st.error("No embeddings found for this document")
            else:
                # Compact Document Statistics
                with st.expander("📊 Document Statistics", expanded=False):
                    col_stats1, col_stats2, col_stats3 = st.columns(3)
                    
                    with col_stats1:
                        st.metric("Total Chunks", len(embeddings_df))
                    with col_stats2:
                        if 'token_count' in embeddings_df.columns:
                            st.metric("Avg Tokens/Chunk", f"{embeddings_df['token_count'].mean():.0f}")
                    with col_stats3:
                        if 'token_count' in embeddings_df.columns:
                            total_tokens = embeddings_df['token_count'].sum()
                            if total_tokens > 1000000:
                                st.metric("Total Tokens", f"{total_tokens/1000000:.1f}M")
                            else:
                                st.metric("Total Tokens", f"{total_tokens:,}")
                
                # Main Q&A interface
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    query = st.text_area(
                        "Enter your question:",
                        placeholder="e.g., What are the main provisions? What are the tax implications?",
                        height=100
                    )
                    
                    col_ask, col_ab, col_summary = st.columns([1, 1, 1])
                    
                    with col_ask:
                        if st.button("Ask Question (RAG Only)", disabled=not query.strip()):
                            if query.strip():
                                with st.spinner("Generating RAG answer..."):
                                    result = rag_chain.answer_question(
                                        query, 
                                        embeddings_df,
                                        top_k=5,
                                        include_neighbors=True
                                    )
                                
                                st.subheader("🎯 RAG Answer")
                                st.write(result['answer'])
                                
                                with st.expander("📋 Answer Details"):
                                    st.write(f"**Model Used:** {result['model_used']}")
                                    st.write(f"**Chunks Used:** {result['chunks_used']}")
                                    st.write(f"**Context Tokens:** {result['context_tokens']}")
                                    st.write(f"**Response Time:** {result.get('response_time', 0):.2f}s")
                                    st.write(f"**Total Tokens:** {result.get('total_tokens', 0)}")
                                
                                if result['citations']:
                                    with st.expander("📚 Source Citations"):
                                        for i, citation in enumerate(result['citations'][:5]):
                                            st.write(f"**Chunk {citation['chunk_id']}** (Similarity: {citation.get('similarity', 0):.3f})")
                                            preview_text = citation['text'][:300] + "..." if len(citation['text']) > 300 else citation['text']
                                            st.text(preview_text)
                                            st.divider()
                    
                    with col_ab:
                        if st.button("A/B Compare", type="primary", disabled=not query.strip()):
                            if query.strip():
                                # Generate all three answers simultaneously
                                with st.spinner("Generating RAG, Non-RAG, and Hybrid answers..."):
                                    rag_result = rag_chain.answer_question(
                                        query, 
                                        embeddings_df,
                                        top_k=5,
                                        include_neighbors=True
                                    )
                                    
                                    non_rag_result = rag_chain.generate_non_rag_answer(query)
                                    
                                    hybrid_result = rag_chain.generate_hybrid_answer(
                                        query,
                                        embeddings_df,
                                        top_k=5,
                                        include_neighbors=True
                                    )
                                    
                                    # Store all results in session state
                                    st.session_state.ab_results = {
                                        'query': query,
                                        'rag_result': rag_result,
                                        'non_rag_result': non_rag_result,
                                        'hybrid_result': hybrid_result
                                    }
                                    
                                    # Initialize comparison mode if not set
                                    if 'comparison_mode' not in st.session_state:
                                        st.session_state.comparison_mode = 'non_rag'
                    
                    with col_summary:
                        if st.button("Generate Document Summary"):
                            with st.spinner("Generating summary..."):
                                summary = rag_chain.get_document_summary(embeddings_df)
                            
                            st.subheader("📄 Document Summary")
                            st.write(summary)
                
                with col2:
                    st.subheader("🔍 Sample Chunks")
                    if len(embeddings_df) > 0:
                        sample_chunks = embeddings_df.head(3)
                        for idx, row in sample_chunks.iterrows():
                            with st.expander(f"Chunk {row['chunk_id']} ({row.get('token_count', '?')} tokens)"):
                                preview_text = row['text'][:200] + "..." if len(row['text']) > 200 else row['text']
                                st.text(preview_text)
        
        # Display A/B comparison results if available
        if st.session_state.ab_results:
            st.divider()
            st.subheader("🆚 A/B Comparison Results")
            st.write(f"**Query:** {st.session_state.ab_results['query']}")
            
            # Initialize comparison mode if not set
            if 'comparison_mode' not in st.session_state:
                st.session_state.comparison_mode = 'non_rag'
            
            # Create full-width two columns for side-by-side comparison
            rag_col, comparison_col = st.columns(2)
            
            rag_result = st.session_state.ab_results['rag_result']
            non_rag_result = st.session_state.ab_results['non_rag_result']
            hybrid_result = st.session_state.ab_results['hybrid_result']
            
            # Display RAG answer
            with rag_col:
                # Add a label to match the right column structure
                st.write("")
                st.write("")  # Empty space to align with dropdown height
                st.write("")  # Empty space to align with dropdown height
                st.write("")  # Empty space to align with dropdown height
                st.write("")  # Empty space to align with dropdown height
                
                st.subheader("🔍 RAG Answer")
                
                # Compact metrics right above answer
                metric_col1, metric_col2, metric_col3 = st.columns([1, 1, 1])
                with metric_col1:
                    st.caption(f"⏱️ {rag_result.get('response_time', 0):.2f}s • 🎯 {rag_result['chunks_used']}ch")
                with metric_col2:
                    st.caption(f"📊 {rag_result.get('total_tokens', 0)}tok • 📝 {rag_result['context_tokens']}ctx")
                with metric_col3:
                    st.caption(f"✍️ {rag_result.get('completion_tokens', 0)}gen")
                
                st.write(rag_result['answer'])
            
            # Display comparison column with toggle
            with comparison_col:
                # Mode toggle switch positioned in the comparison column
                st.selectbox(
                    "View Mode:",
                    options=['non_rag', 'hybrid'],
                    format_func=lambda x: '🧠 Non-RAG LLM' if x == 'non_rag' else '🔗 RAG + LLM Hybrid',
                    index=0 if st.session_state.comparison_mode == 'non_rag' else 1,
                    key="comparison_mode_select",
                    on_change=lambda: setattr(st.session_state, 'comparison_mode', st.session_state.comparison_mode_select)
                )
                
                # Display the selected answer type
                if st.session_state.comparison_mode == 'non_rag':
                    st.subheader("🧠 Non-RAG Answer")
                    
                    # Compact metrics right above answer
                    metric_col1, metric_col2 = st.columns(2)
                    with metric_col1:
                        st.caption(f"⏱️ {non_rag_result.get('response_time', 0):.2f}s • 💭 Pure LLM")
                    with metric_col2:
                        st.caption(f"📊 {non_rag_result.get('total_tokens', 0)}tok • ✍️ {non_rag_result.get('completion_tokens', 0)}gen")
                    
                    st.write(non_rag_result['answer'])
                    
                else:  # hybrid mode
                    st.subheader("🔗 RAG + LLM Hybrid")
                    
                    # Compact metrics right above answer
                    metric_col1, metric_col2, metric_col3 = st.columns([1, 1, 1])
                    with metric_col1:
                        st.caption(f"⏱️ {hybrid_result.get('response_time', 0):.2f}s • 🎯 {hybrid_result.get('chunks_used', 0)}ch")
                    with metric_col2:
                        st.caption(f"📊 {hybrid_result.get('total_tokens', 0)}tok • 📝 {hybrid_result.get('context_tokens', 0)}ctx")
                    with metric_col3:
                        st.caption(f"✍️ {hybrid_result.get('completion_tokens', 0)}gen")
                    
                    st.write(hybrid_result['answer'])
            
            # Clear results button
            if st.button("Clear Comparison Results"):
                st.session_state.ab_results = None
                st.rerun()
    
    else:
        st.info("👈 Please upload a document or select one from the library")
        
        st.subheader("🎯 About This Tool")
        st.markdown("""
        This RAG-powered assistant features **background processing** for analyzing large documents:
        
        - **📤 Upload & Go**: Documents process in background - no waiting required
        - **💾 Persistent Storage**: Process once, query forever  
        - **🔍 Smart Retrieval**: Hybrid semantic + neighbor context search
        - **💡 GPT-4 Answers**: Detailed responses with source citations
        - **📊 Document Library**: Browse and manage processed documents
        - **⚡ Instant Access**: Query completed documents immediately
        
        Perfect for government bills, policy documents, and technical reports.
        """)
    
    # Auto-refresh processing documents
    processing_docs = [doc_id for doc_id, info in st.session_state.progress_info.items() 
                      if info.get('status') == 'processing']
    
    if processing_docs:
        time.sleep(2)
        st.rerun()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
    finally:
        # Cleanup on app shutdown
        pass
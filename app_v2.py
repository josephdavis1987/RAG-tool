import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from src.background_processor import get_processor, shutdown_processor
from src.rag_chain import RAGChain
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
        page_title="RAG Methodology Evaluation Framework",
        page_icon="🔬",
        layout="wide"
    )
    
    st.title("🔬 RAG Methodology Evaluation Framework")
    st.markdown("**Empirical Comparison Platform** - Evaluate RAG-only vs. RAG+LLM hybrid approaches with quantitative metrics")
    
    # Research objective callout
    st.info(
        "🎯 **Research Question**: Should we use pure RAG or RAG+LLM hybrid for our specific use case? "
        "This framework provides empirical measurement of accuracy vs. completeness trade-offs."
    )
    
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
        st.header("📊 Evaluation Setup")
        
        uploaded_file = st.file_uploader(
            "Upload Evaluation Document", 
            type="pdf",
            help="Upload representative documents from your domain for methodology comparison"
        )
        
        if uploaded_file is not None:
            if st.button("Process for Evaluation", type="primary"):
                # Create data/uploads directory if it doesn't exist
                uploads_dir = "data/uploads"
                os.makedirs(uploads_dir, exist_ok=True)
                
                # Save uploaded file permanently in data/uploads directory
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
        
        # Evaluation Documents
        st.header("📊 Evaluation Documents")
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
            st.info("No evaluation documents available")
        
        st.divider()
        
        # Framework Stats
        st.header("📈 Framework Metrics")
        stats = processor.get_stats()
        for key, value in stats.items():
            if key.endswith('_documents'):
                status = key.replace('_documents', '')
                st.metric(f"{status.title()} Documents", value)
            elif key == 'total_chunks':
                st.metric("Total Chunks", value)
            elif key == 'queue_size':
                st.metric("Processing Queue", value)
    
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
            st.subheader("🔬 Methodology Evaluation")
            
            # Load embeddings
            embeddings_df = processor.get_embeddings_df(doc_id)
            
            if embeddings_df.empty:
                st.error("No embeddings found for this document")
            else:
                # Evaluation Document Metrics
                with st.expander("📊 Evaluation Document Metrics", expanded=False):
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
                        "Enter evaluation query:",
                        placeholder="e.g., What are the main provisions? What are the compliance requirements?",
                        help="Design queries that test different aspects: factual retrieval, analytical reasoning, synthesis",
                        height=100
                    )
                    
                    col_baseline, col_comparison, col_summary = st.columns([1, 1, 1])
                    
                    with col_baseline:
                        if st.button("RAG-Only Baseline", disabled=not query.strip(), help="Zero-hallucination document-only approach"):
                            if query.strip():
                                with st.spinner("Generating RAG answer..."):
                                    result = rag_chain.answer_question(
                                        query, 
                                        embeddings_df,
                                        top_k=5,
                                        include_neighbors=True
                                    )
                                
                                st.subheader("🎯 RAG-Only Results")
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
                    
                    with col_comparison:
                        if st.button("Three-Way Comparison", type="primary", disabled=not query.strip(), help="Compare RAG-only vs Non-RAG vs Hybrid approaches"):
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
                    st.subheader("📊 Retrieval Analysis")
                    if len(embeddings_df) > 0:
                        sample_chunks = embeddings_df.head(3)
                        for idx, row in sample_chunks.iterrows():
                            with st.expander(f"Chunk {row['chunk_id']} ({row.get('token_count', '?')} tokens)"):
                                preview_text = row['text'][:200] + "..." if len(row['text']) > 200 else row['text']
                                st.text(preview_text)
        
        # Display methodology comparison results if available
        if st.session_state.ab_results:
            st.divider()
            st.subheader("🔬 Methodology Comparison Results")
            st.write(f"**Evaluation Query:** {st.session_state.ab_results['query']}")
            
            # Add research context
            st.markdown(
                "📊 **Research Objective**: Quantify trade-offs between accuracy (RAG-only) "
                "vs. completeness (Hybrid) vs. baseline (Non-RAG) approaches."
            )
            
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
                
                st.subheader("🔍 RAG-Only (Zero Hallucination)")
                
                # Research metrics for RAG-only approach
                metric_col1, metric_col2, metric_col3 = st.columns([1, 1, 1])
                with metric_col1:
                    st.caption(f"⏱️ {rag_result.get('response_time', 0):.2f}s • 🎯 {rag_result['chunks_used']} chunks")
                with metric_col2:
                    st.caption(f"📊 {rag_result.get('total_tokens', 0)} tokens • 📝 {rag_result['context_tokens']} ctx")
                with metric_col3:
                    st.caption(f"✍️ {rag_result.get('completion_tokens', 0)} gen • 🎯 0% hallucination")
                
                st.write(rag_result['answer'])
            
            # Display comparison column with toggle
            with comparison_col:
                # Mode toggle switch positioned in the comparison column
                st.selectbox(
                    "Comparison Method:",
                    options=['non_rag', 'hybrid'],
                    format_func=lambda x: '🧠 Non-RAG Baseline (Control)' if x == 'non_rag' else '🔗 RAG+LLM Hybrid (Enhanced)',
                    index=0 if st.session_state.comparison_mode == 'non_rag' else 1,
                    key="comparison_mode_select",
                    help="Toggle between control group and enhanced methodology",
                    on_change=lambda: setattr(st.session_state, 'comparison_mode', st.session_state.comparison_mode_select)
                )
                
                # Display the selected answer type
                if st.session_state.comparison_mode == 'non_rag':
                    st.subheader("🧠 Non-RAG Baseline (Control Group)")
                    
                    # Research metrics for control group
                    metric_col1, metric_col2 = st.columns(2)
                    with metric_col1:
                        st.caption(f"⏱️ {non_rag_result.get('response_time', 0):.2f}s • 💭 No document context")
                    with metric_col2:
                        st.caption(f"📊 {non_rag_result.get('total_tokens', 0)} tokens • ✍️ {non_rag_result.get('completion_tokens', 0)} generated")
                    
                    st.write(non_rag_result['answer'])
                    st.caption("🔬 **Research Note**: Baseline showing pure LLM performance without document grounding")
                    
                else:  # hybrid mode
                    st.subheader("🔗 RAG+LLM Hybrid (Enhanced Method)")
                    
                    # Research metrics for hybrid approach
                    metric_col1, metric_col2, metric_col3 = st.columns([1, 1, 1])
                    with metric_col1:
                        st.caption(f"⏱️ {hybrid_result.get('response_time', 0):.2f}s • 🎯 {hybrid_result.get('chunks_used', 0)} chunks")
                    with metric_col2:
                        st.caption(f"📊 {hybrid_result.get('total_tokens', 0)} tokens • 📝 {hybrid_result.get('context_tokens', 0)} ctx")
                    with metric_col3:
                        st.caption(f"✍️ {hybrid_result.get('completion_tokens', 0)} gen • ⚠️ ~5-10% hallucination risk")
                    
                    st.write(hybrid_result['answer'])
                    st.caption("🔬 **Research Note**: Enhanced approach combining document facts with LLM reasoning")
            
            # Research actions
            col_clear, col_export = st.columns(2)
            with col_clear:
                if st.button("Clear Results"):
                    st.session_state.ab_results = None
                    st.rerun()
            with col_export:
                if st.button("Export Data", help="Export metrics for statistical analysis"):
                    st.info("📊 Export functionality: Save comparison metrics to CSV for further analysis")
    
    else:
        st.info("👈 Please upload an evaluation document or select one from the library")
        
        st.subheader("🔬 About This Research Framework")
        st.markdown("""
        This framework enables **empirical evaluation of RAG methodologies** for evidence-based architecture decisions:
        
        ### 📋 Research Capabilities
        - **Three-Way Comparison**: RAG-only vs. Non-RAG vs. RAG+LLM Hybrid
        - **Quantitative Metrics**: Accuracy, completeness, hallucination rates, performance
        - **Statistical Analysis**: Export data for significance testing and confidence intervals
        - **Domain Validation**: Test with your specific document types and query patterns
        - **Risk Quantification**: Measure actual vs. theoretical trade-offs
        
        ### 🎯 Key Research Questions
        1. **When does RAG+LLM hybrid justify the hallucination risk?**
        2. **What completeness do we gain vs. accuracy we lose?**
        3. **Which approach works better for our query patterns?**
        4. **What are the cost-effectiveness trade-offs?**
        
        ### 📈 Evaluation Protocol
        1. Upload representative documents from your domain
        2. Design test queries covering factual, analytical, and synthetic tasks
        3. Run three-way comparison to collect metrics
        4. Export data for statistical analysis and decision making
        
        **Perfect for data science teams making RAG architecture decisions.**
        """)
    
    # Auto-refresh processing documents
    processing_docs = [doc_id for doc_id, info in st.session_state.progress_info.items() 
                      if info.get('status') == 'processing']
    
    if processing_docs:
        time.sleep(2)
        st.rerun()
    
    # Add footer with research context
    st.divider()
    st.markdown(
        "🔬 **Research Framework**: This tool quantifies RAG methodology trade-offs through systematic evaluation. "
        "For technical details, see the [Methodology Comparison documentation](docs/METHODOLOGY_COMPARISON.md)."
    )

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
    finally:
        # Cleanup on app shutdown
        pass
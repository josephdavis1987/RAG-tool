import streamlit as st
import pandas as pd
from openai import OpenAI
from pdf_loader import PDFLoader
from embed_and_store import DocumentEmbedder
from rag_chain import RAGChain
import config

def initialize_openai_client():
    if not config.OPENAI_API_KEY:
        st.error("OpenAI API key not found. Please set OPENAI_API_KEY in your .env file.")
        st.stop()
    
    return OpenAI(api_key=config.OPENAI_API_KEY)

def main():
    st.set_page_config(
        page_title="RAG PDF Intelligence Assistant",
        page_icon="📄",
        layout="wide"
    )
    
    st.title("📄 RAG-Powered PDF Intelligence Assistant")
    st.markdown("Upload large PDF documents and ask questions using natural language")
    
    client = initialize_openai_client()
    pdf_loader = PDFLoader()
    embedder = DocumentEmbedder(client)
    rag_chain = RAGChain(client)
    
    if 'embeddings_df' not in st.session_state:
        st.session_state.embeddings_df = None
    if 'document_text' not in st.session_state:
        st.session_state.document_text = ""
    if 'document_info' not in st.session_state:
        st.session_state.document_info = {}
    
    with st.sidebar:
        st.header("📤 Upload Document")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file", 
            type="pdf",
            help="Upload government bills, policy documents, or other large PDFs"
        )
        
        if uploaded_file is not None:
            if st.button("Process PDF", type="primary"):
                with st.spinner("Loading PDF..."):
                    document_text = pdf_loader.load_pdf(uploaded_file)
                    document_info = pdf_loader.get_document_info(uploaded_file)
                    
                    st.session_state.document_text = document_text
                    st.session_state.document_info = document_info
                
                if document_text:
                    with st.spinner("Chunking text..."):
                        chunks = embedder.chunk_text(document_text)
                        st.success(f"Created {len(chunks)} chunks")
                    
                    with st.spinner("Generating embeddings..."):
                        embeddings_df = embedder.generate_embeddings(chunks)
                        st.session_state.embeddings_df = embeddings_df
                        st.success(f"Generated embeddings for {len(embeddings_df)} chunks")
        
        if st.session_state.document_info:
            st.subheader("📊 Document Info")
            info = st.session_state.document_info
            st.metric("Pages", info.get("num_pages", "Unknown"))
            
            if st.session_state.embeddings_df is not None:
                st.metric("Chunks", len(st.session_state.embeddings_df))
        
        st.subheader("⚙️ Settings")
        top_k = st.slider("Number of chunks to retrieve", 3, 10, config.TOP_K_CHUNKS)
        include_neighbors = st.checkbox("Include neighbor chunks", config.INCLUDE_NEIGHBOR_CHUNKS)
    
    if st.session_state.embeddings_df is not None:
        st.success("✅ Document processed and ready for questions!")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("💬 Ask Questions")
            
            query = st.text_area(
                "Enter your question about the document:",
                placeholder="e.g., What are the main provisions of this bill? What are the tax implications?",
                height=100
            )
            
            col_ask, col_summary = st.columns([1, 1])
            
            with col_ask:
                if st.button("Ask Question", type="primary", disabled=not query.strip()):
                    if query.strip():
                        with st.spinner("Searching document and generating answer..."):
                            result = rag_chain.answer_question(
                                query, 
                                st.session_state.embeddings_df,
                                top_k=top_k,
                                include_neighbors=include_neighbors
                            )
                        
                        st.subheader("🎯 Answer")
                        st.write(result['answer'])
                        
                        with st.expander("📋 Answer Details"):
                            st.write(f"**Model Used:** {result['model_used']}")
                            st.write(f"**Chunks Used:** {result['chunks_used']}")
                            st.write(f"**Context Tokens:** {result['context_tokens']}")
                        
                        if result['citations']:
                            with st.expander("📚 Source Citations"):
                                for i, citation in enumerate(result['citations'][:5]):
                                    st.write(f"**Chunk {citation['chunk_id']}** (Similarity: {citation.get('similarity', 0):.3f})")
                                    st.text(citation['text'][:300] + "..." if len(citation['text']) > 300 else citation['text'])
                                    st.divider()
            
            with col_summary:
                if st.button("Generate Document Summary"):
                    with st.spinner("Generating document summary..."):
                        summary = rag_chain.get_document_summary(st.session_state.embeddings_df)
                    
                    st.subheader("📄 Document Summary")
                    st.write(summary)
        
        with col2:
            st.subheader("📈 Document Statistics")
            if st.session_state.embeddings_df is not None and len(st.session_state.embeddings_df) > 0:
                df = st.session_state.embeddings_df
                
                st.metric("Total Chunks", len(df))
                if 'token_count' in df.columns:
                    st.metric("Avg Tokens per Chunk", f"{df['token_count'].mean():.0f}")
                    st.metric("Total Tokens", f"{df['token_count'].sum():,}")
                else:
                    st.warning("Embedding generation failed - check API key")
                
                st.subheader("🔍 Sample Chunks")
                if len(df) > 0:
                    sample_chunks = df.head(3)
                    for idx, row in sample_chunks.iterrows():
                        with st.expander(f"Chunk {row['chunk_id']} ({row['token_count']} tokens)"):
                            st.text(row['text'][:200] + "..." if len(row['text']) > 200 else row['text'])
    
    else:
        st.info("👈 Please upload a PDF document to get started")
        
        st.subheader("🎯 About This Tool")
        st.markdown("""
        This RAG-powered assistant is designed for analyzing large government documents:
        
        - **📄 PDF Processing**: Handles 50-200+ page documents
        - **🧠 Smart Chunking**: Semantic-aware text splitting with overlap
        - **🔍 Hybrid Retrieval**: Combines similarity search with local context
        - **💡 GPT-4 Answers**: Provides detailed responses with source citations
        - **📊 Document Analysis**: Perfect for bills, acts, and policy documents
        """)

if __name__ == "__main__":
    main()
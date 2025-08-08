# Claude AI Assistant Context

## Project Overview
This is a RAG-powered PDF intelligence assistant with advanced A/B/C testing capabilities, designed to analyze government bills and lengthy documents (50+ pages). The system uses OpenAI GPT-4 for answering and OpenAI embeddings for document retrieval, with three distinct modes for comprehensive comparison: RAG Only, Non-RAG LLM, and RAG+LLM Hybrid.

## Environment Details
- **Conda Environment**: `RAG_env` (Python 3.11)
- **Primary Use Case**: Government legislation analysis (bills, acts, policy documents)
- **Target Document Size**: 50+ pages (optimized for 100-200+ page documents)
- **A/B/C Testing**: Three-way comparison between RAG Only, Non-RAG LLM, and RAG+LLM Hybrid modes

## Key Design Decisions
1. **Hybrid Retrieval**: Combines semantic similarity with local neighbor chunks (±1 context window)
2. **Simple Storage**: Uses pandas DataFrame for vector storage (not FAISS/ChromaDB for faster development)
3. **OpenAI Integration**: GPT-4 for reasoning, OpenAI embeddings for retrieval
4. **PDF Focus**: Supports PDF only (not Word docs) based on government document formats
5. **A/B/C Testing Framework**: Built-in three-way comparison to quantify value-add of different approaches

## Architecture Components
- `pdf_loader.py`: PDF text extraction
- `embed_and_store.py`: Chunking strategy with overlap + embedding generation
- `rag_chain.py`: Three answer modes: RAG Only + Non-RAG LLM + RAG+LLM Hybrid with comprehensive metrics
- `app_v2.py`: Streamlit frontend with A/B/C testing interface and instant mode switching
- `background_processor.py`: Asynchronous document processing
- `database.py`: SQLite persistence for documents and embeddings
- `config.py`: Model settings and API configuration

## Development Notes
- **Status**: ✅ COMPLETED - Production ready system with A/B testing
- **Chunking**: Semantic-aware splitting respecting paragraph/sentence boundaries
- **Citations**: Answers include source references with chunk IDs
- **Context Window**: Tunable neighbor chunk inclusion for sequential document flow
- **Background Processing**: SQLite persistence eliminates re-processing waits
- **Token Management**: Automatic context limiting prevents API errors
- **A/B/C Testing**: Three-way comparison with comprehensive performance metrics

## A/B/C Testing Features
- **Three-way comparison**: RAG Only (left) vs toggleable right column (Non-RAG LLM / RAG+LLM Hybrid)
- **Simultaneous generation**: All three answers generated at once for efficiency
- **Instant switching**: Toggle between Non-RAG and Hybrid without regeneration
- **Comprehensive metrics**: Response time, token usage, chunks used, context tokens, generated tokens
- **Perfect alignment**: Visual layout optimized for stakeholder presentations
- **Mode-specific insights**: Each approach clearly labeled with distinct advantages

## Commands to Remember
- **Activate Environment**: `conda activate RAG_env`
- **Run Main Application**: `streamlit run app_v2.py` (A/B/C testing version)
- **Test Pipeline**: `python test_cli.py` (quick validation)
- **Test Background**: `python test_background.py` (full system test)
- **Generate Test PDF**: `python create_test_pdf.py`

## API Requirements
- OpenAI API key required for both embeddings and LLM calls
- Store in `.env` file as `OPENAI_API_KEY`

## Deployment
- **Status**: ✅ DEPLOYMENT READY
- **Streamlit Cloud**: Configured with config.toml and secrets management
- **GitHub Integration**: Repository ready for automatic deployments
- **Private Repository**: Supported for secure hosting
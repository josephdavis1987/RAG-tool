# Claude AI Assistant Context

## Project Overview
This is a RAG-powered PDF intelligence assistant with A/B testing capabilities, designed to analyze government bills and lengthy documents (50+ pages). The system uses OpenAI GPT-4 for answering and OpenAI embeddings for document retrieval, with a built-in comparison feature to evaluate RAG value-add.

## Environment Details
- **Conda Environment**: `RAG_env` (Python 3.11)
- **Primary Use Case**: Government legislation analysis (bills, acts, policy documents)
- **Target Document Size**: 50+ pages (optimized for 100-200+ page documents)
- **A/B Testing**: Side-by-side RAG vs Non-RAG answer comparison

## Key Design Decisions
1. **Hybrid Retrieval**: Combines semantic similarity with local neighbor chunks (±1 context window)
2. **Simple Storage**: Uses pandas DataFrame for vector storage (not FAISS/ChromaDB for faster development)
3. **OpenAI Integration**: GPT-4 for reasoning, OpenAI embeddings for retrieval
4. **PDF Focus**: Supports PDF only (not Word docs) based on government document formats
5. **A/B Testing Framework**: Built-in comparison to quantify RAG value-add

## Architecture Components
- `pdf_loader.py`: PDF text extraction
- `embed_and_store.py`: Chunking strategy with overlap + embedding generation
- `rag_chain.py`: Hybrid retrieval + GPT-4 answer generation with citations + Non-RAG comparison
- `app_v2.py`: Streamlit frontend with A/B testing interface
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
- **A/B Testing**: Side-by-side RAG vs Non-RAG comparison with performance metrics

## A/B Testing Features
- **Side-by-side comparison**: RAG answer vs Non-RAG answer
- **Performance metrics**: Response time, token usage, chunks used, context tokens, generated tokens
- **Compact display**: Clean metrics layout prevents text wrapping
- **Real-time comparison**: Both answers generated simultaneously

## Commands to Remember
- **Activate Environment**: `conda activate RAG_env`
- **Run Main Application**: `streamlit run app_v2.py` (A/B testing version)
- **Test Pipeline**: `python test_cli.py` (quick validation)
- **Test Background**: `python test_background.py` (full system test)
- **Generate Test PDF**: `python create_test_pdf.py`

## API Requirements
- OpenAI API key required for both embeddings and LLM calls
- Store in `.env` file as `OPENAI_API_KEY`
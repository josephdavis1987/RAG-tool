# RAG-Powered PDF Intelligence Assistant with A/B Testing

A Retrieval-Augmented Generation (RAG) system for querying large PDF documents using natural language. Built specifically for analyzing government bills and lengthy documents (50+ pages). Features built-in A/B testing to compare RAG vs Non-RAG performance.

## Features

- **A/B Testing**: Side-by-side RAG vs Non-RAG answer comparison with performance metrics
- **Background Processing**: Upload documents and get immediate feedback - no waiting!
- **SQLite Persistence**: Process documents once, query forever
- **PDF Document Processing**: Upload and parse large PDF files (100+ pages)
- **Intelligent Chunking**: Semantic-aware text splitting with overlap for context preservation
- **Hybrid Retrieval**: Combines semantic similarity with local neighbor context
- **OpenAI Integration**: Uses GPT-4 for answering and OpenAI embeddings for retrieval
- **Citation Support**: Answers include references to source document sections
- **Document Library**: Browse, manage, and delete processed documents
- **Real-time Progress**: Watch document processing from 0% to 100%
- **Token Management**: Automatic context limiting prevents API errors

## Quick Start

### Environment Setup
```bash
conda activate RAG_env
pip install -r requirements.txt
```

### Configuration
1. Create `.env` file with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

### Run the Application
```bash
# Launch the background processing version
streamlit run app_v2.py

# Or test the CLI tools
python test_cli.py          # Quick pipeline test
python test_background.py   # Background processing test
```

## Usage

### Web Interface
1. **Upload**: Choose PDF → Click "Queue for Processing" → Immediate confirmation
2. **Monitor**: Watch real-time progress in sidebar (0% → 100%)
3. **Browse**: Document library shows all uploads with status indicators
4. **Select**: Click any completed document to activate Q&A mode
5. **Query**: Ask questions using three options:
   - **Ask Question (RAG Only)**: Standard RAG-powered answer
   - **A/B Compare**: Side-by-side RAG vs Non-RAG comparison with metrics
   - **Generate Document Summary**: Overview of the document
6. **Analyze**: Compare performance metrics (response time, tokens, chunks used)
7. **Manage**: Delete documents you no longer need

### A/B Testing Interface
- **Side-by-side comparison**: RAG answer (left) vs Non-RAG answer (right)
- **Performance metrics**: Displayed above each answer for easy comparison
  - ⏱️ Response time
  - 🎯 Chunks used (RAG only)
  - 📊 Total tokens
  - 📝 Context tokens (RAG) / 💭 Pure LLM (Non-RAG)
  - ✍️ Generated tokens
- **Real-time generation**: Both answers generated simultaneously
- **Value-add analysis**: Quantify when RAG provides meaningful improvement

### CLI Development Tools
```bash
# Test core pipeline with sample document
python test_cli.py

# Test background processing system  
python test_background.py

# Create custom test PDF
python create_test_pdf.py
```

## Target Use Case

Designed for analyzing government legislation such as:
- Bills and acts (e.g., Inflation Reduction Act)
- Policy documents
- Legal texts
- Technical reports

## Architecture

### Core Components
- `pdf_loader.py`: PDF parsing and text extraction
- `embed_and_store.py`: Text chunking and embedding generation  
- `rag_chain.py`: Question answering with retrieval
- `config.py`: Configuration and settings

### Background Processing System
- `database.py`: SQLite storage for documents and embeddings
- `background_processor.py`: Asynchronous document processing with threading
- `app.py`: Streamlit frontend with background processing integration

### Development & Testing
- `test_cli.py`: CLI testing framework for rapid iteration
- `test_background.py`: Background processing system tests
- `create_test_pdf.py`: Generate realistic test documents

## Requirements

- Python 3.11
- OpenAI API key
- Conda environment: `RAG_env`

## File Structure
```
RAG tool 1.0/
├── app_v2.py              # Main Streamlit application (with background processing)
├── background_processor.py # Background processing system
├── database.py            # SQLite storage and management
├── pdf_loader.py          # PDF text extraction
├── embed_and_store.py     # Chunking and embedding generation
├── rag_chain.py           # Question answering with citations
├── config.py              # Configuration settings
├── test_cli.py            # CLI testing framework
├── test_background.py     # Background processing tests
├── create_test_pdf.py     # Test document generator
├── requirements.txt       # Python dependencies
├── .env.example           # Environment template
└── uploads/               # Uploaded documents storage (created automatically)
```

## Key Benefits

- **No Wait Time**: Background processing eliminates 15-minute embedding waits
- **One-Time Processing**: Documents stored permanently after first upload
- **Scale Ready**: Handles 50-200+ page government documents efficiently
- **Production Ready**: SQLite persistence, error handling, progress tracking
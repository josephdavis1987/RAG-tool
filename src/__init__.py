"""
RAG Methodology Evaluation Framework
===================================

Core implementation modules for empirical RAG comparison.

This package provides a complete framework for evaluating different RAG approaches
through systematic A/B/C testing. It enables data science teams to make evidence-based
decisions about RAG architecture by quantitatively comparing:

1. **RAG-Only**: Pure retrieval-augmented generation (zero hallucination)
2. **Non-RAG**: Baseline LLM performance without document context
3. **RAG+LLM Hybrid**: Enhanced approach combining retrieval with LLM knowledge

## Package Structure

### Core Modules
- **pdf_loader**: PDF document text extraction and metadata handling
- **database**: SQLite persistence for documents, chunks, and embeddings
- **embed_and_store**: Text chunking, embedding generation, and similarity search
- **rag_chain**: Three-method question answering engine with metrics collection
- **background_processor**: Asynchronous document processing with progress tracking

### Key Features
- Document deduplication using content hashing
- Semantic-aware chunking with configurable overlap
- Multi-threaded background processing
- Real-time progress tracking and status updates
- Comprehensive performance metrics collection
- Three-way methodology comparison interface

### Research Applications
Perfect for data science teams evaluating:
- RAG architecture decisions
- Hallucination vs. completeness trade-offs
- Cost-effectiveness analysis
- Domain-specific performance validation
- Statistical significance testing

## Quick Start

```python
from src.background_processor import get_processor
from src.rag_chain import RAGChain
from openai import OpenAI

# Initialize components
client = OpenAI(api_key="your-key")
processor = get_processor()
rag_chain = RAGChain(client)

# Process document
doc_id = processor.queue_document("document.pdf")
embeddings_df = processor.get_embeddings_df(doc_id)

# Compare methodologies
rag_answer = rag_chain.answer_question(query, embeddings_df)
non_rag_answer = rag_chain.generate_non_rag_answer(query)
hybrid_answer = rag_chain.generate_hybrid_answer(query, embeddings_df)
```

For detailed documentation, see docs/METHODOLOGY_COMPARISON.md
"""

__version__ = "1.0.0"
__description__ = "Empirical evaluation framework for RAG methodology selection"
__author__ = "RAG Research Team"

# Import key classes for easier access
from .pdf_loader import PDFLoader
from .database import DocumentDatabase
from .embed_and_store import DocumentEmbedder
from .rag_chain import RAGChain
from .background_processor import BackgroundProcessor, get_processor, shutdown_processor

__all__ = [
    'PDFLoader',
    'DocumentDatabase', 
    'DocumentEmbedder',
    'RAGChain',
    'BackgroundProcessor',
    'get_processor',
    'shutdown_processor'
]
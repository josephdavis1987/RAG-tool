#!/usr/bin/env python3

import os
import sys
from src.pdf_loader import PDFLoader
from src.embed_and_store import DocumentEmbedder
from src.rag_chain import RAGChain
from openai import OpenAI
import config

def test_pipeline(pdf_path: str):
    print(f"🔄 Testing RAG pipeline with: {pdf_path}")
    
    # Initialize
    if not config.OPENAI_API_KEY:
        print("❌ OpenAI API key not found in .env file")
        return False
        
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    pdf_loader = PDFLoader()
    embedder = DocumentEmbedder(client)
    rag_chain = RAGChain(client)
    
    # Test PDF loading
    print("\n📄 Loading PDF...")
    with open(pdf_path, 'rb') as f:
        document_text = pdf_loader.load_pdf(f)
        document_info = pdf_loader.get_document_info(f)
    
    if not document_text:
        print("❌ Failed to load PDF")
        return False
        
    print(f"✅ Loaded PDF: {document_info.get('num_pages', '?')} pages")
    print(f"   Text length: {len(document_text):,} characters")
    
    # Test chunking
    print("\n✂️  Chunking text...")
    chunks = embedder.chunk_text(document_text)
    print(f"✅ Created {len(chunks)} chunks")
    print(f"   Avg tokens per chunk: {sum(c['token_count'] for c in chunks) / len(chunks):.0f}")
    
    # Test embedding (just first 3 chunks for speed)
    print(f"\n🔗 Testing embedding generation (first 3 chunks)...")
    test_chunks = chunks[:3]
    embeddings_df = embedder.generate_embeddings(test_chunks)
    
    if embeddings_df.empty:
        print("❌ Failed to generate embeddings")
        return False
        
    print(f"✅ Generated embeddings for {len(embeddings_df)} chunks")
    
    # Test retrieval
    print("\n🔍 Testing retrieval...")
    test_query = "What are the main provisions of this legislation?"
    similar_chunks = embedder.find_similar_chunks(test_query, embeddings_df, top_k=2)
    print(f"✅ Found {len(similar_chunks)} similar chunks")
    
    # Test answer generation
    print("\n💭 Testing answer generation...")
    result = rag_chain.generate_answer(test_query, similar_chunks)
    print(f"✅ Generated answer ({len(result['answer'])} characters)")
    print(f"   Model: {result['model_used']}")
    print(f"   Chunks used: {result['chunks_used']}")
    
    print(f"\n📝 Sample Answer:")
    print("-" * 50)
    print(result['answer'][:500] + "..." if len(result['answer']) > 500 else result['answer'])
    print("-" * 50)
    
    return True

def create_test_pdf():
    print("📄 Creating test PDF...")
    try:
        from create_test_pdf import create_test_bill
        filename = create_test_bill()
        print(f"✅ Created test PDF: {filename}")
        return filename
    except ImportError:
        print("❌ reportlab not installed. Run: pip install reportlab")
        return None

def main():
    print("🧪 RAG System CLI Tester")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        # Create test PDF if none provided
        pdf_path = create_test_pdf()
        if not pdf_path:
            print("Usage: python test_cli.py [pdf_path]")
            return
    
    if not os.path.exists(pdf_path):
        print(f"❌ PDF file not found: {pdf_path}")
        return
    
    success = test_pipeline(pdf_path)
    print(f"\n{'✅ All tests passed!' if success else '❌ Some tests failed'}")

if __name__ == "__main__":
    main()
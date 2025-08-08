#!/usr/bin/env python3

import time
import os
from background_processor import get_processor, shutdown_processor

def progress_callback(doc_id, status, progress, message):
    print(f"📊 Doc {doc_id}: [{progress:3d}%] {status} - {message}")

def test_background_processing():
    print("🔄 Testing Background Processing System")
    print("=" * 50)
    
    processor = get_processor()
    
    # Check if test PDF exists
    test_pdf = "test_bill.pdf"
    if not os.path.exists(test_pdf):
        print("❌ test_bill.pdf not found. Run: python test_cli.py first")
        return
    
    # Queue document for processing
    print(f"📤 Queueing document: {test_pdf}")
    doc_id = processor.queue_document(test_pdf, progress_callback=progress_callback)
    print(f"✅ Document queued with ID: {doc_id}")
    
    # Monitor processing
    print(f"\n⏳ Monitoring processing...")
    start_time = time.time()
    
    while True:
        doc = processor.get_document_status(doc_id)
        if not doc:
            print("❌ Document not found")
            break
        
        if doc['status'] == 'completed':
            elapsed = time.time() - start_time
            print(f"\n✅ Processing completed in {elapsed:.1f} seconds!")
            
            # Test loading embeddings
            print(f"\n📊 Loading embeddings...")
            embeddings_df = processor.get_embeddings_df(doc_id)
            print(f"✅ Loaded {len(embeddings_df)} chunks with embeddings")
            
            # Show sample
            if not embeddings_df.empty:
                sample = embeddings_df.iloc[0]
                print(f"   Sample chunk: {sample['text'][:100]}...")
                print(f"   Embedding shape: {len(sample['embedding']) if 'embedding' in sample else 'None'}")
            
            break
            
        elif doc['status'] == 'failed':
            print(f"\n❌ Processing failed: {doc.get('error_message', 'Unknown error')}")
            break
        
        time.sleep(1)
        
        # Timeout after 5 minutes
        if time.time() - start_time > 300:
            print("\n⏰ Timeout - processing taking too long")
            break
    
    # Show stats
    print(f"\n📈 System Stats:")
    stats = processor.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # List all documents
    print(f"\n📋 All Documents:")
    docs = processor.list_documents()
    for doc in docs:
        print(f"   [{doc['id']}] {doc['filename']} - {doc['status']} ({doc.get('total_chunks', 0)} chunks)")
    
    # Cleanup
    shutdown_processor()
    print(f"\n🛑 Background processor stopped")

if __name__ == "__main__":
    test_background_processing()
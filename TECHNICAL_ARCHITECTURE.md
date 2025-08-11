# Technical Architecture - RAG PDF Intelligence System

## System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RAG PDF Intelligence System                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐  │
│  │   User   │────▶│ Streamlit│────▶│   RAG    │────▶│  OpenAI  │  │
│  │Interface │◀────│    App   │◀────│  Engine  │◀────│   APIs   │  │
│  └──────────┘     └──────────┘     └──────────┘     └──────────┘  │
│                          │                │                          │
│                          ▼                ▼                          │
│                   ┌──────────┐     ┌──────────┐                    │
│                   │Background│     │  SQLite  │                    │
│                   │Processor │────▶│ Database │                    │
│                   └──────────┘     └──────────┘                    │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Flow Architecture

### 1. Document Processing Pipeline

```
PDF Upload ──────▶ Text Extraction ──────▶ Chunking ──────▶ Embedding Generation
     │                    │                     │                    │
     │                    │                     │                    │
     ▼                    ▼                     ▼                    ▼
[User File]         [Raw Text]           [Text Chunks]        [Vector Embeddings]
                                          (1000 tokens)         (1536 dimensions)
                                                                      │
                                                                      ▼
                                                               [SQLite Storage]
```

### 2. Query Processing Flow

```
User Question ────▶ Query Embedding ────▶ Similarity Search ────▶ Chunk Retrieval
      │                    │                      │                      │
      │                    │                      │                      │
      ▼                    ▼                      ▼                      ▼
[Natural Lang]     [Vector Format]        [Cosine Similarity]    [Top-K Chunks]
                                                                         │
                                                                         ▼
                                                              Context Assembly
                                                                         │
                                   ┌─────────────────────────────────────┴───────────────┐
                                   │                                                     │
                                   ▼                                                     ▼
                            [RAG Answer Mode]                                   [Non-RAG Mode]
                            Document-based only                              Pure AI knowledge
                                   │                                                     │
                                   └──────────────────┬──────────────────────────────────┘
                                                      ▼
                                              [Hybrid RAG+LLM Mode]
                                            Document + AI knowledge
```

## Component Architecture

### Core Modules

```
config.py
    │
    ├──▶ Configuration Management
    │    • API Keys (OPENAI_API_KEY)
    │    • Model Settings (GPT-4, text-embedding-3-small)
    │    • Processing Parameters (chunk_size=1000, overlap=200)
    │    • Token Limits (max_context=8000, max_response=1500)
    │
pdf_loader.py
    │
    ├──▶ PDF Processing
    │    • PyPDF2 Integration
    │    • Text Extraction with Page Markers
    │    • Metadata Extraction
    │
embed_and_store.py
    │
    ├──▶ Text Processing & Embedding
    │    • Semantic-Aware Chunking
    │    • Token Counting (tiktoken)
    │    • OpenAI Embedding Generation
    │    • Similarity Search (scikit-learn)
    │
rag_chain.py
    │
    ├──▶ Question Answering Engine
    │    • Three Answer Modes:
    │        - generate_answer() → RAG Only
    │        - generate_non_rag_answer() → Pure LLM
    │        - generate_hybrid_answer() → RAG + LLM
    │    • Context Management
    │    • Token Limiting
    │    • Citation Generation
    │
database.py
    │
    ├──▶ Persistence Layer
    │    • SQLite Schema Management
    │    • Document Storage
    │    • Chunk & Embedding Storage
    │    • Query Operations
    │
background_processor.py
    │
    ├──▶ Asynchronous Processing
    │    • Multi-threaded Architecture
    │    • Job Queue Management
    │    • Progress Tracking
    │    • Error Recovery
    │
app_v2.py
    │
    └──▶ User Interface
         • Streamlit Web App
         • Document Library Management
         • A/B/C Testing Interface
         • Real-time Progress Display
```

## Database Schema

```sql
┌─────────────────────────────┐       ┌─────────────────────────────┐
│        documents            │       │          chunks             │
├─────────────────────────────┤       ├─────────────────────────────┤
│ id              INTEGER PK  │───┐   │ id              INTEGER PK  │
│ filename        TEXT        │   │   │ document_id     INTEGER FK  │◀─┘
│ file_hash       TEXT UNIQUE │   └──▶│ chunk_id        INTEGER     │
│ file_size       INTEGER     │       │ text            TEXT        │
│ num_pages       INTEGER     │       │ token_count     INTEGER     │
│ total_chunks    INTEGER     │       │ start_sentence  INTEGER     │
│ status          TEXT        │       │ end_sentence    INTEGER     │
│ created_at      TIMESTAMP   │       │ embedding       BLOB        │
│ processed_at    TIMESTAMP   │       │ created_at      TIMESTAMP   │
│ error_message   TEXT        │       └─────────────────────────────┘
└─────────────────────────────┘

Status Values: pending | processing | completed | failed
```

## Three-Mode Answer Generation

### Mode 1: RAG Only
```
Question → Embedding → Search → Retrieved Chunks → Context Assembly → GPT-4
                                                          │
                                                          ▼
                                              Answer (Document-based only)
                                              + Source Citations
```

### Mode 2: Non-RAG LLM
```
Question ─────────────────────────────────────────────────▶ GPT-4
                                                              │
                                                              ▼
                                                   Answer (AI Knowledge only)
                                                   No Document Context
```

### Mode 3: RAG + LLM Hybrid
```
Question → Embedding → Search → Retrieved Chunks ──┐
                                                    ▼
                                            Context + GPT-4
                                            General Knowledge
                                                    │
                                                    ▼
                                        Answer (Document + AI Knowledge)
                                        Citations + Extended Context
```

## Performance Characteristics

### Processing Metrics
```
┌──────────────────────────────────────────────────────┐
│ Document Processing (One-time per document)          │
├──────────────────────────────────────────────────────┤
│ 10-page PDF:    ~20 seconds                         │
│ 50-page PDF:    ~60 seconds                         │
│ 100-page PDF:   ~120 seconds                        │
│ 200-page PDF:   ~240 seconds                        │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│ Query Response Times                                 │
├──────────────────────────────────────────────────────┤
│ Embedding Generation:     0.2-0.3 seconds           │
│ Similarity Search:        0.01-0.02 seconds         │
│ Context Assembly:         0.05-0.1 seconds          │
│ GPT-4 Generation:         2-4 seconds               │
│ ─────────────────────────────────────────           │
│ Total Response Time:      2.5-5 seconds             │
└──────────────────────────────────────────────────────┘
```

### Storage Requirements
```
┌──────────────────────────────────────────────────────┐
│ Storage Per Document                                 │
├──────────────────────────────────────────────────────┤
│ Original PDF:        Preserved in /uploads           │
│ Text Chunks:         ~2-3 KB per chunk              │
│ Embeddings:          ~6 KB per chunk (1536 floats)  │
│ Metadata:            ~0.5 KB per document           │
│ ─────────────────────────────────────────           │
│ Total (100 pages):   ~2-3 MB in database            │
└──────────────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Security Layers                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. API Key Security                                         │
│     └─▶ Environment Variables (.env)                         │
│     └─▶ Never Hardcoded                                      │
│     └─▶ Streamlit Secrets Management                         │
│                                                               │
│  2. Data Security                                            │
│     └─▶ Local SQLite Storage                                 │
│     └─▶ No External Data Transmission                        │
│     └─▶ Process Isolation                                    │
│                                                               │
│  3. Access Control                                           │
│     └─▶ File System Permissions                              │
│     └─▶ Database ACID Compliance                             │
│     └─▶ Session Isolation in Streamlit                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Architecture

### Option 1: Streamlit Cloud
```
GitHub Repo ──▶ Streamlit Cloud ──▶ Auto Deploy ──▶ Public URL
                      │
                      ▼
               Secrets Management
                (OPENAI_API_KEY)
```

### Option 2: On-Premise
```
Local Server ──▶ Python Environment ──▶ Streamlit Server ──▶ Internal Network
                         │
                         ▼
                  SQLite Database
                  (Persistent Storage)
```

### Option 3: Cloud Platform (AWS/GCP/Azure)
```
Container Image ──▶ Cloud Run/App Service ──▶ Load Balancer ──▶ Users
                            │
                            ▼
                    Cloud SQL/Storage
                    (Scalable Backend)
```

## API Integration Points

### OpenAI API Calls

1. **Embedding Generation**
   - Endpoint: `embeddings.create()`
   - Model: `text-embedding-3-small`
   - Dimension: 1536
   - Rate Limit: 3000 RPM

2. **Chat Completion**
   - Endpoint: `chat.completions.create()`
   - Model: `gpt-4`
   - Context Window: 8K tokens
   - Rate Limit: 200 RPM

### Cost Structure
```
┌──────────────────────────────────────────────────────┐
│ API Cost Breakdown (per document)                    │
├──────────────────────────────────────────────────────┤
│ Embeddings:                                          │
│   100 chunks × $0.00002/1K tokens = $0.02          │
│                                                       │
│ Queries:                                              │
│   Input: ~6K tokens × $0.03/1K = $0.18              │
│   Output: ~1.5K tokens × $0.06/1K = $0.09           │
│   ─────────────────────────────────────             │
│   Total per Query: ~$0.27                           │
└──────────────────────────────────────────────────────┘
```

## Monitoring & Observability

### Key Metrics to Track
```
System Health:
├── Document Processing Queue Length
├── Average Processing Time
├── Failed Processing Rate
└── API Error Rate

Performance:
├── Query Response Time (P50, P95, P99)
├── Tokens Used per Query
├── Cache Hit Rate (if implemented)
└── Concurrent Users

Business:
├── Documents Processed/Day
├── Queries/Day
├── Unique Users
└── Most Queried Topics
```

## Scalability Considerations

### Current Limitations
- Single SQLite database (concurrent write limitation)
- Synchronous embedding generation
- Single-instance Streamlit deployment

### Scale-Up Path
1. **Phase 1**: Current (1-10 users)
   - SQLite + Single Instance
   
2. **Phase 2**: Growth (10-100 users)
   - PostgreSQL migration
   - Redis caching layer
   - Multiple Streamlit instances
   
3. **Phase 3**: Enterprise (100+ users)
   - Distributed processing (Celery)
   - Vector database (Pinecone/Weaviate)
   - Kubernetes deployment

## Technology Stack Summary

- **Language**: Python 3.11
- **Web Framework**: Streamlit 1.28+
- **AI/ML**: OpenAI GPT-4, OpenAI Embeddings
- **Database**: SQLite3
- **PDF Processing**: PyPDF2
- **Vector Operations**: NumPy, scikit-learn
- **Token Management**: tiktoken
- **Environment**: Conda (RAG_env)
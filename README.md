# RAG Methodology Evaluation Framework

An empirical research platform for data scientists to evaluate RAG implementation strategies through systematic A/B/C testing. Compare RAG-only vs. RAG+LLM hybrid approaches using real documents and quantitative metrics to make evidence-based architecture decisions.

## Key Research Question
**"Should we use pure RAG or hybrid RAG+LLM for our specific use case?"**

This framework provides the empirical foundation to answer this question with data rather than assumptions.

## Research Framework Features

- **Empirical Methodology Comparison**: Simultaneous evaluation of three approaches:
  - **RAG-Only**: Zero-hallucination document retrieval with citations
  - **Non-RAG LLM**: Baseline general knowledge control group
  - **RAG+LLM Hybrid**: Enhanced reasoning with managed hallucination risk
- **Quantitative Metrics**: Comprehensive performance measurement and comparison
- **Persistent Test Environment**: Process evaluation documents once, run multiple experiments
- **Statistical Analysis**: Response time, token usage, accuracy, and completeness metrics
- **Domain-Specific Testing**: Evaluate with your actual document types and query patterns
- **Risk Quantification**: Measure hallucination rates vs. completeness trade-offs
- **Comparative Visualization**: Side-by-side results with instant mode switching
- **Export Capabilities**: Data export for further statistical analysis
- **Reproducible Experiments**: Standardized evaluation conditions
- **Architecture Decision Support**: Evidence-based RAG strategy selection

## Quick Start for Data Scientists

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

### Launch Evaluation Framework
```bash
# Start the evaluation interface
streamlit run app_v2.py

# Validate framework setup
python test_cli.py          # Test core pipeline
python test_background.py   # Test background processing
```

## Research Methodology

### Evaluation Protocol
1. **Document Preparation**: Upload representative PDFs from your domain
2. **Processing**: System extracts text, chunks, and generates embeddings
3. **Query Design**: Create test questions covering:
   - Factual queries (expected RAG-only advantage)
   - Analytical queries (expected hybrid advantage)
   - Comparative queries (control group baselines)
4. **Simultaneous Evaluation**: Generate answers from all three approaches
5. **Metrics Collection**: Analyze performance across multiple dimensions
6. **Statistical Analysis**: Export data for significance testing

### Evaluation Interface
- **Controlled Comparison**: All methods use identical inputs and conditions
- **Real-time Metrics**: Response time, token usage, citation coverage
- **Side-by-side Analysis**: Compare outputs for quality assessment
- **Performance Dashboard**: Quantitative metrics for each approach
  - Hallucination detection and measurement
  - Information completeness scoring
  - Cost-effectiveness analysis
  - Factual accuracy assessment
- **Export Functionality**: CSV/JSON export for further analysis
- **Research Documentation**: Built-in experiment logging

### Research Validation Tools
```bash
# Validate framework setup
python test_cli.py

# Test background processing reliability
python test_background.py

# Generate standardized test documents
python create_test_pdf.py
```

## Research Applications

Optimal for evaluating RAG approaches across:
- **Compliance Documents**: Legal texts, regulations, policy documents
- **Technical Documentation**: Manuals, specifications, procedures
- **Research Literature**: Academic papers, reports, analyses
- **Government Documents**: Bills, acts, legislative materials

## Technical Architecture

### Methodology Implementation
- `rag_chain.py`: Three evaluation modes with isolated implementations
  - `generate_answer()`: Pure RAG with document-only responses
  - `generate_non_rag_answer()`: Control group without document context
  - `generate_hybrid_answer()`: RAG+LLM with enhanced reasoning
- `embed_and_store.py`: Standardized chunking and retrieval for fair comparison
- `config.py`: Centralized parameters ensuring consistent evaluation conditions

### Evaluation Infrastructure
- `database.py`: Persistent storage for reproducible experiments
- `background_processor.py`: Reliable document preprocessing pipeline
- `app_v2.py`: Interactive evaluation interface with metrics dashboard

### Research Validation
- `test_cli.py`: Framework validation and performance benchmarking
- `test_background.py`: System reliability testing
- `create_test_pdf.py`: Standardized test document generation

## Technical Requirements

- Python 3.11+ (for optimal performance)
- OpenAI API key (for LLM and embedding services)
- 4GB+ RAM (for document processing)
- Conda environment: `RAG_env`

## Research Deployment

### Local Research Environment (Recommended)
```bash
conda activate RAG_env
streamlit run app_v2.py
```

### Cloud Research Platform
1. Deploy to Streamlit Cloud for team access
2. Configure with `OPENAI_API_KEY` in secrets
3. Share evaluation interface with research team
4. Export results for collaborative analysis

### Institutional Deployment
- **On-premise**: For sensitive research data
- **Private cloud**: For distributed research teams
- **Container deployment**: For scalable evaluation workflows

## Repository Structure
```
RAG-Methodology-Framework/
├── app_v2.py              # Interactive evaluation interface
├── rag_chain.py           # Core methodology implementations
│   ├── generate_answer()       # RAG-only evaluation
│   ├── generate_non_rag_answer() # Control group baseline
│   └── generate_hybrid_answer()  # RAG+LLM hybrid
├── embed_and_store.py     # Standardized document processing
├── database.py            # Persistent evaluation data storage
├── background_processor.py # Reliable document preprocessing
├── config.py              # Evaluation parameters and settings
├── test_cli.py            # Framework validation and benchmarks
├── test_background.py     # System reliability tests
├── create_test_pdf.py     # Standardized test document generator
├── requirements.txt       # Python dependencies
├── METHODOLOGY_COMPARISON.md # Detailed approach analysis
├── EXECUTIVE_SUMMARY.md   # Research framework overview
└── uploads/               # Evaluation documents (auto-created)
```

## Research Benefits

- **Empirical Evidence**: Quantitative comparison replaces theoretical assumptions
- **Risk Quantification**: Measure actual hallucination rates vs. completeness gains
- **Domain Validation**: Test with your specific document types and query patterns
- **Architecture Optimization**: Evidence-based selection of RAG strategies
- **Reproducible Results**: Standardized evaluation conditions ensure reliability
- **Statistical Rigor**: Export data for significance testing and confidence intervals
- **Implementation Guidance**: Clear decision criteria for production deployment
- **Cost-Benefit Analysis**: Detailed token usage and performance trade-off measurement
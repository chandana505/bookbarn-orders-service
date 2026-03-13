# AI Infrastructure Capacity Planning Advisor

## 🏗️ Overview
**AI Capacity Planning Advisor** is a **Streamlit-based web application** that analyzes **any CSV file containing infrastructure metrics** (CPU%, memory, disk, network, requests, etc.) and provides **AI-powered capacity planning recommendations**. 

Key features:
- **Dynamic metric detection** - works with **any numeric CSV columns**
- **Anomaly imputation** & data cleaning
- **Multi-day forecasting** using LLM (DeepSeek-V3)
- **RAG-enhanced decisions** (scaling policies, historical incidents)
- **Interactive Q&A** on uploaded data
- **Executive reports** & visualizations
- **Zero configuration** - upload CSV → instant analysis

**Demo flow**: Upload `sample_metrics.csv` → See trends → Generate 30-day forecast → Get "Scale out CPU by 20%" recommendations.

## 🛠️ Technologies & Major Packages

| Category | Technology/Package | Purpose | Why Chosen |
|----------|-------------------|---------|------------|
| **Web Framework** | [Streamlit](https://streamlit.io/) 1.28+ | Interactive UI/dashboard | **Rapid prototyping** - turns Python into web app in minutes. Perfect for AI demos. Handles file upload, charts, metrics effortlessly. |
| **Data Processing** | [Pandas](https://pandas.pydata.org/) 2.1+, [NumPy](https://numpy.org/) 1.26 | CSV parsing, stats, trends | **Industry standard** for dynamic data analysis. Handles time series, growth rates, imputation automatically. |
| **Visualization** | [Plotly](https://plotly.com/python/) 5.15+ | Interactive trend charts | **Production-ready interactive plots** - zoomable time series for multiple metrics. Better than matplotlib for web. |
| **HTTP/Async** | [HTTPC](https://www.python-httpx.org/) 0.27 | API calls to TCS GenAI | **Modern async HTTP** - handles SSL bypass for internal endpoints, timeouts, retries. |
| **Environment** | [python-dotenv](https://github.com/theskumar/python-dotenv) | `.env` API keys | **Secure secrets** - loads `GENAI_API_KEY` safely. |

## 🤖 AI/LLM Stack (TCS GenAI Platform)

| Model | Endpoint | Usage | Why Chosen |
|-------|----------|--------|------------|
| **azure/genailab-maas-gpt-4o-mini** | Q&A, Decisions, Reports, Summaries | **Primary reasoning model** (~50% usage) | **Cost-effective GPT-4o** - precise structured JSON responses (capacity actions, reports). Temperature 0.2 for reliability. |
| **azure_ai/genailab-maas-DeepSeek-V3-0324** | **Forecasting** (7-30 day predictions) | **Time series forecasting** (~30% usage) | **Specialized forecasting** - better at numeric trend extrapolation than GPT-4. Handles exponential growth detection. |
| **azure/genailab-maas-text-embedding-3-large** | **RAG embeddings** | Vector search on policy docs | **Latest embeddings** - semantic search on scaling policies/incidents for context-aware decisions. |

**API Base**: `https://genailab.tcs.in/v1` (TCS internal GenAI platform)
**Key**: `GENAI_API_KEY` in `.env`

## 🔍 RAG Pipeline (Retrieval-Augmented Generation)

| Component | Tech | Purpose |
|-----------|------|---------|
| **Vector Store** | [FAISS](https://github.com/facebookresearch/faiss) (CPU) | **Fast similarity search** on policy documents. Stores `sample_docs.json` (AWS scaling policies, incidents). |
| **Embeddings** | LangChain + OpenAIEmbeddings | Converts docs → vectors. Queries like "CPU scaling policy" → relevant context. |
| **Docs** | JSON policy library | 5x sample docs: AWS scaling rules, incident post-mortems, best practices. |

**RAG Flow**:
```
Query: "CPU forecast high" → Embed → FAISS search → "Scale out at 80% for 5min" → LLM decision
```

## 📁 Architecture & Core Modules

```
capacity-advisor/
├── app.py                 # Streamlit UI + orchestration
├── data_processor.py      # CSV → clean metrics + imputation
├── forecast_engine.py     # DeepSeek LLM forecasts ALL metrics
├── decision_engine.py     # GPT-4o-mini → capacity actions (RAG)
├── rag_layer.py          # FAISS vector store
├── report_generator.py    # Executive PDF-ready reports
├── prompts.py            # 3x prompt templates (forecast/decision/report)
├── metrics_formatter.py   # LLM-friendly metrics strings
└── sample_metrics.csv    # Demo data (8 days CPU/memory growth)
```

## 🚀 How It Works (End-to-End)

1. **Upload CSV** (`app.py`)
2. **Data Processing** (`data_processor.py`)
   - Detect ALL numeric columns dynamically
   - Impute anomalies (3σ outliers → neighbor avg)
   - Compute growth rates, recent history
3. **Forecasting** (`forecast_engine.py`)
   - LLM prompt with ALL metrics history
   - DeepSeek-V3 → 7/30-day point forecasts per metric
   - Fallback: trend extrapolation if API fails
4. **RAG Context** (`rag_layer.py`)
   - "CPU>80% forecast" → AWS scaling policy retrieved
5. **Decisions** (`decision_engine.py`)
   - GPT-4o-mini analyzes forecasts + RAG → "Scale out 20%"
6. **Reports** (`report_generator.py`)
   - Executive summary with risk/urgency

## 📊 Sample Output

**Input**: `sample_metrics.csv` (CPU 45→82% over 8 days)
```
Forecast (30 days): CPU: 125%, Memory: 105%, Requests: 850
Risk: HIGH
Action: "Scale out 2→3 instances, CPU buffer 25%"
RAG: "CPU>80% → scale out 20% per AWS policy"
```

## 🔑 Why This Stack?

| Choice | Alternatives | Winner Reason |
|--------|--------------|---------------|
| **Streamlit** | Flask, Gradio | **5x faster prototyping**, file upload + charts OOTB |
| **DeepSeek-V3** | GPT-4o only | **Better numeric forecasting**, cheaper |
| **FAISS** | Pinecone/Chroma | **Local/offline**, zero cost, fast for 100s docs |
| **Pandas** | Polars | **Universal**, handles messy CSVs perfectly |
| **TCS GenAI** | OpenAI direct | **Internal compliance**, same models |

## 🧪 Quick Start

```bash
cd capacity-advisor
pip install -r requirements.txt
echo "GENAI_API_KEY=your_key" > .env
streamlit run app.py
```

**Try**: Upload `sample_metrics.csv` → "Generate Capacity Advice"

## 📈 Production Scale
- **Handles 1000+ metrics/rows**
- **Any CSV format** (timestamp optional)
- **RAG extensible** - add company policies to `sample_docs.json`
- **Forecast fallback** - works offline

---

**Built for:** Infrastructure teams needing **proactive capacity planning** without SRE expertise.
**Team:** 5x modular roles (Data/ML/UI/DevOps/Lead)

*Demo-ready POC | Upload → AI Insights → Scale Confidently*


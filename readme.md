# QA-RAG – Bug Intelligence Assistant

QA-RAG is an AI-powered assistant for Quality Assurance teams.  
It combines Retrieval-Augmented Generation (RAG) with structured analytics to answer questions about bug data in a natural and explainable way.

The goal is to help QA leads and engineers:
- understand product risk  
- analyze bug trends  
- explore known issues using natural language  

---

### What QA-RAG Does

QA-RAG supports two main capabilities:

### 1. Analytics (Structured Metrics)

It can compute QA metrics directly from bug data, such as:
- Open bugs by component  
- Open bugs by severity  
- Average / median / P75 resolution time  
- Lists of open critical bugs  
- Closed bugs for a specific component  

Results are returned as:
- a short natural-language summary  
- a table  
- and (when applicable) a chart  

---

### 2. RAG / Explanation (Semantic Analysis)

It can answer free-text questions using semantic search over bug descriptions, such as:
- Is there a known Apple Pay issue?  
- Why does checkout fail sometimes?  
- Are there recurring issues in Payments?  

Each answer:
- is grounded in real bug data  
- includes retrieved evidence  

---

### Supported Question Types

QA-RAG intentionally supports the following categories:

### Aggregations
Counts and grouped metrics:
- How many open bugs by component?  
- Open bugs by severity  
- Count of critical bugs  

### Statistics
Resolution time analysis:
- Average resolution time by component  
- Median resolution time  
- P75 resolution time  

### Lists
Raw bug rows:
- What are the open critical bugs?  
- Show closed bugs for component Payments  

### Lookup
Direct bug ID queries:
- Show details for BUG-1005  
- Resolution time for BUG-1005  

### RAG / Explanation
Semantic questions:
- Is there a known Apple Pay issue?  
- Why does checkout fail sometimes?  

---

### Out of Scope

QA-RAG is not a general BI tool or SQL engine.

The following are intentionally out of scope:
- Ranking queries (e.g. "latest created bug")  
- Forecasting or prediction  
- External system integration (Jira, GitHub, production metrics)  
- Causal reasoning beyond bug text  

Examples of unsupported queries:
- What is the last created bug?  
- Predict next week’s bug volume  
- Why did engineering introduce this bug?  

---

### Design Philosophy

QA-RAG is built around:

### Reliability
All analytics are computed directly from structured bug data.

### Explainability
All RAG answers show retrieved evidence.

### Product Focus
High-signal QA assistant, not a generic data explorer.

---

### Architecture Overview
CSV / Bug Data
↓
Embeddings + Chroma (Vector Store)
↓
Router (RAG vs Analytics)
↓
RAG Answer OR Analytics Computation
↓
Streamlit UI (Chat + Tables + Charts)

### Tech Stack

- Python  
- Streamlit  
- ChromaDB  
- SentenceTransformers  
- Groq / OpenAI-compatible LLM API  
- Pandas  

---

### Typical Demo Questions

- How many open bugs by component?  
- What are open critical bugs?  
- Average resolution time by component?  
- Is there a known Apple Pay issue?  
- Show details for BUG-1005  

---

### Project Status

This project is an MVP demo focused on:
- AI-driven QA analytics  
- practical RAG usage  
- portfolio-quality product demo 

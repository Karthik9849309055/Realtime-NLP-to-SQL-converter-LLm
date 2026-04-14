#  Real-time NLP → SQL Query Engine

> Convert natural-language questions into SQL and execute them against a live MySQL database — powered by **Llama 3.1**, **LangChain**, **ChromaDB**, and **Streamlit**.

#LIVE LINK
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)]([https://your-app-name.streamlit.app](https://realtime-nlp-to-sql-converter-llm-o56aszj4cuwcffusd6wfvs.streamlit.app/))

---

##  Features

| Feature | Detail |
|---------|--------|
| **Natural Language → SQL** | Type a question in English and get an accurate SQL query |
| **Live Execution** | Runs the generated SQL on a cloud MySQL database in real-time |
| **Few-Shot Retrieval** | ChromaDB + sentence-transformers find the most relevant examples to guide the LLM |
| **Caching** | In-memory caching for both SQL generation and query results |
| **Input Validation** | Rate limiting + SQL injection guard (SELECT-only queries) |

##  Architecture

```
User Question
     │
     ▼
┌─────────────┐     ┌──────────────┐
│  ChromaDB   │────▶│  LLM (Groq)  │
│  Few-Shots  │     │  Llama 3.1   │
└─────────────┘     └──────┬───────┘
                           │ SQL
                           ▼
                    ┌──────────────┐
                    │   MySQL DB   │
                    │  (Aiven)     │
                    └──────┬───────┘
                           │ Results
                           ▼
                    ┌──────────────┐
                    │  Streamlit   │
                    │  Dashboard   │
                    └──────────────┘
```

## Tech Stack

- **LLM**: Groq Cloud — Llama 3.1 8B Instant
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Vector Store**: ChromaDB (in-memory)
- **Database**: MySQL 8 (Aiven free tier)
- **Framework**: LangChain + Streamlit
- **Deployment**: Streamlit Community Cloud

##  Quick Start (Local)

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/Realtime-NLP-to-SQL-converter-LLm.git
cd Realtime-NLP-to-SQL-converter-LLm/app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file with your credentials
cp .env.exapmle .env
# Edit .env with your MYSQL_* and GROQ_API_KEY values

# 4. Run
streamlit run app.py
```



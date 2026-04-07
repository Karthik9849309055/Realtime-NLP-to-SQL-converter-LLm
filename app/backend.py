import mysql.connector
from decimal import Decimal
import hashlib
import re
import time

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings

import chromadb
from chromadb.utils import embedding_functions

from fewshots import few_shot

import os
import streamlit as st


# ──────────────────────────────────────────────
# CONFIG — works on Streamlit Cloud AND locally
# ──────────────────────────────────────────────

def _secret(key: str, default: str = "") -> str:
    """Read from Streamlit secrets first, then env vars."""
    try:
        return st.secrets[key]
    except Exception:
        return os.getenv(key, default)


# ──────────────────────────────────────────────
# DB CONNECTION
# ──────────────────────────────────────────────

def get_connection():
    return mysql.connector.connect(
        host=_secret("MYSQL_HOST"),
        port=int(_secret("MYSQL_PORT", "3306")),
        user=_secret("MYSQL_USER"),
        password=_secret("MYSQL_PASSWORD"),
        database=_secret("MYSQL_DB"),
        connection_timeout=10,
    )


# ──────────────────────────────────────────────
# LLM (lazy init — avoids crash if key is missing at import time)
# ──────────────────────────────────────────────

_llm = None


def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGroq(
            model="llama-3.1-8b-instant",
            temperature=0,
            api_key=_secret("GROQ_API_KEY"),
        )
    return _llm


# ──────────────────────────────────────────────
# EMBEDDINGS + CHROMA DB (FEW-SHOT RETRIEVAL)
# ──────────────────────────────────────────────

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

chroma_client = chromadb.Client()

collection = chroma_client.get_or_create_collection(
    name="few_shots",
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL
    )
)

# Load few-shots ONCE
if collection.count() == 0:
    for idx, ex in enumerate(few_shot):
        collection.add(
            documents=[ex["Question"]],
            metadatas=[{"sql": ex["SQLQuery"]}],
            ids=[str(idx)]
        )


# ──────────────────────────────────────────────
# CACHES + RATE LIMITER
# ──────────────────────────────────────────────

SQL_CACHE: dict[str, str] = {}
RESULT_CACHE: dict[str, list] = {}

# Simple in-memory rate limiter: max 20 requests per minute
_rate_log: list[float] = []
RATE_LIMIT = 20
RATE_WINDOW = 60  # seconds


def _check_rate_limit():
    now = time.time()
    # Remove entries older than window
    while _rate_log and _rate_log[0] < now - RATE_WINDOW:
        _rate_log.pop(0)
    if len(_rate_log) >= RATE_LIMIT:
        raise RuntimeError("Rate limit exceeded. Please wait a moment before trying again.")
    _rate_log.append(now)


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


# ──────────────────────────────────────────────
# INPUT VALIDATION
# ──────────────────────────────────────────────

_DANGEROUS_KEYWORDS = re.compile(
    r"\b(DROP|DELETE|TRUNCATE|ALTER|INSERT|UPDATE|CREATE|GRANT|REVOKE|EXEC)\b",
    re.IGNORECASE,
)


def _validate_sql(sql: str):
    """Only allow SELECT statements — reject anything dangerous."""
    stripped = sql.strip().rstrip(";").strip()
    if not stripped.upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed.")
    if _DANGEROUS_KEYWORDS.search(stripped):
        raise ValueError("Query contains forbidden keywords.")


def _sanitize_question(question: str) -> str:
    """Basic input length / character guard."""
    question = question.strip()
    if len(question) > 500:
        raise ValueError("Question too long (max 500 chars).")
    if len(question) < 3:
        raise ValueError("Question too short.")
    return question


def _clean_llm_output(raw: str) -> str:
    """Strip markdown fences and whitespace that LLMs sometimes add."""
    text = raw.strip()
    # Remove ```sql ... ``` wrappers
    if text.startswith("```"):
        lines = text.split("\n")
        # Drop first line (```sql) and last line (```)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


# ──────────────────────────────────────────────
# SQL GENERATION
# ──────────────────────────────────────────────

def generate_sql(question: str) -> str:
    question = _sanitize_question(question)
    _check_rate_limit()

    q_hash = _hash(question)

    # SQL cache hit
    if q_hash in SQL_CACHE:
        return SQL_CACHE[q_hash]

    # Retrieve top-2 similar few-shots
    results = collection.query(
        query_texts=[question],
        n_results=2
    )

    examples = ""
    for meta in results["metadatas"][0]:
        examples += f"\nSQLQuery: {meta['sql']}\n"

    prompt = f"""
You are a MySQL expert.

Tables:
t_shirts(t_shirt_id, brand, color, size, price, stock_quantity)
discounts(discount_id, t_shirt_id, pct_discount)

Rules:
- Inventory questions → use SUM(stock_quantity)
- Revenue → SUM(price * stock_quantity)
- Discount revenue → LEFT JOIN discounts
- Use correct ENUM casing
- Output ONLY the raw SQL query
- No markdown, no code fences, no explanation

Examples:
{examples}

Question: {question}
SQLQuery:
"""

    raw = _get_llm().invoke(prompt).content.strip()
    sql = _clean_llm_output(raw)
    sql = sql.rstrip(";") + ";"

    # Validate generated SQL before caching
    _validate_sql(sql)

    SQL_CACHE[q_hash] = sql
    return sql


# ──────────────────────────────────────────────
# RUN SQL (CACHED, safe connection handling)
# ──────────────────────────────────────────────

def run_sql(sql: str):
    _validate_sql(sql)

    if sql in RESULT_CACHE:
        return RESULT_CACHE[sql]

    conn = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql)
        rows = cur.fetchall()
        cur.close()
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass

    RESULT_CACHE[sql] = rows
    return rows


# ──────────────────────────────────────────────
# NORMALIZE RESULT
# ──────────────────────────────────────────────

def normalize_result(rows):
    if not rows or rows[0][0] is None:
        return 0

    value = rows[0][0]

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (int, float)):
        return value

    return str(value)

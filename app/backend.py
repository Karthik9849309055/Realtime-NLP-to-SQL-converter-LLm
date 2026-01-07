import mysql.connector
from decimal import Decimal
import hashlib

from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings

import chromadb
from chromadb.utils import embedding_functions

from fewshots import few_shot

import os



# DB CONNECTION



def get_connection():
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB"),
    )




# LLM

llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0
)



# EMBEDDINGS + CHROMA DB (FEW-SHOT RETRIEVAL)

embedding_model = "sentence-transformers/all-MiniLM-L6-v2"

embedding = HuggingFaceEmbeddings(
    model_name=embedding_model
)

chroma_client = chromadb.Client()

collection = chroma_client.get_or_create_collection(
    name="few_shots",
    embedding_function=embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=embedding_model
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



# CACHES

SQL_CACHE = {}
RESULT_CACHE = {}


def _hash(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()



# SQL GENERATION (FAST)

def generate_sql(question: str) -> str:
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
- Output ONLY SQL
- No markdown
- No explanation

Examples:
{examples}

Question: {question}
SQLQuery:
"""

    sql = llm.invoke(prompt).content.strip()
    sql = sql.rstrip(";") + ";"

    SQL_CACHE[q_hash] = sql
    return sql



# RUN SQL (CACHED)

def run_sql(sql: str):
    if sql in RESULT_CACHE:
        return RESULT_CACHE[sql]

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql)
    rows = cur.fetchall()
    cur.close()
    conn.close()

    RESULT_CACHE[sql] = rows
    return rows



# NORMALIZE RESULT

def normalize_result(rows):
    if not rows or rows[0][0] is None:
        return 0

    value = rows[0][0]

    if isinstance(value, Decimal):
        return float(value)

    if isinstance(value, (int, float)):
        return value

    return str(value)

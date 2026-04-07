import streamlit as st
import pandas as pd
from backend import generate_sql, run_sql, normalize_result

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────

st.set_page_config(
    page_title="Text → SQL  |  NLP Query Engine",
    page_icon="🧠",
    layout="wide",
)

# ──────────────────────────────────────────────
# CUSTOM CSS
# ──────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }

    h1 {
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0 !important;
    }
    .gradient-text {
        background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    /* Run button */
    div.stButton > button[kind="primary"] {
        border-radius: 12px;
        padding: 0.55rem 1.75rem;
        font-weight: 600;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: white;
        border: none;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(99,102,241,0.40);
    }

    /* Example cards */
    div.stButton > button[kind="secondary"] {
        border-radius: 10px;
        border: 1px solid rgba(99,102,241,0.35) !important;
        background: rgba(99,102,241,0.06) !important;
        color: #818cf8 !important;
        font-size: 0.82rem !important;
        padding: 0.45rem 0.8rem !important;
        text-align: left !important;
        white-space: normal !important;
        height: auto !important;
        line-height: 1.35 !important;
        transition: background 0.15s ease !important;
    }
    div.stButton > button[kind="secondary"]:hover {
        background: rgba(99,102,241,0.14) !important;
        border-color: #6366f1 !important;
    }

    footer { visibility: hidden; }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# SESSION STATE INIT
# ──────────────────────────────────────────────

if "prefill" not in st.session_state:
    st.session_state.prefill = ""


# ──────────────────────────────────────────────
# SIDEBAR — Database Schema Info
# ──────────────────────────────────────────────

with st.sidebar:
    st.markdown("## Database Schema")
    st.caption("Live MySQL database — `llm_db`")
    st.divider()

    # --- t_shirts table ---
    st.markdown("###  `t_shirts`")
    st.markdown("""
| Column | Type | Notes |
|--------|------|-------|
| `t_shirt_id` | INT | Primary Key |
| `brand` | ENUM | Van Huesen, Levi, Nike, Adidas |
| `color` | ENUM | Red, Blue, Black, White |
| `size` | ENUM | XS, S, M, L, XL |
| `price` | INT | $10 – $50 |
| `stock_quantity` | INT | Units in stock |
""")

    st.divider()

    # --- discounts table ---
    st.markdown("###  `discounts`")
    st.markdown("""
| Column | Type | Notes |
|--------|------|-------|
| `discount_id` | INT |  Primary Key |
| `t_shirt_id` | INT |  FK → t_shirts |
| `pct_discount` | DECIMAL | 0 – 100 % |
""")

    st.divider()
    st.markdown("#### 🔗 Relationship")
    st.markdown("`discounts.t_shirt_id` → `t_shirts.t_shirt_id`")
    st.caption("Not every t-shirt has a discount. Use LEFT JOIN for discount queries.")


# ──────────────────────────────────────────────
# MAIN AREA
# ──────────────────────────────────────────────

st.markdown("<h1>🧠 <span class='gradient-text'>Text → SQL Query Engine</span></h1>", unsafe_allow_html=True)
st.markdown(
    "Ask a question in **plain English** — the AI converts it to MySQL and runs it "
    "against a live cloud database in real time."
)
st.divider()


# ──────────────────────────────────────────────
# EXAMPLE QUERIES (clickable cards)
# ──────────────────────────────────────────────

EXAMPLES = {
    "Inventory": [
        "How many Nike t-shirts are in stock?",
        "How many white XS t-shirts does Nike have?",
        "How many white Levi's t-shirts do we have?",
        "How many t-shirts are available for each brand?",
        "Which color has the highest total stock across all brands?",
    ],
    "Revenue": [
        "Total revenue if we sell all t-shirts today?",
        "Revenue from all Levi's t-shirts without any discount?",
        "Revenue from Levi's t-shirts after applying discounts?",
        "Revenue from Nike L-size t-shirts with discounts?",
        "Which brand has the highest total inventory value?",
    ],
    "Discounts & Joins": [
        "Which t-shirts have discounts applied?",
        "Which t-shirts have no discount?",
        "List all brands and their discounted revenue?",
    ],
    "Analytics": [
        "What is the average price of Nike t-shirts by size?",
        "What is the total price of all S-size t-shirts?",
        "Which size has the most stock across all brands?",
    ],
}

st.subheader("Try an Example Query")
st.caption("Click any card below — it fills the question box automatically.")

# Callback to set prefill
def _set_prefill(text: str):
    st.session_state.prefill = text

tabs = st.tabs(list(EXAMPLES.keys()))
for tab, (category, questions) in zip(tabs, EXAMPLES.items()):
    with tab:
        cols = st.columns(2)
        for i, q in enumerate(questions):
            cols[i % 2].button(
                q,
                key=f"ex_{category}_{i}",
                type="secondary",
                on_click=_set_prefill,
                args=(q,),
            )

st.divider()

# ──────────────────────────────────────────────
# QUERY INPUT
# ──────────────────────────────────────────────

st.subheader("Your Question")

question = st.text_input(
    "question",
    value=st.session_state.prefill,
    placeholder="e.g.  How many white Nike t-shirts in XS do we have?",
    label_visibility="collapsed",
)

run_btn = st.button("Run Query", type="primary")

# ──────────────────────────────────────────────
# EXECUTION
# ──────────────────────────────────────────────

if run_btn:
    if not question.strip():
        st.warning("Please enter a question first.")
        st.stop()

    # Clear prefill after running so it doesn't stick
    st.session_state.prefill = ""

    col_sql, col_result = st.columns([1, 1], gap="large")

    with col_sql:
        with st.spinner("Generating SQL …"):
            try:
                sql = generate_sql(question)
            except (ValueError, RuntimeError) as e:
                st.error(str(e))
                st.stop()

        st.markdown("**Generated SQL**")
        st.code(sql, language="sql")

    with col_result:
        with st.spinner("Running against database …"):
            try:
                raw = run_sql(sql)

                st.markdown("**Result**")

                # Multi-row or multi-column → table view
                if raw and (len(raw) > 1 or len(raw[0]) > 1):
                    df = pd.DataFrame(raw)
                    st.dataframe(df, use_container_width=True)
                else:
                    answer = normalize_result(raw)
                    st.success(f"**{answer}**")

            except Exception as e:
                st.error(f"Query error: {e}")

# ──────────────────────────────────────────────
# FOOTER
# ──────────────────────────────────────────────

st.divider()
c1, c2, c3, c4 = st.columns(4)
c1.markdown("**LLM** · Llama 3.1 8B")
c2.markdown("**Vector DB** · ChromaDB")
c3.markdown("**Database** · MySQL")
c4.markdown("**Framework** · LangChain")

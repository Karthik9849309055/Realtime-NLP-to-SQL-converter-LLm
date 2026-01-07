import streamlit as st
from backend import generate_sql, run_sql, normalize_result

st.set_page_config(page_title="Text → SQL", layout="centered")
st.title("🧠 Text → SQL")

question = st.text_input("Ask something about the t_shirts database")

if st.button("Run"):
    if not question.strip():
        st.warning("Enter a question")
        st.stop()

    sql = generate_sql(question)

    st.subheader("Generated SQL")
    st.code(sql, language="sql")

    try:
        raw = run_sql(sql)
        answer = normalize_result(raw)

        st.subheader("Result")
        st.success(answer)

    except Exception as e:
        st.error(str(e))

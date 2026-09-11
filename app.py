import pandas as pd
import streamlit as st
from db import init_db, query, data_quality_summary
from llm import plan, explain
from guardrails import validate_sql

st.set_page_config(page_title="FreshFlow Analytics", layout="wide")
init_db()

st.title("FreshFlow Analytics")
st.caption("Meridian Markets · 10-store pilot · Apr 1–Jun 30, 2026")

with st.sidebar:
    st.subheader("Trust defaults")
    st.write("• Shrink = shipped units − sold units")
    st.write("• Default shrink scope = 5 fresh departments")
    st.write("• LB and EA are never silently combined")
    st.write("• Numeric answers come from SQLite")
    with st.expander("Data checks"):
        st.json(data_quality_summary())

examples = [
    "What was our total shrink cost in June?",
    "What were the top 10 fresh items by shrink cost in June?",
    "Which stores had the worst unit shrink in June?",
    "How did strawberry sales trend over the three months?",
    "Is shrink up or down versus May?",
]

question = st.text_input("Ask Meridian's data", placeholder=examples[0])
st.caption("Try: " + " · ".join(examples[:3]))

if question:
    try:
        with st.spinner("Planning a grounded query..."):
            p = plan(question)
        if p.get("status") != "query":
            st.warning(p.get("message") or "I need more information to answer safely.")
            if p.get("assumptions"):
                st.write("Assumptions considered:", p["assumptions"])
        else:
            sql = p.get("sql", "")
            validate_sql(sql)
            cols, rows = query(sql)
            answer = explain(question, p, cols, rows)
            st.subheader("Answer")
            st.write(answer)
            if rows:
                df = pd.DataFrame(rows, columns=cols)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No matching rows found.")

            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Metric definition**")
                st.write(p.get("metric_definition", ""))
            with c2:
                st.markdown("**Assumptions**")
                for a in p.get("assumptions", []):
                    st.write("•", a)
            st.caption("Sources: " + ", ".join(p.get("sources", [])))
            with st.expander("Show SQL"):
                st.code(sql, language="sql")
    except Exception as e:
        st.error(str(e))

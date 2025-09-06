import streamlit as st, time
from ui.services import expdb
def run(state):
    st.header("🕒 History", anchor=False)
    runs=expdb.list_runs(limit=200)
    if not runs: st.info("Kayıt yok."); return
    for r in runs:
        st.write(f"**{time.ctime(r['ts'])}** — `{r['id']}` — {r['strategy']} — symbols={','.join(r['symbols'])}")

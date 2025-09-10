import streamlit as st, json, time
from ui.services.paths import reports_dir, save_json
def run(state):
    st.header("📑 Report", anchor=False)
    if "last_metrics" not in state: st.info("Önce Run."); return
    meta={"generated_at": time.time(), "metrics": state["last_metrics"].to_dict()}
    name=f"report_{int(time.time())}.json"; path=reports_dir()/name; save_json(path, meta)
    st.success(f"Saved report: {path.name}"); st.code(json.dumps(meta, indent=2), language="json")

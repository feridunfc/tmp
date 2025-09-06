from __future__ import annotations

# ---------------- PATH BOOTSTRAP (ilk satırlar) ----------------
import sys, os, importlib, types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]   # proje kökü
SRC  = ROOT / "src"
for p in (str(ROOT), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ.setdefault("PYTHONPATH", str(SRC))
# ---------------------------------------------------------------

import streamlit as st

# opsiyonel: sidebar helper yoksa no-op
try:
    from ui.components.common import sidebar_controls  # type: ignore
except Exception:
    def sidebar_controls(state: dict):  # no-op
        pass

# Registry’yi hazırla (strateji dropdown’larının boş kalmaması için)
try:
    from src.strategies.registry import bootstrap, get_registry
    bootstrap("both")
except Exception:
    get_registry = None

# ---------------- yardımcılar ----------------
def _make_stub(title: str, err: str | None = None):
    mod = types.SimpleNamespace()
    def run(state: dict):
        st.title(title)
        if err:
            st.warning(f"'{title}' sekmesi yüklenemedi: {err}")
        else:
            st.info(f"{title} sekmesi için yer tutucu.")
    mod.run = run
    return mod

def _safe_import(module_path: str, title: str):
    """
    Modülü import etmeye çalışır; yoksa uyarı veren stub döner.
    run(state) fonksiyonu yoksa da stub üretir.
    """
    try:
        mod = importlib.import_module(module_path)
        if not hasattr(mod, "run") or not callable(getattr(mod, "run", None)):
            return _make_stub(title, "run(state) fonksiyonu tanımlı değil.")
        return mod
    except Exception as e:
        return _make_stub(title, str(e))

# Streamlit yeni API: width='stretch' uyarılarını önlemek için kullanacağız
DF_WIDTH = "stretch"

# ---------------- UI ----------------
st.set_page_config(page_title="ALGO3 UI", layout="wide")
st.title("ALGO3 UI — Backtest, Train, Walk-Forward & Live")

# state
if "state" not in st.session_state:
    st.session_state["state"] = {}
state = st.session_state["state"]
sidebar_controls(state)

# Sekmeleri sabit sırada tanımla; her biri güvenli import edilir.
TAB_SPECS = [
    ("Data",          "ui.tabs.data_tab"),
    ("Run",           "ui.tabs.run_tab"),
    ("Train",         "ui.tabs.train_tab"),
    ("Walk-Forward",  "ui.tabs.walk_tab"),
    ("Compare",       "ui.tabs.compare_tab"),
    ("Robustness",    "ui.tabs.robustness_tab"),
    ("NLP & Anomaly", "ui.tabs.nlp_anomaly_tab"),
    ("Diagnostics",   "ui.tabs.diagnostics_tab"),
    ("History",       "ui.tabs.history_tab"),
    ("Live (Paper)",  "ui.tabs.live_tab"),
    ("Paper",         "ui.tabs.paper_tab"),
    ("Live Monitor",  "ui.tabs.live_monitor"),
    ("Report",        "ui.tabs.report_tab"),
    ("ML",            "ui.tabs.ml_tab"),
]

pages: list[tuple[str, object]] = []
for title, module_path in TAB_SPECS:
    pages.append((title, _safe_import(module_path, title)))

# Tabs oluştur ve tek tip run(state) çağır
tabs = st.tabs([title for title, _ in pages])
for i, (name, mod) in enumerate(pages):
    with tabs[i]:
        try:
            mod.run(state)  # her modül run(state) imzasını uygulamalı
        except Exception as e:
            st.error(f"{name} sekmesi hata verdi: {e}")
            st.exception(e)

# Opsiyonel: Registry durumunu footer’da göster (debug için faydalı)
try:
    if get_registry:
        REG, ORDER = get_registry()
        with st.expander("ℹ️ Registry durumu"):
            st.json({
                "count": len(ORDER),
                "first_entries": ORDER[:5],
            })
except Exception:
    pass

from __future__ import annotations
import streamlit as st
from utils.exceptions import AppError, StrategyValidationError, DataIntegrityError

def show_error(err: Exception, *, title: str|None=None, key: str|None=None) -> None:
    """Render a friendly error banner in Streamlit."""
    if isinstance(err, StrategyValidationError):
        st.error(f"❌ Strategy error: {err}", icon="⚠️")
    elif isinstance(err, DataIntegrityError):
        st.error(f"❌ Data error: {err}", icon="🧱")
    elif isinstance(err, AppError):
        st.error(f"❌ {err}", icon="❗")
    else:
        # Fallback with minimal leakage (no full trace by default)
        st.error(f"""Unexpected error: {type(err).__name__}

{str(err)}""", icon="💥")

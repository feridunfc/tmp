# ALGO5 – Week 5-6 Overlay

## Week 5 (Security + Live Paper)
- `security/rbac.py`: roles (`viewer`, `trader`, `admin`), `require(action)`
- `security/secrets.py`: env-based secrets (`ALGO5_SECRET__BINANCE__API_KEY`)

UI:
- `ui/tabs/live.py`: RBAC-protected market-order paper fill (uses W2 matcher).

## Week 6 (Robustness)
- `robustness/jitter.py`: gaussian jitter on returns
- `robustness/worst_days.py`: remove best/worst k days
- `robustness/mc.py`: block bootstrap on returns

UI:
- `ui/tabs/robustness.py`: run a stress and compare metrics/equity.

### Run
```
pip install -e ".[test]"
pytest tests/security tests/robustness -q
streamlit run ui/streamlit_app_w56.py
```

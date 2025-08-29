# ALGO5 – WEEK-1 (Data Layer) Snapshot

This archive contains the Week-1 deliverables:
- **Data validation + quality report + integrity checksum**
- **Deterministic reproducibility seed**
- **FeatureStore + Parquet cache (env-configurable)**
- **Streamlit Data tab** (quality check + feature build)
- **Unit tests + CI workflow (data.yml)**

## Quick start
```bash
pip install -e ".[dev,test]"
pytest tests/data -q
streamlit run ui/streamlit_app.py
```

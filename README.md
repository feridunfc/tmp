# ALGO5 – Week-1 (Data Layer)

- Data Quality Monitor (schema/NaN + checksum)
- FeatureStore with Parquet caching
- Streamlit UI tab (Data) with "Check Quality" and "Build Cache"

## Dev quickstart

```bash
pip install -e ".[test,ui]"
pytest tests/data -q
streamlit run ui/streamlit_app.py
```

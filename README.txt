Week-1 Fix Pack (Data Layer)
- Drop 'src', 'ui', 'tests' folders into your repo root.
- Ensure PYTHONPATH points to ./src when running tests, or install editable if you have pyproject.
Commands:
  $env:PYTHONPATH="$pwd/src"; pytest tests/data -q
  streamlit run ui/streamlit_app.py

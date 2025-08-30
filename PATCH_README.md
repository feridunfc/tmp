
# W12–W14 Patch (drop-in)

Apply on top of your repo root. Adds:
- Week 12: Regime features/labeler and hybrid regime-aware strategy (+ tests, UI tab, CI)
- Week 13: MLOps registry/drift/A-B (+ tests, UI tab, CI)
- Week 14: Explainability (permutation + SHAP/LIME adapters, tests, UI tab, CI)

## Install & Test
```
pip install -e ".[test]"
pytest tests/regime tests/strategies tests/mlops tests/explain -q
```
## UI
```
streamlit run ui/streamlit_app.py
```

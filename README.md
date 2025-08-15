# e1.8.4 Minimal Sandbox

**Run UI**

```bash
streamlit run ui/streamlit_app.py
```

If you use `yfinance`, intraday for some tickers may fail. Default `synthetic` is reliable.

**Smoke Test (CLI)**

```bash
python -c "import sys, json; sys.path.insert(0,'src'); from pipeline.orchestrator import run_pipeline; cfg={'mode':'backtest','out_dir':'runs/smoke','data':{'source':'synthetic','symbols':['BTC-USD','ETH-USD'],'freq':'30min','seed':42},'fees':{'capital':10000,'fee_bps':5,'slippage_bps':5},'strategy':{'name':'ma_crossover','params':{'ma_fast':10,'ma_slow':30}}}; print(run_pipeline(cfg))"
```

Artifacts are written under `runs/...`.

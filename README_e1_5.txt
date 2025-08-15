
# Algo-Trade e1.5 (stable)

**Ne var?**
- Çalışan backtest/live-stub pipeline (synthetic veya yfinance fallback)
- 3 konvansiyonel strateji (MA, RSI, BB)
- Optuna ile MA tuning (isteğe bağlı)
- Portföy çoklu-asset, eşit ağırlık
- Metrikler: total_return, sharpe, maxdd
- Artefaktlar: per-asset CSV'ler, portfolio_equity.csv, metrics.txt, report_full.html
- Streamlit UI (sidebar + 4 tab)

**Kurulum**
1. `pip install streamlit numpy pandas matplotlib optuna` (+ `yfinance` opsiyonel)
2. Bu zip'i projenizde uygun klasöre çıkarın (ör: proje kökünde `ui/` ve `src/` olarak).
3. `streamlit run ui/streamlit_app.py`

**Notlar**
- Varsayılan tarih aralığı: son 180 gün (intraday) / 730 gün (daily).
- ML/Hybrid paketleri e1.6+ ile gelecek. 
- Her run için `ui_runs/run_YYYYMMDD_HHMMSS/` altında dosyalar oluşur.

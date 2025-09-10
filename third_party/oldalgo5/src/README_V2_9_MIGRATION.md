
# ALGO2 v2.9 Migration Notes

This drop adds:
- Data validator & leakage-safe normalizer
- Hybrid FeatureStore (DuckDB optional)
- Strategy core (base/registry) + sample SMA crossover
- Risk Chain (max leverage / concentration / vol cap)
- Execution gateways (backtest/paper/live stubs)
- Robustness & StrategyAnalyzer
- ExperimentLogger (SQLite)
- Prometheus monitor (optional)

Integrate with UI:
- `from algo2.core.strategies.registry import list_strategies, get_strategy`
- `from algo2.reporting.robustness import monte_carlo_bootstrap, worst_k_days`

If Streamlit warns about duplicate keys, pass unique `key=` to chart widgets.

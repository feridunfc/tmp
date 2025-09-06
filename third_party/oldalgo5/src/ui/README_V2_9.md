
# UI Integration Hints

- Use unique `key=` for every `st.plotly_chart` and `st.bar_chart` call.
- When using robustness:
    ```python
    from algo2.reporting.robustness import monte_carlo_bootstrap, worst_k_days
    mc = monte_carlo_bootstrap(results['returns'], n=500)
    st.plotly_chart(fig, key='mc_hist_sharpe')
    ```
- Experiment logger:
    ```python
    from algo2.experiments.logger import ExperimentLogger
    logger = ExperimentLogger('results/experiments.db')
    run_id = logger.log_run('backtest', params, metrics, {'equity':'path.csv'})
    ```

# AlgoSuite Backtest & Risk Patch v3
Bu yama 1-3 numaralı istekleri karşılayacak şekilde genişletilmiş entegrasyon sağlar.

Eklenen önemli dosyalar:
- `src/core/risk/advanced.py` : ATR tabanlı stoplar, position sizing by percent risk, portfolio limits.
- `src/core/backtest/engine_v2.py` : Vectorized multi-asset backtest engine. Backward compatible adaptor provided.
- `src/train/optimizer.py` : GridSearch, RandomSearch, and Walk-Forward Analysis helper.
- `src/core/backtest/adapter_v3.py` : kolay çağrı fonksiyonu `run_backtest_v3`.
- `configs/backtest_wfa_defaults.json` : WFA ve optimization defaultları.

Entegrasyon adımları:
1. ZIP içeriğini proje köküne açın.
2. Orchestrator içinde yeni engine'ı şu şekilde çağırın:

    from src.core.backtest.adapter_v3 import run_backtest_v3
    result = run_backtest_v3(prices, strategy_fn, cfg, capital=cfg.get('capital',100000.0), project_root=PROJECT_ROOT)

3. WFA kullanımı için `src.train.optimizer.walk_forward_analyze` fonksiyonunu kullanın; cfg içine `engine` anahtarına `run_backtest_v3`'ü verin.

Örnek WFA:
    from src.train.optimizer import walk_forward_analyze
    cfg['engine'] = lambda prices, strat, c: run_backtest_v3(prices, strat, c)
    res = walk_forward_analyze(prices, strategy_builder, cfg, n_splits=3)

Test önerileri:
- Küçük dict formatında fiyat verisi (ör. {'BTC-USD': df, 'ETH-USD': df2}) ile çalıştırın.
- GridSearch/RandomSearch üzerinde `objective_fn` olarak portfolio Sharpe ya da total_return seçin.

Not: Bu patch non-invasive olacak şekilde tasarlandı. Daha ileri entegrasyon (ör. parallelization, optimized vector math) istersen söyle, onu da eklerim.

# AlgoSuite Backtest & Risk Engine Patch

Bu yama, mevcut projeyi çok değiştirmeden "Backtest" ve "Risk" motorlarını güçlendirmek amacıyla hazırlanmıştır.
İçerik:
- `src/core/backtest/engine.py`: Daha gerçekçi backtest özellikleri (pozisyon boyutlama, komisyon/slippage, stop-loss & trailing-stop, trade kayıtları, temel metrikler).
- `src/core/backtest/_utils.py`: Yardımcı fonksiyonlar.
- `src/core/risk/engine.py`: Risk hesaplayıcı (position sizing stratejileri, historical VaR & CVaR, volatility targeting). 
- `configs/backtest_defaults.json`: Varsayılan backtest ve risk parametreleri (UI/Config ile merge için).

Nasıl entegre edilir (öneri):
1. `src/core/backtest/engine.py` dosyasını repo'ya ekleyin veya mevcut `backtest_one` fonksiyonunu bu fonksiyonun sunduğu özelliklerle zenginleştirin.
2. `src/core/risk/engine.py` dosyasını `src/core/risk/` altına koyun ve import yollarını düzenleyin.
3. `configs/backtest_defaults.json` içindeki anahtarları `AppConfig` yükleme/merge mantığınıza ekleyin (ör. cfg['risk'], cfg['execution'], cfg['stop']).
4. UI tarafında `Run` sekmesinde yeni `execution` ve `risk` parametreleri gösterilebilir (Beginner profilinde varsayılanlarla gizli kalır).

Test/Deneme önerisi:
- Mevcut `strategy_fn`'inizi küçük bir DataFrame üzerinde çalıştırarak `run_backtest` çıktısını kontrol edin.
- `allow_short` parametresini True yapıp short senaryolarını sınayın.
- `configs/backtest_defaults.json` dosyasındaki değerleri UI ile uyumlu hale getirin.

Not: Bu yama, kod bazlı entegrasyon gerektirir; değişiklikleri minimal tutmaya çalıştım. Daha ileri optimizasyon (multi-asset simultane pozisyon yönetimi, multi-currency funding, margin sim) isterseniz daha kapsamlı bir patch hazırlarım.

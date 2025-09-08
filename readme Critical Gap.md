# Critical Gaps & Execution Plan (Algo Trading Platform)

Bu doküman; bu sohbette konuşulan tüm başlıkları ve endüstri/akademik yaklaşımlarla tam otonom çalışabilen bir **algorithmic trading** sisteminin gerekliliklerini **gap listesi + yapılacaklar** olarak birleştirir.

---

## 0) Hedefler ve KPI’lar

- **Hedefler:** Otonom, düşük gecikmeli, güvenli ve izlenebilir bir alım-satım platformu; geriye dönük ve ileriye dönük doğrulama ile sürdürülebilir performans.
- **Temel KPI’lar:**
  - **PnL** (net), **Sharpe**, **Sortino**, **Max Drawdown**, **Hit Ratio**, **Turnover**, **Slippage**, **Fill Rate**
  - **Latency p95/p99** (md feed → sinyal → emir), **Reject Rate**, **Error Budget**
  - **Model**: Accuracy/AUC, Drift, Feature Freshness
  - **ESG**: kWh/işlem, gCO₂e/işlem, CPU/GPU saatleri

---

## 1) Event-Driven Mimari (Eksik)

**Sorun:** Senkron akış ve sıkı bağ; ölçeklenebilirlik ve izolasyon zayıf.
**Hedef Durum:** Publish/Subscribe tabanlı, **event-first** mimari (Kafka/RabbitMQ); **Outbox Pattern**, idempotent tüketiciler, **schema registry** (Avro/Protobuf).

**Yapılacaklar**
- Domain event sözlüğü + şema versiyonlama
- Outbox + transactional publisher (CDC/Debezium opsiyonel)
- Consumer retry, **DLQ**, backoff; **exactly-once/at-least-once** kararı
- Event-driven blueprint & şablon servis

**Kabul Kriterleri**
- En az **1 uçtan uca iş akışı** tamamen event-driven
- E2E latency p95 hedefi tanımlı ve dashboard’da görünür

---

## 2) Real-Time Processing (Yetersiz)

**Sorun:** Batch bağımlılığı, canlı veri akışında gecikme.
**Hedef Durum:** Streaming motoru (Flink/Spark/Kafka Streams) + **stateful operators**, watermarking, out-of-order toleransı; front-end’e **SSE/WebSocket**.

**Yapılacaklar**
- Kritik akış için streaming POC (tick → feature → sinyal)
- **Redis/KeyDB** ile düşük gecikmeli feature cache
- WebSocket/SSE ile canlı portföy & emir akışı
- p95 <X ms> hedefi + uyarı eşikleri

**Kabul Kriterleri**
- p95 hedefi 1 hafta prod gözleminde karşılanır
- Backpressure ve drop gözlenmiyor

---

## 3) Veri & Piyasa Mikro Yapısı (Eksik)

**Sorun:** Tick/derinlik verisi, corporate action/temettü ayarlamaları ve zaman senkronu eksik.
**Hedef Durum:** **Zaman serisi veri gölü** (ClickHouse/Parquet+Iceberg/Delta), **order book** snapshot + incremental, **PTP/NTP** ile clock doğruluğu.

**Yapılacaklar**
- Kaynak adaptörleri (market data, broker), replay kabiliyeti
- Kur/shares-adjusted tarihsel veri, survivorship bias önleme
- Clock sync politikası (PTP tercih, aksi NTP + jitter ölçümü)
- Data quality: missing/dup dedup, schema enforcement

**Kabul Kriterleri**
- Replay ile deterministik backtest eşleşmesi ≥ %99
- Veri kalite raporu (günlük) + otomatik alarm

---

## 4) Modelleme & Gelişmiş AI/ML (Eksik)

**Sorun:** Kurallı/heuristic ağırlığı; genelleme ve kişiselleştirme zayıf.
**Hedef Durum:** **Feature Store** (Feast vb.), **Model Servisleme** (FastAPI/GRPC), **drift izleme**, **A/B / canary**, **online/mini-batch** güncelleme.

**Akademik / Endüstri Yaklaşımları**
- **Lopez de Prado**: **Purged K-Fold** + **embargo**, **Deflated Sharpe**, **Meta-Labeling**, **Triple-Barrier** etiketleme
- **Walk-Forward** optimizasyon, **Compositional Cross-Validation**
- **Microstructure**: Order book imbalance, queue position, Almgren-Chriss etki/sürünme modelleri
- **Portföy**: **HRP** (Hierarchical Risk Parity), volatilite hedefleme, fraksiyonel **Kelly**

**Yapılacaklar**
- Öncelikli sinyal ailesi seçimi (momentum/mean-rev/market-making vb.)
- Labeling: triple-barrier + meta-labeling POC
- Feature store + tazelik SLA’ları
- Model gateway + canary, shadow live

**Kabul Kriterleri**
- Prod’da **en az 1 model** canlı; drift & performans grafikleri
- A/B test ile istatistiksel anlamlı iyileşme

---

## 5) Backtest, Simülasyon ve Doğrulama (Eksik)

**Sorun:** Overfitting ve veri sızıntısı riskleri; kârlılık metrikleri güvensiz.
**Hedef Durum:** **Bias-free** backtest; **transaction cost** ve **market impact** dahil; **paper-trading** ve **shadow-live** katmanı.

**Yapılacaklar**
- Purged K-Fold + embargo ile CV; **Deflated Sharpe** raporu
- Komisyon, spread, slippage, kısmi dolum, queue-priority simülasyonu
- Walk-forward & monte-carlo stress; *regime shift* senaryoları
- Paper & shadow live pipeline (prod feed + sanal emir)

**Kabul Kriterleri**
- Backtest ↔ shadow-live sapması kabul bandı içinde (< ε)
- TCA (Transaction Cost Analysis) raporları otomatik üretilir

---

## 6) Emir Yönlendirme & Yürütme (Eksik)

**Sorun:** Best-execution, risk sınırları ve “kill switch” eksikleri.
**Hedef Durum:** **FIX/REST/WS** çoklu aracı/borsa entegrasyonu, **pre-trade risk** (limit, notional, fiyat bandı), **throttle**, **circuit-breaker**, **cancel-all**.

**Yapılacaklar**
- Execution gateway (order router) + venue abstraction
- Slippage/market-impact ölçümü ve adaptif parçalama (TWAP/VWAP/POV)
- Rate-limit ve backoff politikaları; otomatik re-route
- **Kill-switch** ve “safe-mode” prosedürü

**Kabul Kriterleri**
- Reject rate < hedef, failover testleri başarılı
- Cancel-all ve throttle senaryoları tatbikatla doğrulanır

---

## 7) Risk Yönetimi & Portföy (Yetersiz)

**Sorun:** Pozisyon boyutlama ve risk bütçeleri net değil.
**Hedef Durum:** **Vol target**, **Kelly (fractional)**, **VaR/ES**, **position/sector/venue** limitleri; **risk parity/HRP** türevi portföy.

**Yapılacaklar**
- Risk bütçeleri (günlük/haftalık), stop-out ve **drawdown guard**
- Pozisyon boyutlama kütüphanesi (vol target, Kelly f)
- VaR/ES tahmini ve alarm eşikleri
- Hedging kuralları (örn. beta-hedge)

**Kabul Kriterleri**
- Limit ihlallerinde otomatik pozisyon azaltma/kapama
- Drawdown > X% → strateji devre dışı + uyarı

---

## 8) Observability, SRE & Olay Müdahalesi (Eksik)

**Hedef Durum:** **OpenTelemetry** iz, metrik, log; **Prometheus/Grafana** panoları; **SLO/SLA**; olay yönetimi, **runbook**.

**Yapılacaklar**
- Strat-başına PnL, Sharpe, DD; execution fill/latency; feed-lag
- p50/p95/p99 laten­cy; consumer lag; error budget
- Alert routing (Opsgenie/PagerDuty/Slack) + runbook
- **Postmortem** şablonu ve haftalık review

**Kabul Kriterleri**
- Tüm kritik akışlar için pano + alarm kapsaması ≥ %95
- Olay çözüm süresi (MTTR) hedefe iniyor

---

## 9) Güvenlik, Gizlilik ve Uyumluluk (Eksik)

**Hedef Durum:** **Least privilege**, **OIDC + cloud secrets** (Vault/Secrets Manager), **SBOM** (CycloneDX), bağımlılık taraması, imzalı container’lar; **MiFID II / Best Execution** prensipleri, denetim izleri.

**Yapılacaklar**
- API anahtarları: KMS/Secrets Manager, rotasyon, audit log
- 2FA, donanım anahtarı opsiyonu; imzalı build & provenance
- Bağımlılık güvenliği (Dependabot/OSV-Scanner), lisans kontrolü
- Best-execution & TCA raporlarının arşivi; saat senkron kayıtları

**Kabul Kriterleri**
- Sızma testi bulguları kapalı; anahtar rotasyon politikası canlı
- Denetim izleri 5+ yıl saklama politikası tanımlı

---

## 10) ESG & Sürdürülebilirlik (Yetersiz)

**Hedef Durum:** Enerji/karbon görünürlüğü; işlem başına **kWh** ve **gCO₂e**; **eşik aşımlarında uyarı**.

**Yapılacaklar**
- Telemetry → enerji/karbon tahmini katmanı
- Haftalık ESG raporu + dashboard
- Model/altyapı optimizasyon önerileri (ör. batch vs. GPU saatleri)

**Kabul Kriterleri**
- KPI’lar dashboard’da; eşik aşımlarında alarm
- Release’lerde ESG değişim etkisi raporlanır

---

## 11) Platform & DevEx

**Durum:** CI (pytest-cov, ruff, black, mypy) mevcut; artefakt ve rozet eklendi.
**Genişletme:**
- **Monorepo paketleme**, **pre-commit** kuralları, **conventional commits**
- **Docker/Compose** template; **IaC** (Terraform) ile çevreler
- **Ephemeral env** + **integration test** (paper-trading/sandbox)

---

## Yol Haritası (Now / Next / Later)

- **NOW (0-4 hafta):** Event-driven temel, streaming POC, execution gateway v1, backtest doğrulama altyapısı, risk limitleri, observability temel panoları.
- **NEXT (1-3 ay):** Feature store, labeling + meta-labeling, canary deploy, TCA otomasyon, ESG dashboard, security hardening (secrets, SBOM).
- **LATER (3-6 ay):** Multi-venue router optimizasyonu (adaptif), online/mini-batch öğrenme, gelişmiş portföy (HRP/hedge), multi-asset desteği.

---

## Mimari Taslak (Mermaid)

```mermaid
flowchart LR
  MD[(Market Data)] -->|ticks/L2| SP[Stream Proc]
  SP --> FS[(Feature Store)]
  FS --> MS[(Model Serving)]
  MS --> SIG{Signal}
  SIG --> EX[Execution Gateway]
  EX --> VENUE1[[Broker/Exchange A]]
  EX --> VENUE2[[Broker/Exchange B]]

  subgraph Storage
    DL[(Data Lake: Parquet/ClickHouse)]
    BT[(Backtest Store)]
  end
  SP --> DL
  EX --> DL
  MS --> DL
  DL --> BT

  subgraph Obs
    OTEL[OpenTelemetry]
    GRAF[Prometheus/Grafana]
  end
  SP -.-> OTEL
  MS -.-> OTEL
  EX -.-> OTEL
  OTEL --> GRAF

## Snapshot - 2025-09-08

### 1) Modül Durumu (Bizde)
| Modül | Bizdeki Durum | Yorum |
|---|---|---|
| Event Bus | src/algo5/core/eventbus.py (basit) | Temel var; Kafka/Redis ile genişlet |
| Veri Katmanı | provider.py, loaders/, feature_store.py | Var; normalize + checksum eksik |
| TA Özellikler | ta_features.py (rolling, lag) | Var; micro-structure yok |
| AI Model | ai_unified.py (RF) | Sadece RF; XGB/LGBM/NN yok |
| Risk Chain | risk/rules.py (SL/TP/MaxDD) | Var; Kelly/VolTarget/VaR/Drawdown yok |
| Backtest | walkforward.py (WF) | Var; 1-bar delay var; MC/stress yok |
| UI (Streamlit) | ui/tabs/(Data, Train, Run, Compare) | Var; hata paneli + CSV export eksik |
| Registry | STRATEGY_REGISTRY | Boş; doldurulmalı |

### 2) Taslakta Var – Bizde Yok (Öncelik)
| Eksik Bileşen | Öncelik | Açıklama |
|---|:---:|---|
| Micro-structure (LOB imbalance, VPIN) | 🔴 | Kısa-vadeli edge; code-ready |
| Kelly / Vol-target / VaR | 🔴 | Pozisyon boyutlama |
| XGB/LGBM/NN/RL | 🔴 | Model çeşitliliği |
| Monte-Carlo / Stress | 🟡 | Robustness |
| Sentiment (NLP) | 🟡 | Haber/Twitter |
| On-chain (whale) | 🟡 | Kripto-alpha |
| Live Kill-Switch | 🔴 | Canlı risk |
| Compare CSV export | 🟢 | UI kolaylık |

### 3) Hemen Açılacak 5 PR
| PR | Eksik | Tahmini Gün |
|---|---|---|
| PR-A | XGBStrategy + LGBMStrategy (registry doldur) | 1 |
| PR-B | KellyPositionSizer + VolTargetRule | 1 |
| PR-C | MonteCarloStress (1000 path, VaR/CVaR) | 1 |
| PR-D | MicrostructureFeatures (VPIN, OB imbalance) | 1 |
| PR-E | CompareTab CSV Export + UI Error Panel | 0.5 |

### 4) Kod İskelet Referansları
- src/algo5/risk/kelly_sizer.py – Kelly sizing yardımcıları
- src/algo5/features/microstructure.py – VPIN / OB imbalance proxy
- src/algo5/robustness/mc_stress.py – MC path & VaR/CVaR

---

## Snapshot - 2025-09-08

### 1) Modül Durumu (Bizde)
| Modül | Bizdeki Durum | Yorum |
|---|---|---|
| Event Bus | src/algo5/core/eventbus.py (basit) | Temel var; Kafka/Redis ile genişlet |
| Veri Katmanı | provider.py, loaders/, feature_store.py | Var; normalize + checksum eksik |
| TA Özellikler | ta_features.py (rolling, lag) | Var; micro-structure yok |
| AI Model | ai_unified.py (RF) | Sadece RF; XGB/LGBM/NN yok |
| Risk Chain | risk/rules.py (SL/TP/MaxDD) | Var; Kelly/VolTarget/VaR/Drawdown yok |
| Backtest | walkforward.py (WF) | Var; 1-bar delay var; MC/stress yok |
| UI (Streamlit) | ui/tabs/(Data, Train, Run, Compare) | Var; hata paneli + CSV export eksik |
| Registry | STRATEGY_REGISTRY | Boş; doldurulmalı |

### 2) Taslakta Var – Bizde Yok (Öncelik)
| Eksik Bileşen | Öncelik | Açıklama |
|---|:---:|---|
| Micro-structure (LOB imbalance, VPIN) | 🔴 | Kısa-vadeli edge; code-ready |
| Kelly / Vol-target / VaR | 🔴 | Pozisyon boyutlama |
| XGB/LGBM/NN/RL | 🔴 | Model çeşitliliği |
| Monte-Carlo / Stress | 🟡 | Robustness |
| Sentiment (NLP) | 🟡 | Haber/Twitter |
| On-chain (whale) | 🟡 | Kripto-alpha |
| Live Kill-Switch | 🔴 | Canlı risk |
| Compare CSV export | 🟢 | UI kolaylık |

### 3) Hemen Açılacak 5 PR
| PR | Eksik | Tahmini Gün |
|---|---|---|
| PR-A | XGBStrategy + LGBMStrategy (registry doldur) | 1 |
| PR-B | KellyPositionSizer + VolTargetRule | 1 |
| PR-C | MonteCarloStress (1000 path, VaR/CVaR) | 1 |
| PR-D | MicrostructureFeatures (VPIN, OB imbalance) | 1 |
| PR-E | CompareTab CSV Export + UI Error Panel | 0.5 |

### 4) Kod İskelet Referansları
- src/algo5/risk/kelly_sizer.py – Kelly sizing yardımcıları
- src/algo5/features/microstructure.py – VPIN / OB imbalance proxy
- src/algo5/robustness/mc_stress.py – MC path & VaR/CVaR

---

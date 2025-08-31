# Changelog
All notable changes to this project will be documented in this file.

The format is based on **Keep a Changelog**, and this project adheres to **Semantic Versioning**.

## [Unreleased]
### Added
- (placeholder) Add new execution tests (IOC/FOK, bracket, trailing).
### Changed
- (placeholder)
### Fixed
- (placeholder)
### Security
- (placeholder)

## [0.1.1] - 2025-08-31
### Fixed
- **Order-invariant checksum:** `df_checksum` artık kolonları alfabetik, satırları index’e göre sıralayarak hash’ler; bar sırası değişse de checksum sabit.  
- **Outlier fallback:** IQR=0 durumları için median–deviation tabanlı fallback ile uç değerler doğru yakalanır.  
- **Back-compat rapor:** `DataQualityMonitor` çıktısında `SchemaCheck` alias’ı eklendi (eski dashboard/test beklentileri için).

### Security
- **Base dir enforcement:** `DataQualityMonitor` artık `base_dir` dışına yazma girişimlerinde **PermissionError** fırlatır (directory traversal’a karşı).  
- **SHA-256:** integrity modülü zaten SHA-256 kullanıyor; bu sürümle davranış netleştirildi.

### Changed
- **Loader/Schemas 2025-ready:** demo veri üreticisi UTC-safe, ESG proxy içeriyor; `schemas` dtype/JSON Schema entegrasyonu güncellendi.

### Tests
- `tests/data/…` kapsamı genişletildi (integrity/monitor/schemas/validate/loader).  
- `Volume` → `volume` kanonikleştirmesine uygun test düzeltmeleri.

### Notes
- **Data katmanı** Week-1 kapsamı **FROZEN** (yalnızca güvenlik/bugfix kabul).  
- Sürüm: `0.1.1`

## [0.1.0] - 2025-08-31 (Week-1)
### Added
- **2025-ready validator:** dtype coercion, DST-safe UTC normalize, NaN/outlier raporu, deterministik checksum, ESG proxy, opsiyonel JSON payload (Pydantic).  
- **DQ monitor:** JSON audit raporu + Prometheus metrikleri (NaN/outlier/ESG/size).  
- **Integrity:** checksum/seed yönetimi.  
- **Schemas:** kanonik kolonlar ve dtype haritası.  
- **CI (data gate):** ruff + pytest + coverage ≥ 80%.

---

[Unreleased]: https://github.com/feridunfc/tmp/compare/v0.1.1...main
[0.1.1]: https://github.com/feridunfc/tmp/compare/v0.1.0...0.1.1
[0.1.0]: https://github.com/feridunfc/tmp/releases/tag/v0.1.0

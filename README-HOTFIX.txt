HOTFIX v2.2.1 — 2025-08-13T05:40:56.711429Z

Dosyalar:
- ui/st_tabs.py  → Streamlit duplicate-id ve chart key uyumsuzluğu düzeltildi.
  * Tüm widget’lara benzersiz key verildi (train_*, run_*, data_*, cmp_*).
  * line_chart/area_chart çağrılarından key= argümanı kaldırıldı (eski Streamlit ile uyum).
  * Strateji listeleri, core.strategies.ALL_STRATEGIES registry’sinden güvenli çekiliyor.
  * Tuning/Run tarihleri default: bugün & 1 yıl önce.

Kurulum:
1) Bu zip'i açın.
2) Projenizdeki mevcut ui/st_tabs.py dosyasını bununla değiştirin.
3) `streamlit run ui/streamlit_app.py` ile açın.

Not:
- Eğer yeni AI/Hibrid stratejiler ALL_STRATEGIES'e eklenmemişse UI’da görünmez.
- Registry’de hangi isimler varsa, UI yalnızca onları gösterir (KeyError engellendi).

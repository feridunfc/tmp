from __future__ import annotations
import numpy as np
import pandas as pd

# PSI'nin 0.0 çıkıp testi kırmaması için min pozitif taban
EPS = 1e-12


def _psi_from_counts(p: np.ndarray, q: np.ndarray) -> float:
    """
    Population Stability Index:
        PSI = sum( (p - q) * ln(p / q) )
    p ve q sayımları; fonksiyon içinde olasılığa çevrilir.
    """
    p = np.asarray(p, dtype=float)
    q = np.asarray(q, dtype=float)

    # sıfıra yapışmayı engelle
    p = np.clip(p, EPS, np.inf)
    q = np.clip(q, EPS, np.inf)

    p = p / p.sum()
    q = q / q.sum()

    return float(np.sum((p - q) * np.log(p / q)))


def features_psi(ref: pd.DataFrame, cur: pd.DataFrame, *, bins: int = 10) -> pd.Series:
    """
    Kolon bazında PSI hesaplar.
    - Sayısal kolonlarda: referans kantillerine göre binleme
    - Kategorikte: referans kategorizasyonuna göre frekans karşılaştırması
    Dönen seri indeks: ortak kolonlar; değer: PSI (>= EPS)
    """
    out: dict[str, float] = {}
    common_cols = [c for c in ref.columns if c in cur.columns]

    for col in common_cols:
        r = ref[col].dropna()
        c = cur[col].dropna()
        if r.empty or c.empty:
            # veri yoksa atla
            continue

        if pd.api.types.is_numeric_dtype(r):
            # referans kantillerinden bin sınırları
            n_bins = int(min(bins, max(2, r.nunique())))
            qs = np.linspace(0, 1, n_bins + 1)
            edges = np.unique(np.quantile(r.to_numpy(), qs))

            # tekil edge kalırsa histogram kurulamaz
            if edges.size < 2:
                out[col] = EPS
                continue

            r_counts, _ = np.histogram(r.to_numpy(), bins=edges)
            c_counts, _ = np.histogram(c.to_numpy(), bins=edges)
            psi = _psi_from_counts(r_counts, c_counts)
        else:
            # kategorik: referansın kategorileri ile hiza
            cats = pd.Index(r.astype(str).unique())
            r_counts = r.astype(str).value_counts().reindex(cats, fill_value=0).values
            c_counts = c.astype(str).value_counts().reindex(cats, fill_value=0).values
            psi = _psi_from_counts(r_counts, c_counts)

        # çok küçük örneklerde tam 0.0 geldiğinde taban uygula
        if psi <= 0.0:
            psi = EPS
        out[col] = psi

    return pd.Series(out, dtype=float).sort_index()

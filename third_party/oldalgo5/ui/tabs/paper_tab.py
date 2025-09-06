# # # ui/tabs/paper_tab.py
# #
# # import math
# # from typing import Optional, Any, Dict
# #
# # import pandas as pd
# # import streamlit as st
# #
# #
# # # ---------------------- helpers ---------------------- #
# # def _resolve_last_px(symbol: Optional[str], engine: Any, price_df: Optional[pd.DataFrame] = None) -> float:
# #     """Motor/broker/df üzerinden son fiyatı bul. Bulamazsa NaN döndür."""
# #     if not symbol:
# #         return float("nan")
# #
# #     # 1) engine.get_last_price
# #     if hasattr(engine, "get_last_price"):
# #         try:
# #             px = engine.get_last_price(symbol)
# #             if px is not None:
# #                 return float(px)
# #         except Exception:
# #             pass
# #
# #     # 2) engine.broker.get_last_price
# #     br = getattr(engine, "broker", None)
# #     if br is not None and hasattr(br, "get_last_price"):
# #         try:
# #             px = br.get_last_price(symbol)
# #             if px is not None:
# #                 return float(px)
# #         except Exception:
# #             pass
# #
# #     # 3) DataFrame son kapanış
# #     if isinstance(price_df, pd.DataFrame) and len(price_df) > 0:
# #         for col in ("close", "Close", "price", "last"):
# #             if col in price_df.columns:
# #                 try:
# #                     return float(price_df[col].iloc[-1])
# #                 except Exception:
# #                     pass
# #
# #     return float("nan")
# #
# #
# # def _positions_to_df(positions: Dict[str, Dict[str, Any]]) -> pd.DataFrame:
# #     if not positions:
# #         return pd.DataFrame(columns=["symbol", "qty", "avg_price", "unrealized_pnl"])
# #     rows = []
# #     for sym, pos in positions.items():
# #         rows.append({
# #             "symbol": sym,
# #             "qty": pos.get("qty", pos.get("quantity", 0.0)),
# #             "avg_price": pos.get("avg_price", pos.get("average_price", float("nan"))),
# #             "unrealized_pnl": pos.get("unrealized_pnl", float("nan")),
# #         })
# #     return pd.DataFrame(rows)
# #
# #
# # # ---------------------- main tab ---------------------- #
# # def run(state):
# #     # --- engine/symbol güvenli şekilde al ---
# #     engine = (
# #         state.get("paper_engine")
# #         or state.get("engine")
# #         or st.session_state.get("paper_engine")
# #         or st.session_state.get("engine")
# #     )
# #     if engine is None:
# #         st.info("Paper motoru bulunamadı. Lütfen Paper/Live motorunu başlatın.")
# #         return
# #
# #     # Semboller (varsa pozisyonlardan ya da state'ten)
# #     positions_dict = getattr(engine, "positions", {}) or {}
# #     known_symbols = list(positions_dict.keys())
# #
# #     default_symbol = (
# #         state.get("paper_symbol")
# #         or state.get("symbol")
# #         or (known_symbols[0] if known_symbols else None)
# #         or getattr(engine, "symbol", None)
# #     )
# #
# #     st.subheader("Paper Trading")
# #
# #     # Sembol seçimi
# #     if known_symbols:
# #         symbol = st.selectbox("Sembol", options=known_symbols, index=0 if default_symbol in known_symbols else 0)
# #     else:
# #         symbol = st.text_input("Sembol", value=default_symbol or "" ).strip() or None
# #
# #     # Fiyat/veri kaynakları
# #     bars_df = (
# #         state.get("bars")
# #         or state.get("price_df")
# #         or getattr(engine, "bars", None)
# #         or getattr(engine, "price_df", None)
# #     )
# #
# #     # --- metrikler ---
# #     last_px = _resolve_last_px(symbol, engine, bars_df)
# #
# #     c1, c2, c3, c4 = st.columns(4)
# #     with c1:
# #         st.metric("Total Value", f"${getattr(engine, 'portfolio_value', 0.0):,.2f}")
# #     with c2:
# #         st.metric("Cash", f"${getattr(engine, 'cash', 0.0):,.2f}")
# #     with c3:
# #         pnl = getattr(engine, "realized_pnl", 0.0)
# #         st.metric("Realized PnL", f"${pnl:,.2f}")
# #     with c4:
# #         label = f"{(symbol or '-')} Last"
# #         value = "-" if (last_px != last_px or math.isnan(last_px)) else f"{last_px:.4f}"
# #         st.metric(label, value)
# #
# #     st.divider()
# #
# #     # --- pozisyonlar ---
# #     st.markdown("#### Pozisyonlar")
# #     pos_df = _positions_to_df(positions_dict)
# #     st.dataframe(pos_df, width='stretch', hide_index=True)
# #
# #     st.divider()
# #
# #     # --- hızlı emir alanı ---
# #     st.markdown("#### Hızlı Emir")
# #     col_a, col_b, col_c, col_d = st.columns([2, 1, 1, 1])
# #     with col_a:
# #         sel_symbol = st.text_input("Sembol (emir)", value=symbol or "")
# #     with col_b:
# #         side = st.selectbox("Yön", options=["buy", "sell"], index=0)
# #     with col_c:
# #         qty_str = st.text_input("Miktar", value="1")
# #     with col_d:
# #         mkt = st.checkbox("Market", value=True)
# #
# #     place = st.button("Emri Gönder")
# #     if place:
# #         try:
# #             q = float(qty_str)
# #             if not sel_symbol:
# #                 st.warning("Sembol gerekli.")
# #             elif q <= 0:
# #                 st.warning("Miktar pozitif olmalı.")
# #             else:
# #                 if hasattr(engine, "place_order"):
# #                     order_type = "market" if mkt else "limit"
# #                     # limit ise bir fiyat beklenebilir; sade tutuyoruz
# #                     engine.place_order(sel_symbol, side, float(q), order_type)
# #                     st.success(f"Emir gönderildi: {side} {q} {sel_symbol} ({order_type})")
# #                 else:
# #                     st.error("engine.place_order(...) bulunamadı.")
# #         except Exception as e:
# #             st.exception(e)
# #
# #     st.divider()
# #
# #     # --- emir/işlem geçmişi (varsa) ---
# #     orders = getattr(engine, "orders", None)
# #     if isinstance(orders, pd.DataFrame) and not orders.empty:
# #         st.markdown("#### Emirler")
# #         st.dataframe(orders.tail(200), width='stretch')
#
# # ui/tabs/paper_tab.py
#
# from __future__ import annotations
# import math
# from typing import Optional, Any, Dict
# import pandas as pd
# import streamlit as st
#
#
# # ===================== Basit Paper Engine (fallback) ===================== #
# class SimplePaperEngine:
#     """
#     Çok hafif bir paper engine.
#     - cash, realized_pnl, positions, orders tutar
#     - get_last_price / place_order sağlar
#     - son fiyat yoksa 100.0 varsayar (UI'dan güncelleyebilirsin)
#     """
#     def __init__(self, starting_cash: float = 100_000.0):
#         self.cash: float = float(starting_cash)
#         self.realized_pnl: float = 0.0
#         self.positions: Dict[str, Dict[str, float]] = {}  # {sym: {qty, avg_price}}
#         self._prices: Dict[str, float] = {}
#         self.orders: pd.DataFrame = pd.DataFrame(
#             columns=["ts", "symbol", "side", "qty", "price", "status", "realized_pnl"]
#         )
#
#     @property
#     def portfolio_value(self) -> float:
#         total = float(self.cash)
#         for sym, pos in self.positions.items():
#             px = self.get_last_price(sym)
#             if px is None or px != px:  # NaN
#                 px = pos.get("avg_price", 0.0)
#             total += float(pos.get("qty", 0.0)) * float(px)
#         return total
#
#     def set_price(self, symbol: str, price: float) -> None:
#         if symbol:
#             self._prices[symbol] = float(price)
#
#     def get_last_price(self, symbol: str) -> Optional[float]:
#         if not symbol:
#             return None
#         return self._prices.get(symbol, 100.0)
#
#     def place_order(self, symbol: str, side: str, qty: float, order_type: str = "market", price: Optional[float] = None):
#         side = side.lower()
#         if order_type != "market" and price is None:
#             raise ValueError("Limit/diğer emirlerde fiyat gerekli.")
#         px = float(self.get_last_price(symbol) if price is None else price)
#         q = float(qty)
#
#         realized = 0.0
#         pos = self.positions.get(symbol, {"qty": 0.0, "avg_price": 0.0})
#         cur_qty = float(pos["qty"])
#         avg = float(pos["avg_price"])
#
#         if side == "buy":
#             # yeni ağırlıklı ortalama
#             new_qty = cur_qty + q
#             new_avg = (cur_qty * avg + q * px) / new_qty if new_qty != 0 else 0.0
#             pos["qty"] = new_qty
#             pos["avg_price"] = new_avg
#             self.cash -= q * px
#
#         elif side == "sell":
#             sell_qty = min(q, cur_qty)  # kısa pozisyon yok; elindeki kadar sat
#             realized = (px - avg) * sell_qty
#             self.realized_pnl += realized
#             self.cash += q * px
#             pos["qty"] = max(0.0, cur_qty - q)
#             # pozisyon sıfırlandıysa avg'ı sıfırla
#             if pos["qty"] == 0:
#                 pos["avg_price"] = 0.0
#         else:
#             raise ValueError("side buy|sell olmalı")
#
#         # pozisyonu yaz
#         self.positions[symbol] = pos
#
#         # order kaydı
#         row = {
#             "ts": pd.Timestamp.utcnow(),
#             "symbol": symbol,
#             "side": side,
#             "qty": q,
#             "price": px,
#             "status": "filled",
#             "realized_pnl": realized,
#         }
#         self.orders = pd.concat([self.orders, pd.DataFrame([row])], ignore_index=True)
#
#
# # ========================== Yardımcı Fonksiyonlar ========================== #
# def _resolve_last_px(symbol: Optional[str], engine: Any, price_df: Optional[pd.DataFrame] = None) -> float:
#     """Motor/broker/df üzerinden son fiyatı bul. Bulamazsa NaN döndür."""
#     if not symbol:
#         return float("nan")
#
#     # 1) engine.get_last_price
#     if hasattr(engine, "get_last_price"):
#         try:
#             px = engine.get_last_price(symbol)
#             if px is not None:
#                 return float(px)
#         except Exception:
#             pass
#
#     # 2) engine.broker.get_last_price
#     br = getattr(engine, "broker", None)
#     if br is not None and hasattr(br, "get_last_price"):
#         try:
#             px = br.get_last_price(symbol)
#             if px is not None:
#                 return float(px)
#         except Exception:
#             pass
#
#     # 3) DataFrame son kapanış
#     if isinstance(price_df, pd.DataFrame) and len(price_df) > 0:
#         for col in ("close", "Close", "price", "last"):
#             if col in price_df.columns:
#                 try:
#                     return float(price_df[col].iloc[-1])
#                 except Exception:
#                     pass
#
#     return float("nan")
#
#
# def _positions_to_df(positions: Dict[str, Dict[str, Any]], engine: Any) -> pd.DataFrame:
#     if not positions:
#         return pd.DataFrame(columns=["symbol", "qty", "avg_price", "last", "unrealized_pnl"])
#     rows = []
#     for sym, pos in positions.items():
#         qty = float(pos.get("qty", pos.get("quantity", 0.0)))
#         avg_price = float(pos.get("avg_price", pos.get("average_price", 0.0)))
#         last = None
#         try:
#             last = float(engine.get_last_price(sym)) if hasattr(engine, "get_last_price") else None
#         except Exception:
#             last = None
#         if last is None or last != last:
#             last = avg_price
#         unreal = (last - avg_price) * qty
#         rows.append({
#             "symbol": sym,
#             "qty": qty,
#             "avg_price": avg_price,
#             "last": last,
#             "unrealized_pnl": unreal,
#         })
#     return pd.DataFrame(rows)
#
#
# # =============================== Ana Tab ================================= #
# def run(state):
#     # 1) Var olan motoru bul
#     engine = (
#         state.get("paper_engine")
#         or state.get("engine")
#         or st.session_state.get("paper_engine")
#         or st.session_state.get("engine")
#     )
#
#     # 2) Yoksa otomatik başlat (fallback)
#     if engine is None:
#         engine = SimplePaperEngine(starting_cash=100_000.0)
#         st.session_state["paper_engine"] = engine
#         state["paper_engine"] = engine
#         st.success("Paper motoru otomatik başlatıldı (SimplePaperEngine).")
#
#     st.subheader("Paper Trading")
#
#     # Semboller (varsa pozisyonlardan)
#     positions_dict = getattr(engine, "positions", {}) or {}
#     known_symbols = list(positions_dict.keys())
#
#     default_symbol = (
#         state.get("paper_symbol")
#         or state.get("symbol")
#         or (known_symbols[0] if known_symbols else None)
#         or getattr(engine, "symbol", None)
#     )
#
#     # Sembol seçimi
#     if known_symbols:
#         symbol = st.selectbox("Sembol", options=known_symbols, index=0 if default_symbol in known_symbols else 0)
#     else:
#         symbol = st.text_input("Sembol", value=default_symbol or "" ).strip() or None
#
#     # Dış veri (varsa)
#     bars_df = (
#         state.get("bars")
#         or state.get("price_df")
#         or getattr(engine, "bars", None)
#         or getattr(engine, "price_df", None)
#     )
#
#     # Son fiyat
#     last_px = _resolve_last_px(symbol, engine, bars_df)
#
#     # Fiyat bilgin yoksa kullanıcıdan set etme alanı
#     with st.expander("Fiyatı Güncelle (opsiyonel)"):
#         colp1, colp2 = st.columns([2, 1])
#         with colp1:
#             manual_px = st.text_input("Manuel Son Fiyat", value="" if (last_px != last_px or math.isnan(last_px)) else f"{last_px:.4f}")
#         with colp2:
#             if st.button("Fiyatı Kaydet") and symbol:
#                 try:
#                     pxv = float(manual_px)
#                     if hasattr(engine, "set_price"):
#                         engine.set_price(symbol, pxv)
#                     last_px = pxv
#                     st.success(f"{symbol} fiyatı {pxv:.4f} olarak kaydedildi.")
#                 except Exception as e:
#                     st.warning(f"Fiyat kaydedilemedi: {e}")
#
#     # ----------- metrikler ----------- #
#     c1, c2, c3, c4 = st.columns(4)
#     with c1:
#         st.metric("Total Value", f"${getattr(engine, 'portfolio_value', 0.0):,.2f}")
#     with c2:
#         st.metric("Cash", f"${getattr(engine, 'cash', 0.0):,.2f}")
#     with c3:
#         pnl = getattr(engine, "realized_pnl", 0.0)
#         st.metric("Realized PnL", f"${pnl:,.2f}")
#     with c4:
#         label = f"{(symbol or '-')} Last"
#         value = "-" if (last_px != last_px or math.isnan(last_px)) else f"{last_px:.4f}"
#         st.metric(label, value)
#
#     st.divider()
#
#     # ----------- pozisyonlar ----------- #
#     st.markdown("#### Pozisyonlar")
#     pos_df = _positions_to_df(positions_dict, engine)
#     st.dataframe(pos_df, width='stretch', hide_index=True)
#
#     st.divider()
#
#     # ----------- hızlı emir ----------- #
#     st.markdown("#### Hızlı Emir")
#     col_a, col_b, col_c, col_d, col_e = st.columns([2, 1, 1, 1, 1])
#     with col_a:
#         sel_symbol = st.text_input("Sembol (emir)", value=symbol or "")
#     with col_b:
#         side = st.selectbox("Yön", options=["buy", "sell"], index=0)
#     with col_c:
#         qty_str = st.text_input("Miktar", value="1")
#     with col_d:
#         mkt = st.checkbox("Market", value=True)
#     with col_e:
#         px_str = st.text_input("Fiyat (limit için)", value="")
#
#     place = st.button("Emri Gönder")
#     if place:
#         try:
#             q = float(qty_str)
#             if not sel_symbol:
#                 st.warning("Sembol gerekli.")
#             elif q <= 0:
#                 st.warning("Miktar pozitif olmalı.")
#             else:
#                 order_type = "market" if mkt else "limit"
#                 px = None
#                 if not mkt:
#                     if not px_str:

# ui/tabs/paper_tab.py
from __future__ import annotations
from typing import Any, Dict, Optional, List
import pandas as pd
import streamlit as st
from datetime import datetime
# Kendi motorunuz:
from core.execution.paper_engine import PaperTradingEngine


# ---------------------------- Yardımcılar ---------------------------- #
def _ensure_engine(state) -> PaperTradingEngine:
    """Var olan engine'i bulur; yoksa oluşturur ve state'e koyar."""
    engine = (
        state.get("paper_engine")
        or state.get("engine")
        or st.session_state.get("paper_engine")
        or st.session_state.get("engine")
    )
    if not isinstance(engine, PaperTradingEngine):
        engine = PaperTradingEngine(initial_capital=100_000.0)
        st.session_state["paper_engine"] = engine
        state["paper_engine"] = engine
        st.success("Paper motoru otomatik başlatıldı (PaperTradingEngine).")
    return engine


def _get_last_price(engine: PaperTradingEngine, symbol: Optional[str]) -> float:
    if not symbol:
        return float("nan")
    px = engine.get_current_price(symbol)
    return float(px) if px is not None else float("nan")


def _append_manual_price(engine: PaperTradingEngine, symbol: str, price: float) -> None:
    """Manuel fiyatı engine.market_data'ya zaman damgalı olarak ekler."""
    if not symbol:
        return
    series = engine.market_data.get(symbol)
    now = pd.Timestamp.utcnow()
    if isinstance(series, pd.Series) and not series.empty:
        # Var olan seriye yeni noktayı ekle
        new_point = pd.Series([float(price)], index=[now])
        engine.market_data[symbol] = pd.concat([series, new_point])
    else:
        engine.market_data[symbol] = pd.Series([float(price)], index=[now])


def _positions_df(engine: PaperTradingEngine) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for sym, qty in (engine.positions or {}).items():
        try:
            last = engine.get_current_price(sym)
        except Exception:
            last = None
        market_value = (last or 0.0) * float(qty)
        rows.append({
            "symbol": sym,
            "quantity": float(qty),
            "last": float(last) if last is not None else None,
            "market_value": market_value,
        })
    df = pd.DataFrame(rows, columns=["symbol", "quantity", "last", "market_value"])
    return df


def _orders_df(engine: PaperTradingEngine) -> pd.DataFrame:
    if not getattr(engine, "order_history", None):
        return pd.DataFrame(columns=["created_at", "filled_at", "symbol", "side", "quantity", "order_type", "price", "filled_price", "status"])
    rows = []
    for o in engine.order_history:
        rows.append({
            "created_at": o.created_at,
            "filled_at": o.filled_at,
            "symbol": o.symbol,
            "side": o.side,
            "quantity": o.quantity,
            "order_type": o.order_type,
            "price": o.price,
            "filled_price": o.filled_price,
            "status": o.status,
        })
    return pd.DataFrame(rows)


# ------------------------------ Ana Tab ------------------------------ #
def run(state):
    st.subheader("📊 Paper Trading")

    # 1) Engine hazırla
    engine = _ensure_engine(state)

    # 2) Bilgileri güncel tut
    try:
        engine.update_portfolio_value()
    except Exception:
        pass

    # 3) Sembol seçimi
    positions = engine.positions or {}
    known_symbols = list(positions.keys())
    default_symbol = state.get("paper_symbol") or (known_symbols[0] if known_symbols else "")
    if known_symbols:
        symbol = st.selectbox("Sembol", known_symbols, index=known_symbols.index(default_symbol) if default_symbol in known_symbols else 0)
    else:
        symbol = st.text_input("Sembol", value=default_symbol).strip()

    # 4) Son fiyat
    last_px = _get_last_price(engine, symbol if symbol else None)

    # 5) Manuel fiyat ekleme
    with st.expander("Fiyatı Güncelle (opsiyonel)"):
        colp1, colp2 = st.columns([2, 1])
        with colp1:
            manual_px_str = st.text_input(
                "Manuel Son Fiyat",
                value=("" if (pd.isna(last_px)) else f"{last_px:.6f}")
            )
        with colp2:
            if st.button("Fiyatı Kaydet") and symbol:
                try:
                    manual_px = float(manual_px_str)
                    _append_manual_price(engine, symbol, manual_px)
                    engine.update_portfolio_value()
                    last_px = manual_px
                    st.success(f"{symbol} fiyatı {manual_px:.6f} olarak kaydedildi.")
                except ValueError:
                    st.warning("Geçerli bir sayı girin.")

    # 6) Metrikler
    try:
        summary = engine.get_portfolio_summary()
    except Exception:
        # Geriye uyumlu: elde edilemezse portföyü yaklaşıkla
        summary = {
            "total_value": getattr(engine, "portfolio_value", 0.0),
            "cash": getattr(engine, "cash", 0.0),
            "positions": positions,
            "unrealized_pnl": {},
            "total_return": ((getattr(engine, "portfolio_value", 0.0) / getattr(engine, "initial_capital", 1.0) - 1.0) * 100.0)
        }

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Value", f"${summary['total_value']:,.2f}")
    with c2:
        st.metric("Cash", f"${summary['cash']:,.2f}")
    with c3:
        st.metric("Return", f"{summary.get('total_return', 0.0):.2f}%")
    with c4:
        st.metric(f"{symbol or '-'} Last", "-" if pd.isna(last_px) else f"{last_px:.6f}")

    st.divider()

    # 7) Pozisyonlar
    st.markdown("#### 📦 Pozisyonlar")
    pos_df = _positions_df(engine)
    if not pos_df.empty:
        st.dataframe(pos_df, width='stretch', hide_index=True)
    else:
        st.info("Pozisyon bulunmuyor.")

    st.divider()

    # 8) Hızlı Emir
    st.markdown("#### ⚡ Hızlı Emir")
    col_a, col_b, col_c, col_d, col_e = st.columns([2, 1, 1, 1, 1])
    with col_a:
        sel_symbol = st.text_input("Sembol (emir)", value=(symbol or ""))
    with col_b:
        side = st.selectbox("Yön", options=["buy", "sell"], index=0)
    with col_c:
        qty_str = st.text_input("Miktar", value="1")
    with col_d:
        is_market = st.checkbox("Market", value=True)
    with col_e:
        px_str = st.text_input("Fiyat (limit için)", value="", disabled=is_market)

    # --- Emri Gönder ---
    if st.button("Emri Gönder"):
        try:
            q = float(qty_str)
            if not sel_symbol:
                st.warning("Sembol gerekli.")
            elif q <= 0:
                st.warning("Miktar pozitif olmalı.")
            elif is_market:
                # MARKET order
                engine.place_order(sel_symbol, side, q, order_type="market")
                engine.update_portfolio_value()
                st.success(f"Market emir gönderildi: {side.upper()} {q} {sel_symbol}")
            else:
                # LIMIT order
                if not px_str.strip():
                    st.warning("Limit emir için fiyat girin.")
                else:
                    px_val = float(px_str)
                    engine.place_order(sel_symbol, side, q, order_type="limit", price=px_val)
                    engine.update_portfolio_value()
                    st.success(f"Limit emir gönderildi: {side.upper()} {q} {sel_symbol} @ {px_val}")
        except ValueError:
            st.warning("Miktar/Fiyat sayı olmalı.")
        except Exception as e:
            st.error(f"Emir hatası: {e}")

    st.divider()

    # 9) Emirler
    st.markdown("#### 📋 Emir Geçmişi")
    odf = _orders_df(engine)
    if not odf.empty:
        st.dataframe(odf.tail(200), width='stretch')
    else:
        st.info("Henüz emir bulunmuyor.")

    # 10) Manuel Portföy Güncelle
    if st.button("🔄 Portföyü Güncelle"):
        try:
            engine.update_portfolio_value()
            st.success(f"Güncellendi: {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            st.error(f"Güncelleme hatası: {e}")




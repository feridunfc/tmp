"""
ALGO5 Execution • gateways/paper.py

Purpose
-------
Deterministic paper gateway:
- GTC emir defteri
- 1-bar delay: submit'ten sonra ilk on_bar'da OPEN'dan fill
- Bracket (TP/SL) OCO niyetiyle child'ları kitapta bekletir
- Trailing stop: long için peak-high, short için trough-low izleme

Public API
----------
- PaperGateway.on_bar(o,h,l,c) -> List[Fill]
- PaperGateway.submit(order)   -> str (order_id)
- PaperGateway.submit_bracket(bracket) -> str
- PaperGateway.submit_trailing(trailing) -> str
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..models import (
    Order,
    Fill,
    BracketOrder,
    TrailingStopOrder,
    Side,
    OrderType,
    TIF,
)
from ..matcher import match_order_on_bar


@dataclass
class PaperGateway:
    # Çalışan GTC emirler (book)
    orders: Dict[str, Order] = field(default_factory=dict)
    # Gerçekleşen fill’ler
    fills: List[Fill] = field(default_factory=list)
    # Parent fill olduğunda çocukları sahnelemek için bekleyen bracket’lar
    bracket_orders: Dict[str, BracketOrder] = field(default_factory=dict)
    # İzlenen trailing stop emirleri
    trailing_orders: Dict[str, TrailingStopOrder] = field(default_factory=dict)
    # Son bar
    _last_bar: Optional[Tuple[float, float, float, float]] = None
    # Order id sayacı
    _order_counter: int = 0

    def on_bar(self, o: float, h: float, l: float, c: float) -> List[Fill]:
        """Yeni bar’ı işler ve pending GTC emirleri eşler."""
        self._last_bar = (o, h, l, c)
        new_fills: List[Fill] = []

        # Çalışan emirler (snapshot ile iterate)
        for oid in list(self.orders.keys()):
            order = self.orders[oid]
            res = match_order_on_bar(order, o, h, l, c)

            if res.fill:
                new_fills.append(res.fill)
                self.fills.append(res.fill)
                # parent/normal fark etmeksizin dolduysa defterden çıkart
                self.orders.pop(oid, None)

                # Parent fill ise bracket çocuklarını kitapta sahnele
                if oid in self.bracket_orders:
                    br = self.bracket_orders.pop(oid)
                    if br.tp_order:
                        self.orders[f"{oid}_TP"] = br.tp_order
                    if br.sl_order:
                        self.orders[f"{oid}_SL"] = br.sl_order

            elif res.remaining_order is not None:
                # dokunmadı → aynı emir çalışmaya devam
                self.orders[oid] = res.remaining_order

        # Trailing güncelleme ve olası exit
        self._update_trailing(o, h, l, c)

        return new_fills

    def submit(self, order: Order) -> str:
        """Yeni emir alır. Bar varsa 'hemen' değerlendirir; dolmazsa GTC defterine girer."""
        oid = f"order_{self._order_counter}"
        self._order_counter += 1

        if self._last_bar:
            o, h, l, c = self._last_bar
            res = match_order_on_bar(order, o, h, l, c)
            if res.fill:
                self.fills.append(res.fill)
                # IOC/FOK/DAY doldurulduysa kitap yazmaya gerek yok
                if order.tif in (TIF.IOC, TIF.FOK, TIF.DAY):
                    return oid
            elif res.remaining_order is not None and order.tif == TIF.GTC:
                self.orders[oid] = res.remaining_order
        else:
            # Bar gelmediyse sadece GTC kitapta bekler
            if order.tif == TIF.GTC:
                self.orders[oid] = order

        return oid

    def submit_bracket(self, bracket: BracketOrder) -> str:
        """Parent’ı submit eder; parent anında fill olursa çocukları hemen sahneler, aksi halde bekletir."""
        pid = self.submit(bracket.parent)

        if pid in self.orders:
            # Parent henüz working (GTC) → fill olunca on_bar içinde çocuklar eklenecek
            self.bracket_orders[pid] = bracket
        else:
            # Parent anında doldu → çocukları hemen kitapta sahnele
            if bracket.tp_order:
                self.orders[f"{pid}_TP"] = bracket.tp_order
            if bracket.sl_order:
                self.orders[f"{pid}_SL"] = bracket.sl_order

        return pid

    def submit_trailing(self, trailing: TrailingStopOrder) -> str:
        """
        Trailing stop emrini submit eder ve izlemeye alır.
        Not: stop_price başlangıçta None olabilir; matcher bunu GTC working sayar.
        """
        oid = f"order_{self._order_counter}"
        self._order_counter += 1

        # Başlangıç referansı (son bar varsa)
        if self._last_bar:
            o, h, l, c = self._last_bar
            if trailing.side == Side.BUY:
                trailing.peak_price = max(trailing.peak_price or h, h)
            else:
                trailing.trough_price = min(trailing.trough_price or l, l)

        # GTC kitapta yer tutsun ki _update_trailing takip etsin
        self.orders[oid] = trailing

        # Geçerli trailing yapılarını izliyoruz
        if trailing.is_valid():
            self.trailing_orders[oid] = trailing

        return oid

    def _update_trailing(self, o: float, h: float, l: float, c: float) -> None:
        """
        Trailing için peak/trough ve tetik kontrolü (synth market exit).
        Ralli barında yeni zirve oluşursa sadece günceller, tetik kontrolü yapmaz;
        geri çekilmede trigger’a değerse exit üretir.
        """
        for oid, tr in list(self.trailing_orders.items()):
            # Artık working değilse izlemeyi bırak
            if oid not in self.orders:
                self.trailing_orders.pop(oid, None)
                continue

            if tr.side == Side.BUY:
                # Önce önceki zirveyi al
                prev_peak = tr.peak_price if tr.peak_price is not None else h
                # Yeni zirve yaptıysa sadece güncelle, bu barda tetikleme yapma
                if tr.peak_price is None or h > tr.peak_price:
                    tr.peak_price = h
                    continue

                # Trigger’ı önceki zirveden türet
                trigger = (
                    prev_peak - tr.trail_amount
                    if tr.trail_amount > 0
                    else prev_peak * (1.0 - tr.trail_pct / 100.0)
                )
                if l <= trigger:
                    # Çıkış için synth market emri
                    exit_order = Order(
                        side=Side.SELL, qty=tr.qty, type=OrderType.MARKET, tif=TIF.GTC
                    )
                    res = match_order_on_bar(exit_order, o, h, l, c)
                    if res.fill:
                        self.fills.append(res.fill)
                        self.orders.pop(oid, None)
                        self.trailing_orders.pop(oid, None)

            else:  # Short (SELL)
                prev_trough = tr.trough_price if tr.trough_price is not None else l
                # Yeni dip yaptıysa sadece güncelle, tetikleme yapma
                if tr.trough_price is None or l < tr.trough_price:
                    tr.trough_price = l
                    continue

                trigger = (
                    prev_trough + tr.trail_amount
                    if tr.trail_amount > 0
                    else prev_trough * (1.0 + tr.trail_pct / 100.0)
                )
                if h >= trigger:
                    exit_order = Order(
                        side=Side.BUY, qty=tr.qty, type=OrderType.MARKET, tif=TIF.GTC
                    )
                    res = match_order_on_bar(exit_order, o, h, l, c)
                    if res.fill:
                        self.fills.append(res.fill)
                        self.orders.pop(oid, None)
                        self.trailing_orders.pop(oid, None)

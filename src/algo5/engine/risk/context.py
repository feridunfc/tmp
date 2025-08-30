from dataclasses import dataclass

@dataclass
class RiskContext:
    capital: float
    position_qty: float
    last_price: float

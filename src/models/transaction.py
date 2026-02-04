from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

@dataclass(frozen=True)
class Transaction:
    kind: Literal['buy', 'sell']
    ticker: str
    quantity: float
    price: float
    gross_amount: float
    cash_after: float
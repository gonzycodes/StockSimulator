from __future__ import annotations

import logging
from typing import Dict

from src.portfolio import Portfolio

log = logging.getLogger(__name__)


def format_portfolio_output(portfolio: Portfolio, price_map: Dict[str, float]) -> str:
    """
    Format portfolio data into readable string.

    Args:
        portfolio: Portfolio object containing cash and holdings
        price_map: Mapping from ticker to latest price. 

    Returns:
        Formatted string with cash, holdings and total value.
    """
    lines: list[str] = []
    lines.append(f"Cash: {portfolio.cash:.2f}")
    lines.append("")
    
    if not portfolio.holdings:
        lines.append("No holdings")
        lines.append(f"Total value: {portfolio.cash:.2f}")
        return "\n".join(lines)
    
    lines.append("Holdings:")
    
    # Start total with cash balance
    total = portfolio.cash
    
    # Iterate through holdings and calculate value per ticker
    for ticker, qty in portfolio.holdings.items():
        
        # If price is missing, log warning and skip from total calculation
        if ticker not in price_map:
            log.warning("Price unavailable for %s", ticker)
            lines.append(f"- {ticker} qty={qty}  price unavailable")
            continue
            
            
        price = float(price_map[ticker])
        value = qty * price
        total += value
        lines.append(f"- {ticker}  qty={qty}  price={price:.2f}  value={value:.2f}")
        
    lines.append("")
    lines.append(f"Total value: {total:.2f}")
    return "\n".join(lines)
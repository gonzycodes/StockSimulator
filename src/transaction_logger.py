from src.logger import get_logger
from src.config import DATA_DIR
from datetime import datetime
import json
from src.models.transaction import Transaction

log = get_logger(__name__)

TRANSACTIONS_FILE = DATA_DIR / "transactions.json"  # från config


def log_transaction(tx: Transaction) -> bool:
    """Loggar en genomförd transaktion till JSON-historik (append)."""
    record = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "side": tx.kind.upper(),
        "ticker": tx.ticker,
        "quantity": tx.quantity,
        "price": tx.price,
        "total": tx.gross_amount,
        "cash_after": tx.cash_after,
    }

    # Ladda befintlig historik (eller börja tom)
    existing = []
    if TRANSACTIONS_FILE.is_file():
        try:
            with TRANSACTIONS_FILE.open("r", encoding="utf-8") as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            log.warning("transactions.json is corrupt – restarting with empty history")
            existing = []
        except OSError as e:
            log.error("Couldn't read transaction history: %s", e)
            existing = []

    existing.append(record)

    try:
        TRANSACTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with TRANSACTIONS_FILE.open("w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
        
        log.info(
            "Transaction logged to history: %s %s × %.2f @ %.2f (cash after: %.2f)",
            record["side"], record["ticker"], record["quantity"], record["price"], record["cash_after"]
        )
        return True
    
    except OSError as e:
        log.error("Failed to save transactions history: %s", e)
        print("Warning: Couldn't save  transactions historiy – check writing rights.")
        return False
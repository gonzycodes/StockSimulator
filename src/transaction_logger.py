from src.logger import get_logger
from src.config import DATA_DIR
from datetime import datetime, timezone
import json
from src.models.transaction import Transaction

log = get_logger(__name__)

TRANSACTIONS_FILE = DATA_DIR / "transactions.json"  # from config


def log_transaction(tx: Transaction) -> bool:
    """Logs a completed transaction to the JSON history (append)."""
    record = {
        "timestamp": (tx.timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
        "side": tx.kind.upper(),
        "ticker": tx.ticker,
        "quantity": tx.quantity,
        "price": tx.price,
        "total": tx.gross_amount,
        "cash_after": tx.cash_after,
    }

    # Load history or from scratch if none
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
            "Transaction logged: %s %s qty=%.2f price=%.2f total=%.2f ts=%s cash_after=%.2f",
            record["side"],
            record["ticker"],
            float(record["quantity"]),
            float(record["price"]),
            float(record["total"]),
            record["timestamp"],
            float(record["cash_after"]),
        )
        return True
    
    except OSError as e:
        log.error("Failed to save transactions history: %s", e)
        print("Warning: Couldn't save  transactions historiy – check writing rights.")
        return False
    

def utc_timestamp_iso_z() -> str:
    """Return current UTC timestamp as ISO 8601 with Z suffix."""
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

# src/main.py

"""
Application entry point for StockSimulator.

This module initializes logging, logs app start/exit, and provides a main()
function that returns a process exit code.
"""

from src.logger import init_logging_from_env, get_logger

log = get_logger(__name__)


def main() -> int:
    """
    Run the application and return an exit code.

    Returns:
        0 on success, 1 on unhandled errors.
    """
    init_logging_from_env()  # INFO by default; configurable via LOG_LEVEL
    log.info("App start")

    try:
        # ... application code here ...
        return 0
    except Exception:
        log.exception("Unhandled exception")
        return 1
    finally:
        log.info("App exit")


if __name__ == "__main__":
    raise SystemExit(main())


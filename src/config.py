"""
Configuration module for StockSimulator
Centralizes the path definitions using pathlib to ensure cross platform compatibility.
"""
import os
from datetime import datetime, time
from pathlib import Path

#   Base directory of the project
#   resolve the directory of this file (src/config.py)
#  .parent gives us 'src/'
#  .parent.parent gives us the root directory of the project 'StockSimulator/'
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define standard paths
_env_data_dir = os.getenv("STOCKSIM_DATA_DIR")
DATA_DIR = (Path(_env_data_dir).expanduser() if _env_data_dir else (PROJECT_ROOT / "data")).resolve()
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"
SNAPSHOTS_FILE = DATA_DIR / "snapshots.csv"
TRANSACTIONS_FILE = DATA_DIR / "transactions.json"
MOCK_PRICES_FILE = DATA_DIR / "mock_prices.json"
USE_MOCK_DATA = False  # Set to true for demo/offline mode

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# for debugging purposes only
if __name__ == "__main__":
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Source Directory: {SRC_DIR}")
    print(f"Tests Directory: {TESTS_DIR}")

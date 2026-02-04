"""
Configuration module for StockSimulator
Centralizes the path definitions using pathlib to ensure cross platform compatibility.
"""

from pathlib import Path

#   Base directory of the project
#  resolve the directory of this file (src/config.py)
#  .parent gives us 'src/'
#  .parent.parent gives us the root directory of the project 'StockSimulator/'
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define standard paths
DATA_DIR = PROJECT_ROOT / "data"
SRC_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"
SNAPSHOTS_FILE = DATA_DIR / "snapshots.csv"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

# for debugging purposes only
if __name__ == "__main__":
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"Source Directory: {SRC_DIR}")
    print(f"Tests Directory: {TESTS_DIR}")
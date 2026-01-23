# StockSimulator
StockSimulator is a Python-based trading simulator where users receive a virtual budget (e.g., 100,000 SEK) and can buy/sell stocks or cryptocurrencies using real market data. The project is designed to demonstrate object-oriented programming, API integration, data analysis, and visualization.








``` ## Map Structure
stocksimulator/
│
├── data/                 # Stores portfolio files (JSON) and logs
├── src/
│   ├── __init__.py
│   ├── main.py           # Entry point (CLI Menu)
│   ├── market.py         # Fetches market data from Yahoo Finance (API)
│   ├── portfolio.py      # Core logic for cash, holdings, and trades
│   ├── storage.py        # Handles data persistence (Save/Load JSON)
│   ├── analysis.py       # Analytics using Pandas (Calculates Profit/Loss)
│   └── utils.py          # Utility functions (Input validation, etc.)
├── tests/
│   ├── test_portfolio.py
│   ├── test_market.py
│   └── ...
├── requirements.txt      # List of dependencies
├── README.md             # Project documentation
└── .github/workflows/python-app.yml  # CI/CD configuration
```

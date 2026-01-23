# StockSimulator
StockSimulator is a Python-based trading simulator where users receive a virtual budget (e.g., 100,000 SEK) and can buy/sell stocks or cryptocurrencies using real market data. The project is designed to demonstrate object-oriented programming, API integration, data analysis, and visualization.



``` Map Structure
tradesim/
│
├── data/                 # Här sparas portfölj-filer (json) och loggar
├── src/
│   ├── __init__.py
│   ├── main.py           # Startpunkten (CLI-menyn)
│   ├── market.py         # Hämtar data från Yahoo Finance (API)
│   ├── portfolio.py      # Klasser för Pengar, Innehav, Köp/Sälj-logik
│   ├── storage.py        # Sparar/Laddar data till JSON
│   ├── analysis.py       # Pandas-analyser (Räknar ut vinst/förlust)
│   └── utils.py          # Hjälpfunktioner (Validering av input etc.)
├── tests/
│   ├── test_portfolio.py
│   ├── test_market.py
│   └── ...
├── requirements.txt
├── README.md
└── .github/workflows/python-app.yml  # CI/CD
```

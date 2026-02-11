<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->

<a id="readme-top"></a>

<!--
*** Thanks for checking out the Best-README-Template. If you have a suggestion
*** that would make this better, please fork the repo and create a pull request
*** or simply open an issue with the tag "enhancement".
*** Don't forget to give the project a star!
*** Thanks again! Now go create something AMAZING! :D
-->

<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/othneildrew/Best-README-Template">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
  </a>

  <h3 align="center">Stock Simulator</h3>

  <p align="center">
    Probably the second best stock-trading simulator out there!
    <br />
    <a href="https://github.com/othneildrew/Best-README-Template"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/othneildrew/Best-README-Template">View Demo</a>
    &middot;
    <a href="https://github.com/othneildrew/Best-README-Template/issues/new?labels=bug&template=bug-report---.md">Report Bug</a>
    &middot;
    <a href="https://github.com/othneildrew/Best-README-Template/issues/new?labels=enhancement&template=feature-request---.md">Request Feature</a>
  </p>
</div>

<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>

<!-- ABOUT THE PROJECT -->

## About The Project


[![Product Name Screen Shot][product-screenshot]](https://example.com)

StockSimulator is a Python-based trading simulator where users receive a virtual budget (e.g., 100,000 SEK) and can buy/sell stocks or cryptocurrencies using real market data. The project is designed to demonstrate object-oriented programming, API integration, data analysis, and visualization.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Built With

This section should list any major frameworks/libraries used to bootstrap your project. Leave any add-ons/plugins for the acknowledgements section. Here are a few examples.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- GETTING STARTED -->

## Project Structure

```bash
StockSimulator/
├── data/                           # Local runtime data + optional helper modules
│   └── yfinance_fetcher.py         # Legacy/alt Yahoo Finance fetch helper (used in tests)
│
├── src/                            # Application source code
│   ├── main.py                     # Entry point: menu + safe interactive loop + routes args to CLI
│   ├── cli.py                      # Argparse CLI commands (quote/sell) + portfolio JSON IO helpers
│   ├── validators.py               # Central input validation logic (tickers/amounts)
│   ├── data_fetcher.py             # Market data layer (yfinance) + Quote model + QuoteFetchError codes
│   ├── portfolio.py                # Portfolio domain model (cash/holdings + buy/sell + total_value)
│   ├── transaction_manager.py      # TransactionManager + domain exceptions + Transaction result model
│   ├── errors.py                   # Controlled app error types (ValidationError/FileError/DataFetchError)
│   ├── logger.py                   # Central logging setup (console + rotating file) + env initializer
│   └── config.py                   # Centralized paths (PROJECT_ROOT/DATA_DIR/SRC_DIR/TESTS_DIR)
│
├── tests/                          # Automated tests (pytest)
│   ├── conftest.py                 # Pytest config: adds repo root to sys.path for `from src...`
│   ├── test_logger.py              # Tests logging init + idempotency + log file creation
│   ├── test_portfolio.py           # Tests Portfolio behaviors (cash/holdings operations)
│   ├── test_transaction_manager.py # Tests TransactionManager + domain validation/exceptions
│   ├── test_market_data.py         # Tests yfinance fetching + fetch_latest_quote error codes
│   └── test_cli_quote.py           # CLI quote command tests (output/behavior)
│
├── requirements.txt                # Python dependencies (pip install -r requirements.txt)
└── README.md                       # Project documentation
```
## Core Classes

- **Portfolio** (src/portfolio.py)  
  Represents the portfolio state including cash balance and holdings.

- **TransactionManager** (src/transaction_manager.py)  
  Handles buy and sell operations, validation, and transaction side effects.

- **SnapshotStore** (src/snapshot_store.py)  
  Persists portfolio snapshots after each trade.


## Getting Started

This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Installation


1. **Clone the Repo**

   ```sh
   git clone <url>
   cd <project_map>
   ```

2. **Create virtual environment**
   Windows:

   ```sh
   python -m venv .venv
   source .venv\Scripts\activate
   ```

   MacOS/Linux:

   ```sh
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   When venv is activated you will see (venv) in the prompt.

3. **Install dependencies**
   ```sh
   pip install -r requirements.txt
   ```

### Common commands

Run the web based mode with graph
```bash
start index.html
python api_server.py
```


Run the app (menu):

```bash
python -m src.main
```

Run a CLI command:

```bash
python -m src.main quote AAPL
python -m src.main buy AAPL 2
```

Run tests:
Run a CLI command:

```bash
pytest -q
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- USAGE EXAMPLES -->

## Usage

The app can run in three modes:

1. Interactive mode (menu + safe REPL loop)
2. CLI mode (single command via argparse)
3. Web based mode with graph

### Interactive mode (recommended)

From the project root:

```bash
python -m src.main
```

Inside the simulation:

- `help` or `?` shows available commands
- empty input does nothing (new prompt)
- unknown commands show a hint ("Type 'help' ...")

Example commands:

- `quote AAPL`
- `buy AAPL 5`
- `sell AAPL 2`
- `portfolio`
- `exit`

### CLI mode (single command)

You can run CLI commands either via the main entrypoint (recommended):

```bash
python -m src.main quote AAPL
python -m src.main buy AAPL 5
python -m src.main sell AAPL 2
```

Or directly via the CLI module:

```bash
python -m src.cli quote AAPL
python -m src.cli sell AAPL 2
python -m src.cli save
python -m src.cli load
```

Optional log level:

```bash
python -m src.main --log-level DEBUG quote AAPL
```

### Portfolio command

Show current portfolio status including cash, holdings, and total value.

```bash
python -m src.cli portfolio
```

<!-- ANALYTICS -->

### Analytics (Profit & Loss)

The analytics module calculates Profit/Loss (P/L) using a simple **average cost model**.

- **Realized P/L**: profit or loss from sold positions  
- **Unrealized P/L**: (latest price − average cost) × remaining quantity  
- **Total P/L**: realized + unrealized  

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- TESTS -->

## Tests

The project includes automated tests using **PyTest**.

### Running the tests

From the project root (`StockSimulator/`), with your virtual environment active:

```bash
pytest
```

or with more detailed output:

```bash
pytest -v
```
run a specific file:

```bash
pytest tests/test_transaction_manager.py
```

### Verification

The installation and run instructions have been tested on a fresh installation
using a clean virtual environment.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ERROR HANDLING -->

## Error Handling

The interactive simulation loop is designed to be stable and never crash on expected errors:

- **Input/validation errors** are caught and shown as a friendly message.
- **File errors** (e.g. unreadable or unwritable portfolio JSON) are caught and shown as a friendly message.
- **Market/API errors** when fetching quotes are caught and shown as a friendly message.
- For **unexpected exceptions**, the app logs a full stacktrace (ERROR) and prints:
  `Unexpected error occurred.`

### Transaction history

All buy and sell history saves automatically in  
`data/transactions.json` (JSON-list with append).

Example:

```json
[
  {
    "timestamp": "2026-02-03T13:45:12Z",
    "side": "BUY",
    "ticker": "ERIC-B.ST",
    "quantity": 20.0,
    "price": 95.0,
    "total": 1900.0,
    "cash_after": 8100.0
  }
]
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Snapshots
After each successful trade (buy/sell), a snapshot is appended to `data/snapshots.csv`.

## Continuous Integration (GitHub Actions)

This project uses GitHub Actions for Continuous Integration.

On every push and pull request, an automated pipeline is executed that:

- sets up Python
- installs dependencies from requirements.txt
- runs the full pytest test suite

A pull request can only be merged when the CI pipeline passes successfully.

The workflow definition can be found here:

.github/workflows/python-tests.yml

This ensures that the project remains stable and that all tests pass before changes are merged.



<!-- ROADMAP -->

## Roadmap

TBA

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- WHO DID WHAT -->
## Contributions (Who did what)

Updated continuously. Primary sources are Trello cards (TR-xxx) and pull request history.

**Nahuel**

- TR-204: Cache and mock data fallback when market API fails  
  Modules: src/data_fetcher.py, src/config.py, data/mock_prices.json, related tests
- TR-242: Portfolio snapshots saved after each trade  
  Modules: src/snapshot_store.py, integration with TransactionManager, snapshot CSV persistence
- TR-253: Pytest JSON save and load roundtrip for portfolio persistence  
  Modules: portfolio save/load logic, tests using tmp_path
- TR-234: CLI command `portfolio` showing cash, holdings, and total value  
  Modules: src/cli.py, portfolio formatting and total value calculation
- TR-212: Core Portfolio class (cash, holdings, total_value)  
  Modules: src/portfolio.py
- TR-251: Pytest coverage for buy behavior (cash decreases, holdings increase)  
  Modules: tests/test_transaction_manager.py
- TR-263: README test instructions and CI/CD documentation  
  Documentation: README sections for pytest usage and GitHub Actions CI pipeline

**Nicklas (Scrum Master)**
- `src/transactions.py` — `TransactionManager` (buy/sell flow) *(TR-213, PR #29)*
- `src/cli.py` — robust error handling + `quote <TICKER>` *(TR-236, TR-231)*
- `src/portfolio.py` — save portfolio to JSON *(TR-221)*
- `src/reporting.py` — “today’s trading” report (summary, trades, P/L) *(TR-244)*
- `src/logger.py` — logging setup (console + file, trade logging) *(TR-104)*
- `tests/` — test: cannot sell more than holdings *(TR-252)*
- Fixes: timezone-aware UTC timestamps *(PR #28)*; prevent pytest writing to repo `data/` *(PR #37)*

**David**

**Anton**

**Alex**
- TR-102 venv + requirements.txt (yfinance,  pytest)
  README.md, requirements.txt
  - TR-201 Data Fetcher: fetch current price for ticker via yfinance
  data/ __init__.py, yfinance_fetcher.py
  tests/ test_market_data.py
  pytest.ini
  - TR-202 Data Fetcher: handle errors (invalid ticker, network error) + clear error messages
  src/data_fetcher.py
  tests/test_market_data.py
- TR-203 Exchange times (datetime): Blocks if the market is closed (different depending on the market)
  src/data_fetcher.py
  tests/test_transaction_manager.py
  - TR-222 Robust loading of portfolio from JSON + autosave after every buy/sell
  src/portfolio.py
  tests/test_transaction_manager
  - TR-223 Added transactions logging with failsafe
  src/models/transaction.py
  src/cli.py, transaction_logger.py, transaction_manager.py
  tests/test_portfolio.py, test_transaction_logger.py, test_transaction_manager.py
- TR-243 TradingView Charts: Real-time visualization of portfolio with interactive chart graph
  css/styles.css
  js/app.js
  tests/stock_sim_chart.py, test_transaction_logger.py, test_transaction_manager.py
  api_server.py
  index.html

    
<!-- CONTRIBUTING -->

## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- LICENSE -->

## License

TBA

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTACT -->

## Contact

TBA

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- ACKNOWLEDGMENTS -->

## Acknowledgments

Use this space to list resources you find helpful and would like to give credit to. I've included a few of my favorites to kick things off!

- [Choose an Open Source License](https://choosealicense.com)
- [GitHub Emoji Cheat Sheet](https://www.webpagefx.com/tools/emoji-cheat-sheet)
- [Malven's Flexbox Cheatsheet](https://flexbox.malven.co/)
- [Malven's Grid Cheatsheet](https://grid.malven.co/)
- [Img Shields](https://shields.io)
- [GitHub Pages](https://pages.github.com)
- [Font Awesome](https://fontawesome.com)
- [React Icons](https://react-icons.github.io/react-icons/search)

<p align="right">(<a href="#readme-top">back to top</a>)</p>




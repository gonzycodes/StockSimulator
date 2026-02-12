import json
from pathlib import Path

from src.data_fetcher import load_mock_prices


def test_load_mock_prices_reads_json(tmp_path: Path):
    p = tmp_path / "mock_prices.json"
    p.write_text(
        json.dumps({"AAPL": {"price": 100.0, "updated_at": "2026-01-30T10:00:00"}})
    )

    data = load_mock_prices(p)
    assert data["AAPL"]["price"] == 100.0

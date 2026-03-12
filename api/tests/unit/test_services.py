import pytest
from app.services_prices import _parse_daily_adjusted

SAMPLE_PAYLOAD = {
    "Time Series (Daily Adjusted)": {
        "2024-01-02": {
            "1. open": "180.00",
            "2. high": "185.00",
            "3. low": "179.00",
            "4. close": "182.00",
            "5. adjusted close": "182.00",
            "6. volume": "1000000.0",
        }
    }
}


def test_parse_basic():
    rows = _parse_daily_adjusted("AAPL", SAMPLE_PAYLOAD)
    assert len(rows) == 1
    row = rows[0]
    assert row.symbol == "AAPL"
    assert float(row.close) == pytest.approx(182.00)
    assert int(row.volume) == 1000000


def test_parse_sorted_ascending():
    payload = {
        "Time Series (Daily Adjusted)": {
            "2024-01-03": {
                "1. open": "183.00",
                "2. high": "188.00",
                "3. low": "182.00",
                "4. close": "186.00",
                "5. adjusted close": "186.00",
                "6. volume": "2000000.0",
            },
            "2024-01-02": {
                "1. open": "180.00",
                "2. high": "185.00",
                "3. low": "179.00",
                "4. close": "182.00",
                "5. adjusted close": "182.00",
                "6. volume": "1000000.0",
            },
        }
    }
    rows = _parse_daily_adjusted("AAPL", payload)
    assert len(rows) == 2
    assert str(rows[0].date) <= str(rows[1].date)


def test_parse_missing_time_series_key_raises():
    bad_payload = {"Note": "API rate limit reached"}
    with pytest.raises(RuntimeError, match="Unexpected"):
        _parse_daily_adjusted("AAPL", bad_payload)

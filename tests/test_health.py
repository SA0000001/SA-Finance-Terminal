from services.health import merge_source_health


def test_merge_source_health_drops_inactive_fallback_sources():
    previous = {
        "TradingView USDT.D": {
            "source": "TradingView USDT.D",
            "ok": True,
            "latency_ms": 120.0,
            "fetched_at": "2026-04-01T00:00:00+00:00",
            "last_success_at": "2026-04-01T00:00:00+00:00",
            "error": "",
            "stale_after_seconds": 300,
        },
        "CoinGecko Global": {
            "source": "CoinGecko Global",
            "ok": True,
            "latency_ms": 160.0,
            "fetched_at": "2026-03-31T22:22:50+00:00",
            "last_success_at": "2026-03-31T22:22:50+00:00",
            "error": "",
            "stale_after_seconds": 900,
        },
    }
    latest = {
        "TradingView USDT.D": {
            "source": "TradingView USDT.D",
            "ok": True,
            "latency_ms": 95.0,
            "fetched_at": "2026-04-01T00:05:00+00:00",
            "last_success_at": "2026-04-01T00:05:00+00:00",
            "error": "",
            "stale_after_seconds": 300,
        }
    }

    merged = merge_source_health(previous, latest)

    assert set(merged) == {"TradingView USDT.D"}


def test_merge_source_health_keeps_last_success_for_current_failure():
    previous = {
        "OKX Funding": {
            "source": "OKX Funding",
            "ok": True,
            "latency_ms": 88.0,
            "fetched_at": "2026-04-01T00:00:00+00:00",
            "last_success_at": "2026-04-01T00:00:00+00:00",
            "error": "",
            "stale_after_seconds": 300,
        }
    }
    latest = {
        "OKX Funding": {
            "source": "OKX Funding",
            "ok": False,
            "latency_ms": 210.0,
            "fetched_at": "2026-04-01T00:02:00+00:00",
            "last_success_at": None,
            "error": "HTTP error",
            "stale_after_seconds": 300,
        }
    }

    merged = merge_source_health(previous, latest)

    assert merged["OKX Funding"]["last_success_at"] == "2026-04-01T00:00:00+00:00"
    assert merged["OKX Funding"]["error"] == "HTTP error"

from datetime import datetime

from notify import (
    build_telegram_summary,
    format_terminal_report_for_telegram,
    send_telegram_text,
    split_telegram_message,
)


def test_build_telegram_summary_includes_core_market_fields():
    context = {
        "data": {
            "BTC_P": "$101,000",
            "BTC_C": "1.80%",
            "Sup_Wall": "$99,500",
            "Res_Wall": "$103,000",
        },
        "analytics": {
            "scores": {
                "overlay": "Constructive Risk-On",
                "overall": 64,
                "dominant_driver": "Liquidity",
                "invalidate_conditions": ["VIX > 28"],
            }
        },
    }

    summary = build_telegram_summary(
        context,
        fallback_used=False,
        now=datetime(2026, 4, 1, 21, 0),
    )

    assert "Constructive Risk-On" in summary
    assert "$101,000" in summary
    assert "Liquidity" in summary
    assert "$99,500 / $103,000" in summary
    assert "VIX > 28" in summary


def test_format_terminal_report_for_telegram_formats_headings_and_bullets():
    report = "### Baslik\nParagraf\n- Ilk madde\n- Ikinci madde"

    formatted = format_terminal_report_for_telegram(report)

    assert "*Baslik*" in formatted
    assert "• Ilk madde" in formatted
    assert "• Ikinci madde" in formatted


def test_split_telegram_message_respects_limit():
    text = "A" * 25 + "\n\n" + "B" * 25 + "\n\n" + "C" * 25

    parts = split_telegram_message(text, limit=35)

    assert len(parts) == 3
    assert all(len(part) <= 35 for part in parts)


def test_send_telegram_text_falls_back_to_plain_text(monkeypatch):
    calls = []

    class FakeResponse:
        def __init__(self, ok: bool, text: str = ""):
            self.ok = ok
            self.text = text

    def fake_post(url, json, timeout):
        calls.append(json)
        if json.get("parse_mode") == "Markdown":
            return FakeResponse(False, "markdown failed")
        return FakeResponse(True)

    monkeypatch.setattr("notify.requests.post", fake_post)

    send_telegram_text("token", "chat", "*merhaba*", prefer_markdown=True)

    assert len(calls) == 2
    assert calls[0]["parse_mode"] == "Markdown"
    assert "parse_mode" not in calls[1]

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

from domain.analytics import build_alerts, build_analytics_payload
from domain.market_brief import build_market_brief
from services.ai_service import _fallback_terminal_report, build_openrouter_client, generate_strategy_report
from services.health import build_health_summary
from services.market_data import load_terminal_data
from services.preferences import DEFAULT_PREFERENCES, load_preferences

DEFAULT_MODEL = "google/gemini-2.5-flash"
DEFAULT_DEPTH = "Orta"
TELEGRAM_MESSAGE_LIMIT = 2800
ISTANBUL_TZ = ZoneInfo("Europe/Istanbul")


@dataclass(frozen=True)
class RuntimeConfig:
    openrouter_api_key: str
    telegram_token: str
    telegram_chat_id: str
    fred_api_key: str
    report_depth: str
    openrouter_model: str


def _safe(value, fallback: str = "-") -> str:
    if value in (None, "", [], {}):
        return fallback
    return str(value)


def load_runtime_config() -> RuntimeConfig:
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    telegram_token = os.getenv("TELEGRAM_TOKEN", "").strip()
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    fred_api_key = os.getenv("FRED_API_KEY", "").strip()
    report_depth = os.getenv("REPORT_DEPTH", DEFAULT_DEPTH).strip() or DEFAULT_DEPTH
    openrouter_model = os.getenv("OPENROUTER_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL

    missing = [
        name
        for name, value in (
            ("OPENROUTER_API_KEY", openrouter_api_key),
            ("TELEGRAM_TOKEN", telegram_token),
            ("TELEGRAM_CHAT_ID", telegram_chat_id),
        )
        if not value
    ]
    if missing:
        raise RuntimeError(f"Eksik zorunlu environment variable: {', '.join(missing)}")

    return RuntimeConfig(
        openrouter_api_key=openrouter_api_key,
        telegram_token=telegram_token,
        telegram_chat_id=telegram_chat_id,
        fred_api_key=fred_api_key,
        report_depth=report_depth,
        openrouter_model=openrouter_model,
    )


def build_bulletin_context(config: RuntimeConfig) -> dict:
    preferences = load_preferences()
    thresholds = preferences.get("thresholds") or DEFAULT_PREFERENCES["thresholds"]

    data = load_terminal_data(config.fred_api_key)
    health_summary = build_health_summary(data.get("_health", {}))
    brief = build_market_brief(data)
    analytics = build_analytics_payload(data)
    alerts = build_alerts(data, thresholds)

    return {
        "data": data,
        "brief": brief,
        "analytics": analytics,
        "alerts": alerts,
        "health_summary": health_summary,
    }


def normalize_report_payload(report, context: dict) -> dict:
    fallback_terminal = _fallback_terminal_report(context["data"], context["brief"], context["analytics"])
    if not isinstance(report, dict):
        return {"terminal_report": fallback_terminal, "raw": str(report or "").strip()}
    return {
        "terminal_report": str(report.get("terminal_report") or fallback_terminal),
        "raw": str(report.get("raw") or "").strip(),
    }


def generate_bulletin_report(client, context: dict, config: RuntimeConfig) -> tuple[dict, bool]:
    try:
        report = generate_strategy_report(
            client,
            context["data"],
            context["brief"],
            context["analytics"],
            context["alerts"],
            context["health_summary"],
            model=config.openrouter_model,
            depth=config.report_depth,
        )
        return normalize_report_payload(report, context), False
    except Exception as exc:
        print(f"AI raporu uretilemedi, fallback bulten kullaniliyor: {exc}")
        return normalize_report_payload(None, context), True


def build_telegram_summary(context: dict, fallback_used: bool = False, now: datetime | None = None) -> str:
    now = now or datetime.now(ISTANBUL_TZ)
    data = context["data"]
    scores = context["analytics"].get("scores", {})
    invalidate = " | ".join(scores.get("invalidate_conditions", [])[:1]) or _safe(scores.get("weakest_driver"))

    lines = [
        "*SA Finance Alpha | Gunluk Makro Bulten*",
        now.strftime("%d.%m.%Y %H:%M TRT"),
        f"Rejim: {_safe(scores.get('overlay'))} ({_safe(scores.get('overall'))}/100)",
        f"BTC: {_safe(data.get('BTC_P'))} | 24s {_safe(data.get('BTC_C'))}",
        f"Ana surucu: {_safe(scores.get('dominant_driver'))}",
        f"Destek / Direnc: {_safe(data.get('Sup_Wall'))} / {_safe(data.get('Res_Wall'))}",
        f"Ana risk: {invalidate}",
    ]
    if fallback_used:
        lines.append("Not: AI yerine fallback bulten kullanildi.")
    return "\n".join(lines)


def format_terminal_report_for_telegram(report_text: str) -> str:
    formatted_lines = []
    for raw_line in (report_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            formatted_lines.append("")
            continue
        if line.startswith("### "):
            formatted_lines.append(f"*{line[4:].strip()}*")
            continue
        if line.startswith("- "):
            formatted_lines.append(f"- {line[2:].strip()}")
            continue
        formatted_lines.append(line)

    text = "\n".join(formatted_lines).strip()
    while "\n\n\n" in text:
        text = text.replace("\n\n\n", "\n\n")
    return text


def split_telegram_message(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT, reserved: int = 0) -> list[str]:
    remaining = (text or "").strip()
    if not remaining:
        return []

    chunk_limit = max(1, limit - max(reserved, 0))
    parts = []
    while remaining:
        if len(remaining) <= chunk_limit:
            parts.append(remaining)
            break
        split_at = remaining.rfind("\n\n", 0, chunk_limit)
        if split_at == -1:
            split_at = remaining.rfind("\n", 0, chunk_limit)
        if split_at == -1:
            split_at = chunk_limit
        parts.append(remaining[:split_at].strip())
        remaining = remaining[split_at:].strip()
    return parts


def send_telegram_text(token: str, chat_id: str, text: str, *, prefer_markdown: bool = True) -> dict:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    if prefer_markdown:
        response = requests.post(url, json={**payload, "parse_mode": "Markdown"}, timeout=15)
        if response.ok:
            return response.json().get("result", {})

    fallback = requests.post(url, json=payload, timeout=15)
    if fallback.ok:
        return fallback.json().get("result", {})
    raise RuntimeError(f"Telegram sendMessage failed: {fallback.text}")


def delete_telegram_message(token: str, chat_id: str, message_id: int) -> bool:
    url = f"https://api.telegram.org/bot{token}/deleteMessage"
    response = requests.post(url, json={"chat_id": chat_id, "message_id": message_id}, timeout=15)
    return response.ok


def build_failure_notification(error_text: str, now: datetime | None = None) -> str:
    now = now or datetime.now(ISTANBUL_TZ)
    lowered = error_text.lower()
    if "message is too long" in lowered:
        reason = "Telegram mesaj limiti asildi."
    else:
        reason = error_text.replace("\n", " ").strip()[:180]
    return "\n".join(
        [
            "Gunluk Makro Bulten gonderilemedi.",
            now.strftime("%d.%m.%Y %H:%M TRT"),
            f"Neden: {reason}",
        ]
    )


def send_daily_bulletin(token: str, chat_id: str, summary_text: str, terminal_report: str):
    report_text = format_terminal_report_for_telegram(terminal_report)
    report_parts = split_telegram_message(report_text, reserved=32)
    total_parts = len(report_parts)
    sent_message_ids: list[int] = []

    if not report_parts:
        failure_note = build_failure_notification("Makro Bulten bos uretildi.")
        send_telegram_text(token, chat_id, failure_note, prefer_markdown=False)
        raise RuntimeError("Makro Bulten bos uretildi.")

    try:
        for index, part in enumerate(report_parts, start=1):
            if total_parts > 1:
                header = f"*Makro Bulten {index}/{total_parts}*\n\n"
            else:
                header = "*Makro Bulten*\n\n"
            result = send_telegram_text(token, chat_id, f"{header}{part}", prefer_markdown=True)
            message_id = result.get("message_id") if isinstance(result, dict) else None
            if isinstance(message_id, int):
                sent_message_ids.append(message_id)

        send_telegram_text(token, chat_id, summary_text, prefer_markdown=True)
    except Exception as exc:
        for message_id in reversed(sent_message_ids):
            try:
                delete_telegram_message(token, chat_id, message_id)
            except Exception:
                pass
        failure_note = build_failure_notification(str(exc))
        try:
            send_telegram_text(token, chat_id, failure_note, prefer_markdown=False)
        except Exception:
            pass
        raise


def main():
    config = load_runtime_config()
    print("Terminal verileri yukleniyor...")
    context = build_bulletin_context(config)

    print("Makro Bulten uretiliyor...")
    client = build_openrouter_client(config.openrouter_api_key)
    report, fallback_used = generate_bulletin_report(client, context, config)

    print("Telegram ozeti hazirlaniyor...")
    summary_text = build_telegram_summary(context, fallback_used=fallback_used)

    print("Telegram gonderimi basliyor...")
    send_daily_bulletin(
        config.telegram_token,
        config.telegram_chat_id,
        summary_text,
        report["terminal_report"],
    )
    print("Gonderim tamamlandi.")


if __name__ == "__main__":
    main()

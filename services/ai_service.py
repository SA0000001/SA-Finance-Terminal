import re

from openai import OpenAI

from prompts.strategy_report import build_strategy_report_prompt


def build_openrouter_client(api_key: str) -> OpenAI:
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


def _extract_tagged_section(text: str, tag: str) -> str:
    pattern = re.compile(rf"<{tag}>\s*(.*?)\s*</{tag}>", re.IGNORECASE | re.DOTALL)
    match = pattern.search(text or "")
    return match.group(1).strip() if match else ""


def _fallback_x_lead(data: dict, analytics: dict) -> str:
    scores = analytics.get("scores", {})
    return (
        f"Makro Bulten: BTC {_safe(data.get('BTC_P'))}, rejim {scores.get('overall', '-')}/100 "
        f"({_safe(scores.get('overlay'))}). En kritik izlenecekler: ETF {_safe(data.get('ETF_FLOW_TOTAL'))}, "
        f"DXY {_safe(data.get('DXY'))}, VIX {_safe(data.get('VIX'))}."
    )[:280]


def _fallback_x_thread(data: dict, analytics: dict) -> str:
    scores = analytics.get("scores", {})
    items = [
        f"1/4 Rejim {scores.get('overall', '-')}/100 ve ana etiket {_safe(scores.get('overlay'))}. Dominant driver {_safe(scores.get('dominant_driver'))}, weakest link {_safe(scores.get('weakest_driver'))}.",
        f"2/4 Makro taraf: DXY {_safe(data.get('DXY'))}, US10Y {_safe(data.get('US10Y'))}, VIX {_safe(data.get('VIX'))}, ETF netflow {_safe(data.get('ETF_FLOW_TOTAL'))}.",
        f"3/4 Kripto internalleri: funding {_safe(data.get('FR'))}, OI {_safe(data.get('OI'))}, L/S {_safe(data.get('LS_Ratio'))}, Taker {_safe(data.get('Taker'))}.",
        f"4/4 Seviyeler: destek {_safe(data.get('Sup_Wall'))}, direnc {_safe(data.get('Res_Wall'))}. Invalidate: {(_safe(' | '.join(scores.get('invalidate_conditions', [])[:1])))}",
    ]
    return "\n".join(items)


def _safe(value, fallback: str = "-") -> str:
    if value in (None, "", [], {}):
        return fallback
    return str(value)


def _fallback_terminal_report(data: dict, brief: dict, analytics: dict) -> str:
    scores = analytics.get("scores", {})
    return "\n".join(
        [
            "### Bugunun Ozeti",
            f"BTC {_safe(data.get('BTC_P'))} seviyesinde. Rejim {scores.get('overall', '-')}/100 ve {_safe(scores.get('overlay'))}.",
            "",
            "### Rejim ve Bias",
            f"Bias: {_safe(scores.get('bias'))}",
            "",
            "### Makro Suruculer",
            f"DXY {_safe(data.get('DXY'))}, VIX {_safe(data.get('VIX'))}, ETF {_safe(data.get('ETF_FLOW_TOTAL'))}.",
            "",
            "### Kripto Ic Gorunum",
            f"Funding {_safe(data.get('FR'))}, OI {_safe(data.get('OI'))}, L/S {_safe(data.get('LS_Ratio'))}, Taker {_safe(data.get('Taker'))}.",
            "",
            "### Takvim ve Katalizorler",
            f"Haber akisi: {_safe(data.get('NEWS', [{}])[0].get('title') if data.get('NEWS') else '-')} | Takvim kaynagi: {_safe(data.get('ECONOMIC_CALENDAR_SOURCE'))}",
            "",
            "### Seviyeler ve Invalidation",
            f"Destek {_safe(data.get('Sup_Wall'))}, direnc {_safe(data.get('Res_Wall'))}. Invalidate: {_safe(' | '.join(scores.get('invalidate_conditions', [])[:2]))}",
            "",
            "### Bugun Ne Izlenmeli?",
            f"{_safe(' | '.join(scores.get('watch_next', [])[:3]))}",
        ]
    )


def _parse_report_payload(content: str, data: dict, brief: dict, analytics: dict) -> dict:
    terminal_report = _extract_tagged_section(content, "terminal_report")
    x_lead = _extract_tagged_section(content, "x_lead")
    x_thread = _extract_tagged_section(content, "x_thread")

    return {
        "terminal_report": terminal_report or _fallback_terminal_report(data, brief, analytics),
        "x_lead": x_lead or _fallback_x_lead(data, analytics),
        "x_thread": x_thread or _fallback_x_thread(data, analytics),
        "raw": content.strip(),
    }


def generate_strategy_report(
    client: OpenAI,
    data: dict,
    brief: dict,
    analytics: dict,
    alerts: list[dict],
    health_summary: dict,
    model: str = "google/gemini-2.5-flash",
    depth: str = "Orta",
) -> dict:
    prompt = build_strategy_report_prompt(
        data,
        brief=brief,
        analytics=analytics,
        alerts=alerts,
        health_summary=health_summary,
        depth=depth,
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "You are a macro-crypto bulletin writer. Follow the requested tags exactly and avoid extra prefacing text.",
            },
            {"role": "user", "content": prompt},
        ],
        max_tokens=8000,
    )
    content = response.choices[0].message.content or ""
    return _parse_report_payload(content, data, brief, analytics)

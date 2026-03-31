from __future__ import annotations

from io import BytesIO

from domain.parsers import parse_number

PLACEHOLDER = "-"
DEFAULT_PINNED_METRICS = ["BTC_P", "BTC_C", "FNG", "FR", "VIX", "ETF_FLOW_TOTAL", "USDT_D", "TOTAL_CAP"]
METRIC_LABELS = {
    "BTC_P": "BTC fiyat",
    "BTC_C": "BTC 24s",
    "BTC_7D": "BTC 7g",
    "FNG": "Fear & Greed",
    "FR": "Funding",
    "OI": "Open Interest",
    "VIX": "VIX",
    "ETF_FLOW_TOTAL": "ETF netflow",
    "USDT_D": "USDT.D",
    "STABLE_C_D": "Stable.C.D",
    "TOTAL_CAP": "TOTAL",
    "TOTAL2_CAP": "TOTAL2",
    "TOTAL3_CAP": "TOTAL3",
    "ETH_P": "ETH fiyat",
    "SOL_P": "SOL fiyat",
    "DXY": "DXY",
    "FED": "FED",
}


def clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _metric_reason(label: str, value) -> str:
    return f"{label}: {value if value not in (None, '', PLACEHOLDER) else PLACEHOLDER}"


def build_regime_scores(data: dict) -> dict:
    btc_change = parse_number(data.get("BTC_C")) or 0.0
    etf_flow = parse_number(data.get("ETF_FLOW_TOTAL")) or 0.0
    stable_cd = parse_number(data.get("STABLE_C_D")) or 0.0
    usdt_d = parse_number(data.get("USDT_D")) or 0.0
    vix = parse_number(data.get("VIX")) or 20.0
    funding = parse_number(data.get("FR")) or 0.0
    ls_ratio = parse_number(data.get("LS_Ratio")) or 1.0
    total2 = parse_number(data.get("TOTAL2_CAP")) or 0.0
    total3 = parse_number(data.get("TOTAL3_CAP")) or 0.0
    total = parse_number(data.get("TOTAL_CAP")) or 0.0

    liquidity = clamp_score(55 + (etf_flow / 15) - (stable_cd * 3) - (usdt_d * 2))
    volatility = clamp_score(100 - (vix - 12) * 4 + max(btc_change, -8) * 2)
    positioning = clamp_score(65 - abs(funding) * 1800 - abs(ls_ratio - 1) * 30)
    breadth_ratio = ((total2 + total3) / (2 * total)) * 100 if total else 50
    breadth = clamp_score(40 + breadth_ratio * 0.6)
    overall = clamp_score((liquidity * 0.3) + (volatility * 0.2) + (positioning * 0.25) + (breadth * 0.25))

    return {
        "overall": overall,
        "subscores": {
            "Liquidity": liquidity,
            "Volatility": volatility,
            "Positioning": positioning,
            "Breadth": breadth,
        },
    }


def build_scenario_matrix(data: dict) -> list[dict]:
    current_price = parse_number(data.get("BTC_P")) or parse_number(data.get("BTC_Now")) or 0.0
    support = parse_number(data.get("Sup_Wall")) or (current_price * 0.98 if current_price else 0.0)
    resistance = parse_number(data.get("Res_Wall")) or (current_price * 1.02 if current_price else 0.0)

    return [
        {
            "Scenario": "Bullish",
            "Trigger": f"Fiyat {resistance:,.0f} ustu kalirsa" if resistance else PLACEHOLDER,
            "Follow-through": f"ETF akisi {data.get('ETF_FLOW_TOTAL', PLACEHOLDER)} ve funding {data.get('FR', PLACEHOLDER)} destekleyici olmali",
        },
        {
            "Scenario": "Base",
            "Trigger": (
                f"Fiyat {support:,.0f} - {resistance:,.0f} araliginda kalirsa"
                if support and resistance
                else PLACEHOLDER
            ),
            "Follow-through": f"VIX {data.get('VIX', PLACEHOLDER)} ve USDT.D {data.get('USDT_D', PLACEHOLDER)} dengeyi korumali",
        },
        {
            "Scenario": "Bear",
            "Trigger": f"Fiyat {support:,.0f} alti kapanirsa" if support else PLACEHOLDER,
            "Follow-through": f"Funding {data.get('FR', PLACEHOLDER)} ve ETF netflow {data.get('ETF_FLOW_TOTAL', PLACEHOLDER)} zayiflamayi teyit etmeli",
        },
    ]


def build_alerts(data: dict, thresholds: dict) -> list[dict]:
    alerts = []
    funding = parse_number(data.get("FR"))
    vix = parse_number(data.get("VIX"))
    etf_flow = parse_number(data.get("ETF_FLOW_TOTAL"))

    funding_above = thresholds.get("funding_above")
    vix_above = thresholds.get("vix_above")
    etf_below = thresholds.get("etf_flow_below")

    if funding is not None and funding_above is not None and funding > funding_above:
        alerts.append(
            {
                "title": "Funding alarmi",
                "detail": f"Funding {data.get('FR', PLACEHOLDER)} | esik {funding_above:.4f}",
                "level": "warning",
            }
        )
    if vix is not None and vix_above is not None and vix > vix_above:
        alerts.append(
            {
                "title": "VIX alarmi",
                "detail": f"VIX {data.get('VIX', PLACEHOLDER)} | esik {vix_above:.2f}",
                "level": "error",
            }
        )
    if etf_flow is not None and etf_below is not None and etf_flow < etf_below:
        alerts.append(
            {
                "title": "ETF alarmi",
                "detail": f"ETF netflow {data.get('ETF_FLOW_TOTAL', PLACEHOLDER)} | esik {etf_below:.1f}",
                "level": "error",
            }
        )

    return alerts


def build_pinned_metrics(data: dict, metric_keys: list[str]) -> list[tuple[str, str, str]]:
    items = []
    for key in metric_keys[:8]:
        label = METRIC_LABELS.get(key, key)
        value = data.get(key, PLACEHOLDER)
        delta_key = f"{key}_C"
        delta = data.get(delta_key, "") if delta_key in data else ""
        items.append((label, value, delta))
    return items


def build_daily_summary_markdown(
    data: dict, brief: dict, analytics: dict, alerts: list[dict], health_summary: dict
) -> str:
    lines = [
        "# Gunluk Ozet",
        "",
        f"- BTC: {data.get('BTC_P', PLACEHOLDER)} | 24s {data.get('BTC_C', PLACEHOLDER)}",
        f"- Rejim skoru: {analytics['scores']['overall']}/100",
        f"- Likidite: {brief['liquidity']['title']}",
        f"- Pozisyonlanma: {brief['positioning']['title']}",
        f"- Odak seviye: {brief['focus']['detail']}",
        f"- Veri sagligi: {health_summary.get('healthy_sources', 0)} saglikli / {len(health_summary.get('failed_sources', []))} problemli / {len(health_summary.get('stale_sources', []))} stale",
        "",
        "## Neden boyle dusunuyorum?",
    ]
    for key in ["regime", "positioning", "liquidity", "focus"]:
        lines.append(f"- {brief[key]['title']}: " + " | ".join(brief[key].get("why", [])))
    if alerts:
        lines.extend(["", "## Aktif Alarmlar"])
        for alert in alerts:
            lines.append(f"- {alert['title']}: {alert['detail']}")
    lines.extend(["", "## Senaryo Matrisi"])
    for row in analytics["scenarios"]:
        lines.append(f"- {row['Scenario']}: {row['Trigger']} | {row['Follow-through']}")
    return "\n".join(lines)


def markdown_to_basic_pdf_bytes(markdown_text: str) -> bytes:
    safe_text = markdown_text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    lines = [line[:100] for line in safe_text.splitlines() if line.strip()]
    if not lines:
        lines = ["Gunluk Ozet"]

    content_lines = ["BT", "/F1 11 Tf", "50 780 Td"]
    first = True
    for line in lines[:45]:
        if first:
            content_lines.append(f"({line}) Tj")
            first = False
        else:
            content_lines.append("0 -16 Td")
            content_lines.append(f"({line}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="ignore")

    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Count 1 /Kids [3 0 R] >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n"
    )
    objects.append(f"4 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1") + stream + b"\nendstream endobj\n")
    objects.append(b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")

    buffer = BytesIO()
    buffer.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(buffer.tell())
        buffer.write(obj)
    xref_pos = buffer.tell()
    buffer.write(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010d} 00000 n \n".encode("latin-1"))
    buffer.write(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("latin-1"))
    return buffer.getvalue()


def build_analytics_payload(data: dict) -> dict:
    return {
        "scores": build_regime_scores(data),
        "scenarios": build_scenario_matrix(data),
    }

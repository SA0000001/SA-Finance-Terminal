import re

from openai import OpenAI

from prompts.strategy_report import build_strategy_report_prompt


def build_openrouter_client(api_key: str) -> OpenAI:
    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


def _safe(value, fallback: str = "-") -> str:
    if value in (None, "", [], {}):
        return fallback
    return str(value)


def _normalize_content_part(part) -> str:
    if part is None:
        return ""
    if isinstance(part, str):
        return part
    if isinstance(part, dict):
        for key in ("text", "content", "value", "output_text"):
            value = part.get(key)
            if isinstance(value, list):
                normalized = _normalize_content(value)
                if normalized:
                    return normalized
            if value not in (None, ""):
                return str(value)
        return ""
    for attr in ("text", "content", "value", "output_text"):
        value = getattr(part, attr, None)
        if isinstance(value, list):
            normalized = _normalize_content(value)
            if normalized:
                return normalized
        if value not in (None, ""):
            return str(value)
    return ""


def _normalize_content(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(part for part in (_normalize_content_part(item) for item in content) if part).strip()
    return _normalize_content_part(content)


def _extract_tagged_section(text, tag: str) -> str:
    normalized_text = _normalize_content(text)
    pattern = re.compile(rf"<{tag}>\s*(.*?)\s*</{tag}>", re.IGNORECASE | re.DOTALL)
    match = pattern.search(normalized_text or "")
    return match.group(1).strip() if match else ""


def _fallback_x_lead(data: dict, analytics: dict) -> str:
    scores = analytics.get("scores", {})
    return (
        f"Makro Bulten | BTC {_safe(data.get('BTC_P'))}, rejim {scores.get('overall', '-')}/100 "
        f"({_safe(scores.get('overlay'))}). Ana konu {_safe(scores.get('dominant_driver'))}; "
        f"zayif halka {_safe(scores.get('weakest_driver'))}. ETF {_safe(data.get('ETF_FLOW_TOTAL'))}, "
        f"DXY {_safe(data.get('DXY'))}, VIX {_safe(data.get('VIX'))} bugunun ana tetikleyicileri."
    )[:280]


def _fallback_x_thread(data: dict, analytics: dict) -> str:
    scores = analytics.get("scores", {})
    items = [
        f"1/5 Rejim {scores.get('overall', '-')}/100 ve etiket {_safe(scores.get('overlay'))}. Ana cikarim: {_safe(scores.get('summary'))}.",
        f"2/5 Makro taraf: DXY {_safe(data.get('DXY'))}, US10Y {_safe(data.get('US10Y'))}, VIX {_safe(data.get('VIX'))}, ETF netflow {_safe(data.get('ETF_FLOW_TOTAL'))}.",
        f"3/5 BTC ve turev: funding {_safe(data.get('FR'))}, OI {_safe(data.get('OI'))}, L/S {_safe(data.get('LS_Ratio'))}, Taker {_safe(data.get('Taker'))}.",
        f"4/5 Katilim ve akis: dominant driver {_safe(scores.get('dominant_driver'))}, weakest link {_safe(scores.get('weakest_driver'))}, BTC {_safe(data.get('BTC_7D'))} 7g.",
        f"5/5 Seviyeler: destek {_safe(data.get('Sup_Wall'))}, direnc {_safe(data.get('Res_Wall'))}. Invalidate: {_safe(' | '.join(scores.get('invalidate_conditions', [])[:1]))}",
    ]
    return "\n".join(items)


def _fallback_terminal_report(data: dict, brief: dict, analytics: dict) -> str:
    scores = analytics.get("scores", {})
    participation = scores.get("participation", {})
    macro_breadth = participation.get("subfactors", {}).get("macro", {})
    crypto_breadth = participation.get("subfactors", {}).get("crypto", {})
    news = data.get("NEWS", [])
    top_news = news[0].get("title") if news else "-"
    return "\n".join(
        [
            "### SA Finance Alpha Makro Bulteni Giris",
            f"Gunun ana cercevesi BTC {_safe(data.get('BTC_P'))}, rejim {scores.get('overall', '-')}/100 ve {_safe(scores.get('overlay'))}. Bu not, makro risk istahi ile kripto internallerini tek akista okur.",
            "",
            "### Gunluk Harita ve Ana Cikarim",
            f"Dominant driver {_safe(scores.get('dominant_driver'))}, weakest link {_safe(scores.get('weakest_driver'))}. Gunun davranis cizgisi: {_safe(scores.get('bias'))}",
            "",
            "### Makro Ortam ve Risk Istahi",
            f"DXY {_safe(data.get('DXY'))}, US10Y {_safe(data.get('US10Y'))}, VIX {_safe(data.get('VIX'))} ve ETF akisi {_safe(data.get('ETF_FLOW_TOTAL'))} birlikte okundugunda risk istahi {_safe(scores.get('overlay'))} bolgesinde. Neden onemli: bu blok bozulursa rejim destegi hizla zayiflar.",
            "",
            "### BTC, Turev ve Order Book Analizi",
            f"BTC {_safe(data.get('BTC_P'))} seviyesinde; funding {_safe(data.get('FR'))}, OI {_safe(data.get('OI'))}, L/S {_safe(data.get('LS_Ratio'))}, taker {_safe(data.get('Taker'))}. Order book sinyali {_safe(data.get('ORDERBOOK_SIGNAL'))}; detail {_safe(data.get('ORDERBOOK_SIGNAL_DETAIL'))}.",
            "",
            "### ETF, Stablecoin ve Altcoinler",
            f"ETF netflow {_safe(data.get('ETF_FLOW_TOTAL'))}, USDT.D {_safe(data.get('USDT_D'))}, Stable.C.D {_safe(data.get('STABLE_C_D'))}. Neden onemli: spot talep ile ic likidite ayni yondeyse trend daha saglikli okunur.",
            "",
            "### Macro Breadth ve Crypto Breadth",
            f"Macro breadth {_safe(macro_breadth.get('score'))}/100, crypto breadth {_safe(crypto_breadth.get('score'))}/100, composite participation {_safe(participation.get('score'))}/100. Neden onemli: katilim daralirsa fiyat yukselisi daha kirilgan kalir.",
            "",
            "### Ekonomik Takvim ve Olasi Etkiler",
            f"Takvim kaynagi {_safe(data.get('ECONOMIC_CALENDAR_SOURCE'))}. En yakin yuksek etkili veriler DXY, VIX ve faiz beklentileri uzerinden BTC oynakligini etkileyebilir.",
            "",
            "### Onemli Haberler ve Piyasa Yorumu",
            f"Haber akisinin ana basligi: {_safe(top_news)}. Neden onemli: haber akisinin rejime etkisi ETF, stablecoin ve risk istahi tarafinda fiyat teyidi yaratabilir.",
            "",
            "### Long / Short / Bekle ve Kritik Riskler",
            f"Long ancak destekler korunur ve ETF akisi zayiflamazsa anlamli. Short ancak {_safe(scores.get('weakest_driver'))} bozulmasi ve vol baskisi artarsa temizlesir. Bekle modu, invalidate kosullari fiyatin hemen ustune biniyorsa daha sagliklidir.",
            "",
            "### Kritik Seviyeler, Invalidation ve Bugun Ne Izlenmeli",
            f"Destek {_safe(data.get('Sup_Wall'))}, direnc {_safe(data.get('Res_Wall'))}. Invalidate: {_safe(' | '.join(scores.get('invalidate_conditions', [])[:2]))}. Watch next: {_safe(' | '.join(scores.get('watch_next', [])[:3]))}",
        ]
    )


def _parse_report_payload(content, data: dict, brief: dict, analytics: dict) -> dict:
    normalized_content = _normalize_content(content)
    terminal_report = _extract_tagged_section(content, "terminal_report")
    x_lead = _extract_tagged_section(content, "x_lead")
    x_thread = _extract_tagged_section(content, "x_thread")

    return {
        "terminal_report": terminal_report or _fallback_terminal_report(data, brief, analytics),
        "x_lead": x_lead or _fallback_x_lead(data, analytics),
        "x_thread": x_thread or _fallback_x_thread(data, analytics),
        "raw": normalized_content.strip(),
    }


def generate_strategy_report(
    client: OpenAI,
    data: dict,
    *args,
    brief: dict | None = None,
    analytics: dict | None = None,
    alerts: list[dict] | None = None,
    health_summary: dict | None = None,
    model: str = "google/gemini-2.5-flash",
    depth: str = "Orta",
) -> dict:
    if args:
        remaining = list(args)
        if remaining and isinstance(remaining[0], dict):
            brief = remaining.pop(0)
        if remaining and isinstance(remaining[0], dict):
            analytics = remaining.pop(0)
        if remaining and isinstance(remaining[0], list):
            alerts = remaining.pop(0)
        if remaining and isinstance(remaining[0], dict):
            health_summary = remaining.pop(0)
        if remaining and isinstance(remaining[0], str):
            model = remaining.pop(0)
        if remaining and isinstance(remaining[0], str):
            depth = remaining.pop(0)

    brief = brief or {}
    analytics = analytics or {}
    alerts = alerts or []
    health_summary = health_summary or {}

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
    content = _normalize_content(response.choices[0].message.content)
    return _parse_report_payload(content, data, brief, analytics)

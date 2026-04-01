import pandas as pd


DEPTH_RULES = {
    "Kisa": {
        "terminal_length": "350-500 kelime",
        "style": "Kisa ama research-note tonunda, net ve karar odakli yaz.",
    },
    "Orta": {
        "terminal_length": "550-800 kelime",
        "style": "Research note tonunda, sayisal, editoryal ve uygulanabilir yaz.",
    },
    "Derin": {
        "terminal_length": "800-1100 kelime",
        "style": "Detayli ama tekrar etmeyen, bolum disiplini guclu bir research note yaz.",
    },
}


def _safe(value, fallback: str = "-") -> str:
    if value in (None, "", [], {}):
        return fallback
    return str(value)


def _format_news(news: list[dict]) -> str:
    if not news:
        return "- Haber akisi su an yok"
    return "\n".join(
        f"- {_safe(item.get('title'))} | {_safe(item.get('source'))} | {_safe(item.get('time'))}"
        for item in news[:3]
    )


def _format_alerts(alerts: list[dict]) -> str:
    if not alerts:
        return "- Aktif alarm yok"
    return "\n".join(
        f"- {_safe(item.get('title'))}: {_safe(item.get('detail'))}"
        for item in alerts[:4]
    )


def _format_health(health_summary: dict) -> str:
    rows = health_summary.get("rows", [])
    if not rows:
        return "- Veri sagligi kaydi yok"
    problem_rows = [row for row in rows if row.get("Durum") != "OK"][:4]
    if not problem_rows:
        return (
            f"- Veri sagligi: {health_summary.get('healthy_sources', 0)} saglikli kaynak, "
            f"{len(health_summary.get('failed_sources', []))} fail, {len(health_summary.get('stale_sources', []))} stale"
        )
    return "\n".join(
        f"- {_safe(row.get('Kaynak'))}: {_safe(row.get('Durum'))} | {_safe(row.get('Detay'))}"
        for row in problem_rows
    )


def _format_calendar(calendar_events: list[dict]) -> str:
    if not calendar_events:
        return "- Calendar unavailable"
    return "\n".join(
        (
            f"- {_safe(event.get('date'))} {_safe(event.get('time'))} | {_safe(event.get('country'))} | "
            f"{_safe(event.get('impact'))} | {_safe(event.get('title'))} | "
            f"A:{_safe(event.get('actual'))} F:{_safe(event.get('forecast'))} P:{_safe(event.get('previous'))}"
        )
        for event in calendar_events[:3]
    )


def _format_brief(brief: dict) -> str:
    sections = []
    for key in ("regime", "liquidity", "positioning", "focus"):
        item = brief.get(key, {})
        why = " | ".join(item.get("why", [])) if item.get("why") else "-"
        sections.append(
            f"- {key}: {_safe(item.get('title'))} | badge: {_safe(item.get('badge'))} | why: {why}"
        )
    return "\n".join(sections)


def _format_scenarios(analytics: dict) -> str:
    scenarios = analytics.get("scenarios", [])
    if not scenarios:
        return "- Senaryo verisi yok"
    return "\n".join(
        f"- {_safe(item.get('Scenario'))}: {_safe(item.get('Trigger'))} | {_safe(item.get('Follow-through'))}"
        for item in scenarios[:3]
    )


def _format_factor_lines(scores: dict) -> str:
    factors = scores.get("factors", [])
    if not factors:
        return "- Faktor verisi yok"
    return "\n".join(
        (
            f"- {_safe(factor.get('label'))}: {_safe(factor.get('score'))}/100 | "
            f"delta7g {_safe(factor.get('delta_7d'))} | support {_safe(factor.get('primary_support'))} | "
            f"risk {_safe(factor.get('primary_risk'))}"
        )
        for factor in factors
    )


def build_strategy_report_prompt(
    data,
    brief: dict | None = None,
    analytics: dict | None = None,
    alerts: list[dict] | None = None,
    health_summary: dict | None = None,
    depth: str = "Orta",
):
    data = data or {}
    brief = brief or {}
    analytics = analytics or {}
    alerts = alerts or []
    health_summary = health_summary or {}
    rules = DEPTH_RULES.get(depth, DEPTH_RULES["Orta"])
    now_text = pd.Timestamp.now(tz="Europe/Istanbul").strftime("%d %B %Y %H:%M")
    scores = analytics.get("scores", {})
    participation = scores.get("participation", {})
    macro_breadth = participation.get("subfactors", {}).get("macro", {})
    crypto_breadth = participation.get("subfactors", {}).get("crypto", {})

    return f"""
Sen SA Finance Alpha Terminal icin gunluk Makro Bulten hazirlayan ust duzey bir makro-kripto stratejistsin.
Turkce yaz. Cikti profesyonel, research-note tonunda, sayisal ve paylasilabilir olsun.

Ana amac:
- Terminal icin karar destek bulteni yazmak
- X hesabinda paylasilabilecek ozet paketini birlikte vermek
- Anlatiyi editoryal ama disiplinli tutmak; rapor genel yorum gibi degil, gunluk strateji notu gibi okunmali

Stil:
- {rules['style']}
- Terminal raporu uzunlugu: {rules['terminal_length']}
- Tekrara dusme
- Her ana bolumde neden onemli oldugunu tek cumleyle bagla
- Genel laflar yerine esik, trigger, invalidate ve davranis cumlesi ver
- Gereksiz yasal uyari ekleme
- Haberleri tek basina anlatma; rejime etkisi uzerinden kullan
- Markdown tablo kullanma
- Her ana bolum 1 kisa paragraf ve gerekirse 2-4 kisa madde icersin
- Ayni metriği birden fazla bolumde uzun uzun tekrar etme
- "Long / Short / Bekle" bolumunde net davranis kosullari ver
- "Ekonomik Takvim" bolumunde en fazla 3 olay yaz
- "Onemli Haberler" bolumunde en fazla 3 haber yaz

Zorunlu cikti formati:
<terminal_report>
### SA Finance Alpha Makro Bulteni Giris
### Gunluk Harita ve Ana Cikarim
### Makro Ortam ve Risk Istahi
### BTC, Turev ve Order Book Analizi
### ETF, Stablecoin ve Altcoinler
### Macro Breadth ve Crypto Breadth
### Ekonomik Takvim ve Olasi Etkiler
### Onemli Haberler ve Piyasa Yorumu
### Long / Short / Bekle ve Kritik Riskler
### Kritik Seviyeler, Invalidation ve Bugun Ne Izlenmeli
</terminal_report>
<x_lead>
Tek postluk acilis metni. 280 karakteri gecmesin. Pazarlama dili kullanma; sabah notu gibi yaz.
</x_lead>
<x_thread>
1/5 ...
2/5 ...
3/5 ...
4/5 ...
5/5 ...
</x_thread>

Canli baglam ({now_text}):

1) Rejim motoru
- Overall: {_safe(scores.get('overall'))}/100
- Base score: {_safe(scores.get('base_score'))}/100
- Fragility: {_safe(scores.get('fragility', {}).get('score'))}/100 | {_safe(scores.get('fragility', {}).get('label'))}
- Confidence: {_safe(scores.get('confidence'))}/100 | {_safe(scores.get('confidence_label'))}
- Regime band: {_safe(scores.get('regime_band'))}
- Overlay: {_safe(scores.get('overlay'))}
- Bias: {_safe(scores.get('bias'))}
- Dominant driver: {_safe(scores.get('dominant_driver'))}
- Weakest link: {_safe(scores.get('weakest_driver'))}
- Summary: {_safe(scores.get('summary'))}

2) Faktor kirilimi
{_format_factor_lines(scores)}

3) Participation
- Composite participation: {_safe(participation.get('score'))}/100 | {_safe(participation.get('state'))}
- Macro breadth: {_safe(macro_breadth.get('score'))}/100 | {_safe(macro_breadth.get('state'))}
- Crypto breadth: {_safe(crypto_breadth.get('score'))}/100 | {_safe(crypto_breadth.get('state'))}

4) Piyasa ve execution verileri
- BTC: {_safe(data.get('BTC_P'))} | 24s {_safe(data.get('BTC_C'))} | 7g {_safe(data.get('BTC_7D'))}
- Funding: {_safe(data.get('FR'))} | OI: {_safe(data.get('OI'))} | L/S: {_safe(data.get('LS_Ratio'))} | Taker: {_safe(data.get('Taker'))}
- ETF netflow: {_safe(data.get('ETF_FLOW_TOTAL'))} | Tarih: {_safe(data.get('ETF_FLOW_DATE'))} | Kaynak: {_safe(data.get('ETF_FLOW_SOURCE'))}
- DXY: {_safe(data.get('DXY'))} | US10Y: {_safe(data.get('US10Y'))} | VIX: {_safe(data.get('VIX'))} | FED: {_safe(data.get('FED'))}
- USDT.D: {_safe(data.get('USDT_D'))} | Stable.C.D: {_safe(data.get('STABLE_C_D'))}
- Order book signal: {_safe(data.get('ORDERBOOK_SIGNAL'))}
- Order book detail: {_safe(data.get('ORDERBOOK_SIGNAL_DETAIL'))}
- Support: {_safe(data.get('Sup_Wall'))} | Resistance: {_safe(data.get('Res_Wall'))}

5) Brief yorumu
{_format_brief(brief)}

6) Invalidate ve watch next
{chr(10).join(f"- {item}" for item in scores.get('invalidate_conditions', [])) or '- Invalidate verisi yok'}
{chr(10).join(f"- watch: {item}" for item in scores.get('watch_next', [])) or '- Watch list yok'}

7) Senaryolar
{_format_scenarios(analytics)}

8) Alarmlar
{_format_alerts(alerts)}

9) Haberler
{_format_news(data.get('NEWS', []))}

10) Ekonomik takvim
Kaynak: {_safe(data.get('ECONOMIC_CALENDAR_SOURCE'))}
{_format_calendar(data.get('ECONOMIC_CALENDAR', []))}

11) Veri sagligi
{_format_health(health_summary)}

Ek kurallar:
- X lead ve X thread, terminal raporunun kisa yansimasi olmali; yeni hikaye uydurma.
- X thread 5 madde olmali ve her madde tek paragraf olmali.
- Terminal raporunda kritik seviyeleri dolar veya yuzde ile mutlaka yaz.
- Invalidation bolumunde ne olursa gorusun bozulacagini net soyle.
- "Gunluk Harita ve Ana Cikarim" bolumunde rejim, dominant driver, weakest link ve gunun temel davranis cizgisi ilk 5-6 satirda verilmis olsun.
- "Long / Short / Bekle ve Kritik Riskler" bolumunde su uc kalip zorunlu: long icin anlamli kosul, short icin anlamli kosul, beklemek icin anlamli kosul.
"""

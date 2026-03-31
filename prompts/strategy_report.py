import pandas as pd

DEPTH_PROMPTS = {
    "Kisa": "Raporu 6 kisa bolumde, karar odakli ve oz yaz.",
    "Orta": "Raporu dengeli derinlikte, sayisal ve uygulanabilir sekilde yaz.",
    "Derin": "Raporu kapsamli, senaryo bazli ve tetikleyici seviyelerle detayli yaz.",
}


def build_strategy_report_prompt(data, depth: str = "Orta"):
    now_text = pd.Timestamp.now(tz="Europe/Istanbul").strftime("%d %B %Y %H:%M")
    prompt_style = DEPTH_PROMPTS.get(depth, DEPTH_PROMPTS["Orta"])
    news_lines = (
        "\n".join(f"- {item['title']} ({item['source']})" for item in data.get("NEWS", [])[:6]) or "- Haber yok"
    )

    return f"""
Sen deneyimli bir makro-kripto stratejistsin.
Turkce yaz. Yanit profesyonel, net ve sayisal olsun.

Stil:
{prompt_style}

Kurallar:
- Soyut yargilar yerine mevcut veriyi kullan.
- Fiyat, risk, likidite ve pozisyonlanma icin net seviyeler ver.
- Bullish / base / bear senaryolarini ayir.
- Gereksiz yasal uyari ekleme.

Canli veriler ({now_text}):
- BTC fiyat: {data.get('BTC_P', '-')} | 24s: {data.get('BTC_C', '-')} | 7g: {data.get('BTC_7D', '-')}
- Funding: {data.get('FR', '-')} | OI: {data.get('OI', '-')} | L/S: {data.get('LS_Ratio', '-')} | Taker: {data.get('Taker', '-')}
- ETF netflow: {data.get('ETF_FLOW_TOTAL', '-')} | Tarih: {data.get('ETF_FLOW_DATE', '-')}
- USDT.D: {data.get('USDT_D', '-')} | Stable.C.D: {data.get('STABLE_C_D', '-')}
- VIX: {data.get('VIX', '-')} | DXY: {data.get('DXY', '-')} | FED: {data.get('FED', '-')}
- TOTAL: {data.get('TOTAL_CAP', '-')} | TOTAL2: {data.get('TOTAL2_CAP', '-')} | TOTAL3: {data.get('TOTAL3_CAP', '-')}
- Order book: {data.get('ORDERBOOK_SIGNAL', '-')} | Detay: {data.get('ORDERBOOK_SIGNAL_DETAIL', '-')}
- Haberler:
{news_lines}

Beklenen cikti:
## Makro Ortam
## Kripto Rejimi
## Likidite ve Pozisyonlanma
## Senaryo Matrisi
## Islem Plani
## Kritik Riskler
"""

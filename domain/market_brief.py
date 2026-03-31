from domain.parsers import parse_number
from domain.signals import badge_class


def build_market_brief(data):
    btc_change = parse_number(data.get("BTC_C"))
    funding = parse_number(data.get("FR"))
    usdt_d = parse_number(data.get("USDT_D"))
    stable_c_d = parse_number(data.get("STABLE_C_D"))
    vix = parse_number(data.get("VIX"))
    etf_flow_total = data.get("ETF_FLOW_TOTAL", "—")
    etf_flow_num = parse_number(etf_flow_total)
    etf_flow_date = data.get("ETF_FLOW_DATE", "—")
    ls_signal = data.get("LS_Signal", "—")
    orderbook_signal = data.get("ORDERBOOK_SIGNAL", "—")
    orderbook_detail = data.get("ORDERBOOK_SIGNAL_DETAIL", "—")

    if btc_change is not None and btc_change >= 2:
        regime = {
            "label": "Piyasa Rejimi",
            "title": "Momentum Güçlü",
            "detail": f"BTC 24s {data.get('BTC_C', '—')} · VIX {data.get('VIX', '—')}",
            "badge": "TREND",
            "class": "signal-long",
        }
    elif btc_change is not None and btc_change <= -2:
        regime = {
            "label": "Piyasa Rejimi",
            "title": "Baskı Artıyor",
            "detail": f"BTC 24s {data.get('BTC_C', '—')} · VIX {data.get('VIX', '—')}",
            "badge": "RISK",
            "class": "signal-short",
        }
    else:
        regime = {
            "label": "Piyasa Rejimi",
            "title": "Denge Aranıyor",
            "detail": f"BTC 24s {data.get('BTC_C', '—')} · VIX {data.get('VIX', '—')}",
            "badge": "RANGE",
            "class": "signal-neutral",
        }

    if funding is not None and funding > 0 and "Long" in ls_signal:
        positioning = {
            "label": "Pozisyonlanma",
            "title": "Longlar Kalabalık",
            "detail": f"Funding {data.get('FR', '—')} · L/S {data.get('LS_Ratio', '—')} · Taker {data.get('Taker', '—')}",
            "badge": ls_signal,
            "class": "signal-short",
        }
    elif funding is not None and funding < 0:
        positioning = {
            "label": "Pozisyonlanma",
            "title": "Short Baskısı",
            "detail": f"Funding {data.get('FR', '—')} · L/S {data.get('LS_Ratio', '—')} · Taker {data.get('Taker', '—')}",
            "badge": ls_signal,
            "class": "signal-short",
        }
    else:
        positioning = {
            "label": "Pozisyonlanma",
            "title": "Daha Dengeli Akış",
            "detail": f"Funding {data.get('FR', '—')} · L/S {data.get('LS_Ratio', '—')} · Taker {data.get('Taker', '—')}",
            "badge": ls_signal,
            "class": badge_class(ls_signal),
        }

    liquidity_pressure = max(
        value for value in [usdt_d, stable_c_d] if value is not None
    ) if any(value is not None for value in [usdt_d, stable_c_d]) else None

    liquidity_detail = (
        f"ETF Netflow {etf_flow_total} · {etf_flow_date} · "
        f"Stable.C.D {data.get('STABLE_C_D', '—')} · USDT.D {data.get('USDT_D', '—')}"
    )

    if etf_flow_num is not None and etf_flow_num > 0 and (liquidity_pressure is None or liquidity_pressure < 7):
        liquidity = {
            "label": "Likidite",
            "title": "Risk Sermayesi Akıyor",
            "detail": liquidity_detail,
            "badge": "FLOW",
            "class": "signal-long",
        }
    elif (etf_flow_num is not None and etf_flow_num < 0) or (liquidity_pressure is not None and liquidity_pressure >= 7):
        liquidity = {
            "label": "Likidite",
            "title": "Savunmacı Konumlanma",
            "detail": liquidity_detail,
            "badge": "CASH",
            "class": "signal-short",
        }
    else:
        liquidity = {
            "label": "Likidite",
            "title": "Likidite Kararsız",
            "detail": liquidity_detail,
            "badge": "WATCH",
            "class": "signal-neutral",
        }

    if "destek" in orderbook_signal.lower():
        focus = {
            "label": "Odak Seviye",
            "title": "Ortak Destek",
            "detail": orderbook_detail,
            "badge": "SUPPORT",
            "class": "signal-long",
        }
    elif "direnc" in orderbook_signal.lower():
        focus = {
            "label": "Odak Seviye",
            "title": "Ortak Direnc",
            "detail": orderbook_detail,
            "badge": "RESISTANCE",
            "class": "signal-short",
        }
    elif "Diren" in data.get("Wall_Status", "—"):
        focus = {
            "label": "Odak Seviye",
            "title": "Kraken Direnci",
            "detail": f"Şimdi {data.get('BTC_Now', '—')} · Duvar {data.get('Res_Wall', '—')} ({data.get('Res_Vol', '—')})",
            "badge": "RESISTANCE",
            "class": "signal-short",
        }
    elif "Dest" in data.get("Wall_Status", "—"):
        focus = {
            "label": "Odak Seviye",
            "title": "Kraken Destegi",
            "detail": f"Şimdi {data.get('BTC_Now', '—')} · Duvar {data.get('Sup_Wall', '—')} ({data.get('Sup_Vol', '—')})",
            "badge": "SUPPORT",
            "class": "signal-long",
        }
    else:
        focus = {
            "label": "Odak Seviye",
            "title": "Seviye Dengesi",
            "detail": orderbook_detail,
            "badge": data.get("ORDERBOOK_SIGNAL_BADGE", "RANGE"),
            "class": data.get("ORDERBOOK_SIGNAL_CLASS", "signal-neutral"),
        }

    if vix is not None and vix >= 25:
        regime["detail"] = f"{regime['detail']} · Yüksek oynaklık"

    return {
        "regime": regime,
        "positioning": positioning,
        "liquidity": liquidity,
        "focus": focus,
    }

import os, re
import streamlit as st
import requests
import yfinance as yf
from openai import OpenAI
import pandas as pd
import streamlit.components.v1 as components
from dotenv import load_dotenv

load_dotenv()
FRED_API_KEY       = os.getenv("FRED_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

if not OPENROUTER_API_KEY:
    st.error("❌ OPENROUTER_API_KEY eksik!")
    st.stop()

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=OPENROUTER_API_KEY)

st.set_page_config(
    page_title="SA Finance Alpha Terminal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

:root {
    --bg:        #070d1a;
    --bg2:       #0b1425;
    --bg3:       #0f1e35;
    --border:    #1a2d4a;
    --accent:    #00e5ff;
    --accent2:   #ff6b35;
    --green:     #00ff88;
    --red:       #ff3b5c;
    --yellow:    #ffd600;
    --text:      #c8d8e8;
    --muted:     #4a6080;
    --mono:      'Space Mono', monospace;
    --sans:      'Syne', sans-serif;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: var(--sans) !important;
    color: var(--text) !important;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070d1a 0%, #0b1425 100%) !important;
    border-right: 1px solid var(--border) !important;
}

/* Hide streamlit default header */
#MainMenu, footer, header { visibility: hidden; }

/* Custom title */
.terminal-header {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px 0 8px 0;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
}
.terminal-header h1 {
    font-family: var(--sans);
    font-size: 1.6em;
    font-weight: 800;
    color: #fff;
    margin: 0;
    letter-spacing: -0.5px;
}
.terminal-header .badge {
    font-family: var(--mono);
    font-size: 0.65em;
    background: var(--accent);
    color: #000;
    padding: 3px 8px;
    border-radius: 4px;
    font-weight: 700;
}
.status-dot {
    width: 8px; height: 8px;
    background: var(--green);
    border-radius: 50%;
    display: inline-block;
    animation: blink 2s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.3} }

/* ── KATEGORİ BAŞLIKLARI ───────────────────────────────── */
.cat-header {
    font-family: var(--mono);
    font-size: 0.68em;
    font-weight: 700;
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 2.5px;
    padding: 6px 0 10px 0;
    border-bottom: 1px solid var(--border);
    margin: 16px 0 12px 0;
}

/* ── METRİK KARTLARI ───────────────────────────────────── */
.metric-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 14px 16px;
    transition: border-color 0.2s, transform 0.15s;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, var(--card-accent, var(--accent)), transparent);
}
.metric-card:hover {
    border-color: var(--accent);
    transform: translateY(-1px);
}
.metric-label {
    font-family: var(--mono);
    font-size: 0.62em;
    color: var(--muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 4px;
}
.metric-value {
    font-family: var(--mono);
    font-size: 1.15em;
    font-weight: 700;
    color: #fff;
    line-height: 1.2;
}
.metric-delta-pos { color: var(--green); font-size: 0.75em; font-family: var(--mono); margin-top: 2px; }
.metric-delta-neg { color: var(--red);   font-size: 0.75em; font-family: var(--mono); margin-top: 2px; }
.metric-delta-neu { color: var(--muted); font-size: 0.75em; font-family: var(--mono); margin-top: 2px; }

/* ── BTC HEROCard ──────────────────────────────────────── */
.btc-hero {
    background: linear-gradient(135deg, #0b1e38 0%, #0d2848 100%);
    border: 1px solid #1e3d6b;
    border-radius: 14px;
    padding: 24px 28px;
    position: relative;
    overflow: hidden;
}
.btc-hero::after {
    content: '₿';
    position: absolute;
    right: 20px; top: 10px;
    font-size: 6em;
    color: rgba(0,229,255,0.05);
    font-weight: 700;
}
.btc-hero .price {
    font-family: var(--mono);
    font-size: 2.6em;
    font-weight: 700;
    color: #fff;
    line-height: 1;
}
.btc-hero .sub { color: var(--muted); font-size: 0.8em; margin-top: 4px; font-family: var(--mono); }

/* ── SINYAL BADGE'LERİ ─────────────────────────────────── */
.signal-long {
    background: rgba(0,255,136,0.12);
    border: 1px solid var(--green);
    color: var(--green);
    font-family: var(--mono);
    font-size: 0.72em;
    padding: 4px 10px;
    border-radius: 6px;
    display: inline-block;
    font-weight: 700;
}
.signal-short {
    background: rgba(255,59,92,0.12);
    border: 1px solid var(--red);
    color: var(--red);
    font-family: var(--mono);
    font-size: 0.72em;
    padding: 4px 10px;
    border-radius: 6px;
    display: inline-block;
    font-weight: 700;
}
.signal-neutral {
    background: rgba(255,214,0,0.10);
    border: 1px solid var(--yellow);
    color: var(--yellow);
    font-family: var(--mono);
    font-size: 0.72em;
    padding: 4px 10px;
    border-radius: 6px;
    display: inline-block;
    font-weight: 700;
}

/* ── DUVAR GÖSTERGESİ ──────────────────────────────────── */
.wall-bar-container {
    background: var(--bg3);
    border-radius: 8px;
    padding: 14px 16px;
    border: 1px solid var(--border);
    margin-top: 8px;
}
.wall-label { font-family: var(--mono); font-size: 0.65em; color: var(--muted); letter-spacing: 1px; }
.wall-price { font-family: var(--mono); font-size: 1.05em; font-weight: 700; }

/* ── HABER KARTI ───────────────────────────────────────── */
.news-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
    transition: border-color 0.2s;
}
.news-card:hover { border-color: var(--accent2); }
.news-card a { color: #e0eef8; text-decoration: none; font-size: 0.88em; font-family: var(--sans); font-weight: 600; }
.news-card a:hover { color: var(--accent); }
.news-meta { color: var(--muted); font-size: 0.72em; margin-top: 5px; font-family: var(--mono); }

/* ── RAPOR KUTUSU ──────────────────────────────────────── */
.report-box {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px 28px;
    line-height: 1.8;
    font-size: 0.9em;
    font-family: var(--sans);
}

/* ── TABS ──────────────────────────────────────────────── */
[data-testid="stTab"] {
    font-family: var(--mono) !important;
    font-size: 0.78em !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
}

/* ── BUTON ─────────────────────────────────────────────── */
.stButton button {
    background: linear-gradient(135deg, var(--accent), #0099bb) !important;
    color: #000 !important;
    font-family: var(--mono) !important;
    font-weight: 700 !important;
    font-size: 0.8em !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 20px !important;
    letter-spacing: 1px !important;
    transition: opacity 0.2s !important;
    width: 100% !important;
}
.stButton button:hover { opacity: 0.85 !important; }

/* Metric override — Streamlit'in kendi metric bileşeni */
[data-testid="metric-container"] {
    background: var(--bg2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 12px 14px !important;
}
[data-testid="stMetricLabel"] { 
    font-family: var(--mono) !important;
    font-size: 0.62em !important;
    color: var(--muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 1.5px !important;
}
[data-testid="stMetricValue"] {
    font-family: var(--mono) !important;
    font-size: 1.05em !important;
    color: #fff !important;
}
[data-testid="stMetricDelta"] { font-family: var(--mono) !important; font-size: 0.78em !important; }

/* Sidebar text */
[data-testid="stSidebar"] * { font-family: var(--sans) !important; }
[data-testid="stSidebar"] .stMarkdown p { font-size: 0.82em !important; color: var(--muted) !important; }

/* Divider */
hr { border-color: var(--border) !important; margin: 16px 0 !important; }

[data-testid="stAppViewBlockContainer"] {
    max-width: 1480px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

.stApp {
    background:
        radial-gradient(circle at top right, rgba(0,229,255,0.08), transparent 32%),
        radial-gradient(circle at left center, rgba(255,107,53,0.06), transparent 30%),
        linear-gradient(180deg, #060b16 0%, #08111f 100%) !important;
}

.terminal-header {
    justify-content: space-between;
    align-items: flex-end;
    padding: 28px 32px;
    margin: 10px 0 18px 0;
    border: 1px solid rgba(38, 71, 115, 0.9);
    border-radius: 20px;
    background:
        radial-gradient(circle at top right, rgba(0,229,255,0.18), transparent 30%),
        linear-gradient(135deg, rgba(11,20,37,0.98) 0%, rgba(10,29,54,0.96) 100%);
    box-shadow: 0 18px 55px rgba(0,0,0,0.28);
}

.hero-kicker {
    font-family: var(--mono);
    font-size: 0.72em;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 10px;
}

.header-subtitle {
    max-width: 740px;
    margin: 10px 0 0 0;
    color: var(--text);
    opacity: 0.82;
    font-size: 0.95em;
    line-height: 1.7;
}

.header-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: flex-end;
}

.header-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 9px 12px;
    border-radius: 999px;
    border: 1px solid rgba(55, 91, 137, 0.9);
    background: rgba(7, 16, 30, 0.78);
    color: #eff8ff;
    font-family: var(--mono);
    font-size: 0.74em;
}

.overview-card,
.info-panel {
    background: linear-gradient(180deg, rgba(12,20,37,0.95), rgba(10,17,31,0.96));
    border: 1px solid rgba(32, 53, 84, 0.95);
    border-radius: 18px;
    padding: 18px 18px 16px 18px;
    box-shadow: 0 14px 34px rgba(0,0,0,0.18);
}

.overview-card .metric-value {
    font-size: 1.24em;
    margin-top: 8px;
}

.overview-detail {
    margin-top: 10px;
    color: var(--muted);
    font-size: 0.82em;
    line-height: 1.6;
}

.info-panel {
    height: 100%;
    padding: 22px;
}

.panel-kicker {
    font-family: var(--mono);
    font-size: 0.68em;
    color: var(--accent);
    letter-spacing: 1.8px;
    text-transform: uppercase;
}

.panel-title {
    margin-top: 8px;
    color: #ffffff;
    font-size: 1.18em;
    font-weight: 700;
    line-height: 1.3;
}

.panel-copy {
    margin-top: 8px;
    color: var(--muted);
    font-size: 0.83em;
    line-height: 1.6;
}

.panel-list {
    margin-top: 16px;
}

.panel-row {
    display: flex;
    justify-content: space-between;
    gap: 14px;
    align-items: flex-start;
    padding: 11px 0;
    border-bottom: 1px solid rgba(30, 45, 70, 0.92);
}

.panel-row:last-child {
    border-bottom: none;
    padding-bottom: 0;
}

.panel-row span {
    color: var(--muted);
    font-size: 0.8em;
}

.panel-row strong {
    color: #f4fbff;
    font-size: 0.88em;
    text-align: right;
}

.hero-caption {
    margin-top: 14px;
    color: rgba(232, 244, 255, 0.78);
    font-size: 0.84em;
    line-height: 1.7;
}

.section-lead {
    margin: 4px 0 14px 0;
    color: var(--muted);
    font-size: 0.9em;
}

[data-testid="stTabs"] {
    margin-top: 12px;
}

[data-testid="stTab"] {
    background: rgba(10, 18, 31, 0.88) !important;
    border: 1px solid transparent !important;
    border-radius: 999px !important;
    padding: 8px 14px !important;
    margin-right: 6px !important;
}

[data-testid="stTab"][aria-selected="true"] {
    background: rgba(12, 28, 51, 0.98) !important;
    border-color: rgba(35, 72, 116, 0.95) !important;
}

.stButton button,
.stDownloadButton button {
    box-shadow: 0 12px 24px rgba(0, 153, 187, 0.15) !important;
}

@media (max-width: 900px) {
    .terminal-header {
        padding: 22px 20px;
        align-items: flex-start;
    }

    .terminal-header h1 {
        font-size: 1.9em;
    }

    .header-meta {
        justify-content: flex-start;
        margin-top: 16px;
    }

    .panel-row {
        flex-direction: column;
        gap: 6px;
    }

    .panel-row strong {
        text-align: left;
    }
}
</style>
""", unsafe_allow_html=True)

HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}


# ============================================================
#  YARDIMCI: HTML METRİK KARTI
# ============================================================
def mcard(label: str, value: str, delta: str = "", accent_color: str = "--accent"):
    if delta and delta not in ("—", ""):
        try:
            raw = float(delta.replace("%", "").replace(",", ".").strip())
            cls = "metric-delta-pos" if raw >= 0 else "metric-delta-neg"
            arrow = "▲" if raw >= 0 else "▼"
            delta_html = f'<div class="{cls}">{arrow} {delta}</div>'
        except Exception:
            delta_html = f'<div class="metric-delta-neu">{delta}</div>'
    elif delta:
        delta_html = f'<div class="metric-delta-neu">{delta}</div>'
    else:
        delta_html = ""

    return f"""
    <div class="metric-card" style="--card-accent: var({accent_color});">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {delta_html}
    </div>
    """


def render_cards(items, cols=4, accent="--accent"):
    """items = [(label, value, delta), ...]"""
    columns = st.columns(cols)
    for i, item in enumerate(items):
        label = item[0]
        value = item[1] if len(item) > 1 else "—"
        delta = item[2] if len(item) > 2 else ""
        with columns[i % cols]:
            st.markdown(mcard(label, value, delta, accent), unsafe_allow_html=True)


def cat(title: str, icon: str = ""):
    st.markdown(f'<div class="cat-header">{icon}&nbsp; {title}</div>', unsafe_allow_html=True)


def parse_number(value):
    if value in (None, "", "—"):
        return None
    if isinstance(value, (int, float)):
        return float(value)

    raw_text = str(value).strip()
    negative_by_parens = raw_text.startswith("(") and raw_text.endswith(")")
    cleaned = re.sub(r"[^0-9,.\-+]", "", raw_text)
    if not cleaned:
        return None

    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif cleaned.count(",") == 1 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")

    try:
        number = float(cleaned)
        return -abs(number) if negative_by_parens else number
    except Exception:
        return None


def badge_class(text: str):
    text = (text or "").lower()
    if any(word in text for word in ["long", "güçlü", "risk", "destek", "akıyor", "pozitif"]):
        return "signal-long"
    if any(word in text for word in ["short", "baskı", "direnç", "savunmacı", "negatif"]):
        return "signal-short"
    return "signal-neutral"


ETF_FLOW_COLUMNS = ("IBIT", "FBTC", "BITB", "ARKB", "BTCO", "EZBC", "BRRR", "HODL", "BTCW", "GBTC", "BTC", "TOTAL")
ETF_PLACEHOLDERS = {"", "-", "—"}


def format_flow_millions(value):
    number = parse_number(value)
    if number is None:
        return "—"
    sign = "+" if number > 0 else ""
    return f"{sign}{number:.1f}M $"


def build_etf_flow_df(data):
    return pd.DataFrame(
        [
            {
                "ETF": "Total" if symbol == "TOTAL" else symbol,
                "Netflow (US$m)": data.get(f"ETF_FLOW_{symbol}", "—"),
            }
            for symbol in ETF_FLOW_COLUMNS
        ]
    )


def fetch_text_without_env_proxy(url, timeout=20):
    session = requests.Session()
    session.trust_env = False
    request_headers = dict(HEADERS)
    request_headers["Accept"] = "text/plain, text/markdown, */*"
    response = session.get(url, headers=request_headers, timeout=timeout)
    response.raise_for_status()
    return response.text


def fetch_json_without_env_proxy(url, timeout=20):
    session = requests.Session()
    session.trust_env = False
    response = session.get(url, headers=HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.json()


def parse_latest_etf_flow_row(flow_text):
    flow_rows = [
        line.strip()
        for line in flow_text.splitlines()
        if re.match(r"^\|\s*\d{2}\s+[A-Za-z]{3}\s+\d{4}\s*\|", line.strip())
    ]
    if not flow_rows:
        return None

    for row in reversed(flow_rows):
        parts = [part.strip() for part in row.split("|")[1:-1]]
        if len(parts) < len(ETF_FLOW_COLUMNS) + 1:
            continue

        date_text = parts[0]
        values = parts[1:1 + len(ETF_FLOW_COLUMNS)]
        non_placeholder_count = sum(value not in ETF_PLACEHOLDERS for value in values[:-1])
        if non_placeholder_count == 0:
            continue

        return date_text, values

    return None


def extract_wall_levels(bids, asks, noise=250, bucket_size=100):
    if not bids or not asks:
        raise ValueError("order book is empty")

    current_price = bids[0][0]
    max_distance = current_price * 0.08
    sane_bids = [(p, q) for p, q in bids if 0 < p <= current_price and (current_price - p) <= max_distance] or bids
    sane_asks = [(p, q) for p, q in asks if p >= current_price and (p - current_price) <= max_distance] or asks

    filtered_bids = [(p, q) for p, q in sane_bids if p < current_price - noise] or sane_bids[len(sane_bids) // 2 :]
    filtered_asks = [(p, q) for p, q in sane_asks if p > current_price + noise] or sane_asks[len(sane_asks) // 2 :]

    def strongest_bucket(levels, bucket_fn):
        buckets = {}
        for price, qty in levels:
            bucket_key = bucket_fn(price)
            buckets[bucket_key] = buckets.get(bucket_key, 0.0) + qty
        return max(buckets.items(), key=lambda item: item[1])

    support_price, support_volume = strongest_bucket(filtered_bids, lambda price: int(price / bucket_size) * bucket_size)
    resistance_price, resistance_volume = strongest_bucket(filtered_asks, lambda price: int((price / bucket_size) + 1) * bucket_size)

    distance_support = current_price - support_price
    distance_resistance = resistance_price - current_price
    if distance_resistance < distance_support:
        status = "🔴 Dirence Yakın"
    elif distance_support < distance_resistance:
        status = "🟢 Desteğe Yakın"
    else:
        status = "⚖️ Kanal Ortası"

    return {
        "current_price": current_price,
        "support_price": support_price,
        "support_volume": support_volume,
        "resistance_price": resistance_price,
        "resistance_volume": resistance_volume,
        "status": status,
    }


def wall_field(prefix, field):
    return f"{prefix}_{field}" if prefix else field


def format_btc_volume(volume):
    if volume is None:
        return "—"
    if volume >= 10:
        return f"{volume:,.0f} BTC"
    if volume >= 1:
        return f"{volume:,.1f} BTC"
    return f"{volume:,.3f} BTC"


def save_wall_levels(target, prefix, levels):
    target[wall_field(prefix, "Sup_Wall")] = f"${levels['support_price']:,}"
    target[wall_field(prefix, "Sup_Vol")] = format_btc_volume(levels["support_volume"])
    target[wall_field(prefix, "Res_Wall")] = f"${levels['resistance_price']:,}"
    target[wall_field(prefix, "Res_Vol")] = format_btc_volume(levels["resistance_volume"])
    target[wall_field(prefix, "Wall_Status")] = levels["status"]
    target[wall_field(prefix, "BTC_Now")] = f"${levels['current_price']:,.0f}"


def clear_wall_levels(target, prefix):
    target[wall_field(prefix, "Sup_Wall")] = "—"
    target[wall_field(prefix, "Sup_Vol")] = "—"
    target[wall_field(prefix, "Res_Wall")] = "—"
    target[wall_field(prefix, "Res_Vol")] = "—"
    target[wall_field(prefix, "Wall_Status")] = "—"
    target[wall_field(prefix, "BTC_Now")] = "—"


def build_orderbook_signal(data):
    exchanges = [
        ("Kraken", ""),
        ("OKX", "OKX"),
        ("KuCoin", "KUCOIN"),
        ("Gate.io", "GATE"),
        ("Coinbase", "COINBASE"),
    ]
    snapshots = []
    for name, prefix in exchanges:
        snapshots.append(
            {
                "name": name,
                "status": data.get(wall_field(prefix, "Wall_Status"), "—"),
                "support": data.get(wall_field(prefix, "Sup_Wall"), "—"),
                "resistance": data.get(wall_field(prefix, "Res_Wall"), "—"),
            }
        )

    support_names = [item["name"] for item in snapshots if "Dest" in item["status"]]
    resistance_names = [item["name"] for item in snapshots if "Diren" in item["status"]]

    if len(support_names) >= 2 and len(support_names) > len(resistance_names):
        detail = " · ".join(
            f"{item['name']} {item['support']}"
            for item in snapshots
            if item["name"] in support_names and item["support"] != "—"
        )
        return {
            "title": "Ortak destek guclu",
            "detail": detail or "Coklu borsa destegi goruluyor.",
            "badge": "SUPPORT",
            "class": "signal-long",
        }

    if len(resistance_names) >= 2 and len(resistance_names) > len(support_names):
        detail = " · ".join(
            f"{item['name']} {item['resistance']}"
            for item in snapshots
            if item["name"] in resistance_names and item["resistance"] != "—"
        )
        return {
            "title": "Ortak direnc guclu",
            "detail": detail or "Coklu borsa direnci goruluyor.",
            "badge": "RESISTANCE",
            "class": "signal-short",
        }

    detail = " · ".join(
        f"{item['name']} {item['support']} / {item['resistance']}"
        for item in snapshots
        if item["support"] != "—" or item["resistance"] != "—"
    )
    return {
        "title": "Seviyeler karisik",
        "detail": detail or "Coklu borsa teyidi henuz yok.",
        "badge": "MIXED",
        "class": "signal-neutral",
    }


@st.cache_data(ttl=30)
def fetch_live_usdt_d():
    try:
        tv_text = fetch_text_without_env_proxy(
            "https://r.jina.ai/http://www.tradingview.com/symbols/USDT.D/?exchange=CRYPTOCAP",
            timeout=20,
        )
        match = re.search(r"Market open\s+([0-9]+(?:\.[0-9]+)?)%R", tv_text)
        if not match:
            match = re.search(r"USDT\.D Market open\s+([0-9]+(?:\.[0-9]+)?)\sR%", tv_text)
        if not match:
            match = re.search(r"Market closed\s+([0-9]+(?:\.[0-9]+)?)%R", tv_text)
        if not match:
            raise ValueError("tradingview usdt.d not found")
        return {
            "USDT_D": f"%{float(match.group(1)):.2f}",
            "USDT_D_SOURCE": "TradingView",
        }
    except:
        try:
            cg_g = fetch_json_without_env_proxy(
                "https://api.coingecko.com/api/v3/global",
                timeout=6,
            )["data"]
            return {
                "USDT_D": f"%{cg_g['market_cap_percentage']['usdt']:.2f}",
                "USDT_D_SOURCE": "CoinGecko",
            }
        except:
            try:
                cg2 = fetch_json_without_env_proxy(
                    "https://api.coinpaprika.com/v1/global",
                    timeout=6,
                )
                total_mc = cg2["market_cap_usd"]
                ur = fetch_json_without_env_proxy(
                    "https://api.coinpaprika.com/v1/tickers/usdt-tether",
                    timeout=6,
                )
                return {
                    "USDT_D": f"%{ur['quotes']['USD']['market_cap']/total_mc*100:.2f}",
                    "USDT_D_SOURCE": "Coinpaprika",
                }
            except:
                return {"USDT_D": "—", "USDT_D_SOURCE": "—"}


def format_market_cap_short(value):
    if value is None:
        return "—"
    if value >= 1e12:
        return f"${value/1e12:.2f}T"
    if value >= 1e9:
        return f"${value/1e9:.1f}B"
    if value >= 1e6:
        return f"${value/1e6:.1f}M"
    return f"${value:,.0f}"


def parse_tradingview_market_cap(text):
    match = re.search(r"Market open\s+([0-9]+(?:\.[0-9]+)?)\s*([TBM])\s*R USD", text)
    if not match:
        match = re.search(r"Market closed\s+([0-9]+(?:\.[0-9]+)?)\s*([TBM])\s*R USD", text)
    if not match:
        raise ValueError("tradingview market cap not found")

    value = float(match.group(1))
    unit = match.group(2)
    multiplier = {"T": 1e12, "B": 1e9, "M": 1e6}[unit]
    return value * multiplier


@st.cache_data(ttl=30)
def fetch_tradingview_market_cap_segments():
    symbols = {
        "TOTAL": "https://r.jina.ai/http://www.tradingview.com/symbols/TOTAL/",
        "TOTAL2": "https://r.jina.ai/http://www.tradingview.com/symbols/TOTAL2/",
        "TOTAL3": "https://r.jina.ai/http://www.tradingview.com/symbols/TOTAL3/",
        "OTHERS": "https://r.jina.ai/http://www.tradingview.com/symbols/OTHERS/?exchange=CRYPTOCAP",
    }

    parsed = {}
    for key, url in symbols.items():
        parsed[key] = parse_tradingview_market_cap(fetch_text_without_env_proxy(url, timeout=20))

    return {
        "TOTAL_CAP": format_market_cap_short(parsed["TOTAL"]),
        "TOTAL2_CAP": format_market_cap_short(parsed["TOTAL2"]),
        "TOTAL3_CAP": format_market_cap_short(parsed["TOTAL3"]),
        "OTHERS_CAP": format_market_cap_short(parsed["OTHERS"]),
        "TOTAL_CAP_NUM": parsed["TOTAL"],
        "TOTAL2_CAP_NUM": parsed["TOTAL2"],
        "TOTAL3_CAP_NUM": parsed["TOTAL3"],
        "OTHERS_CAP_NUM": parsed["OTHERS"],
        "TOTAL_CAP_SOURCE": "TradingView",
    }


@st.cache_data(ttl=30)
def fetch_live_market_cap_segments():
    try:
        return fetch_tradingview_market_cap_segments()
    except:
        try:
            global_data = fetch_json_without_env_proxy(
                "https://api.coingecko.com/api/v3/global",
                timeout=6,
            )["data"]
            total_cap_num = global_data["total_market_cap"]["usd"]
            btc_d = global_data["market_cap_percentage"].get("btc", 0)
            eth_d = global_data["market_cap_percentage"].get("eth", 0)

            top10 = fetch_json_without_env_proxy(
                "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=10&page=1&sparkline=false",
                timeout=8,
            )
            top10_sum = sum(item.get("market_cap") or 0 for item in top10)

            total2_num = total_cap_num * (1 - btc_d / 100)
            total3_num = total_cap_num * (1 - (btc_d + eth_d) / 100)
            others_num = max(total_cap_num - top10_sum, 0)

            return {
                "TOTAL_CAP": format_market_cap_short(total_cap_num),
                "TOTAL2_CAP": format_market_cap_short(total2_num),
                "TOTAL3_CAP": format_market_cap_short(total3_num),
                "OTHERS_CAP": format_market_cap_short(others_num),
                "TOTAL_CAP_NUM": total_cap_num,
                "TOTAL2_CAP_NUM": total2_num,
                "TOTAL3_CAP_NUM": total3_num,
                "OTHERS_CAP_NUM": others_num,
                "TOTAL_CAP_SOURCE": "CoinGecko fallback",
            }
        except:
            return {
                "TOTAL_CAP": "—",
                "TOTAL2_CAP": "—",
                "TOTAL3_CAP": "—",
                "OTHERS_CAP": "—",
                "TOTAL_CAP_NUM": None,
                "TOTAL2_CAP_NUM": None,
                "TOTAL3_CAP_NUM": None,
                "OTHERS_CAP_NUM": None,
                "TOTAL_CAP_SOURCE": "—",
            }


def render_info_panel(kicker: str, title: str, rows, badge_text: str = "", badge_kind: str = "signal-neutral", copy: str = ""):
    rows_html = "".join(
        f"<div class='panel-row'><span>{label}</span><strong>{value}</strong></div>"
        for label, value in rows
    )
    copy_html = f"<div class='panel-copy'>{copy}</div>" if copy else ""
    badge_html = f"<div style='margin-top:16px'><span class='{badge_kind}'>{badge_text}</span></div>" if badge_text else ""

    st.markdown(
        f"""
        <div class="info-panel">
            <div class="panel-kicker">{kicker}</div>
            <div class="panel-title">{title}</div>
            {copy_html}
            <div class="panel-list">{rows_html}</div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


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


def render_market_brief(brief):
    cols = st.columns(4)
    for col, card in zip(cols, brief.values()):
        with col:
            st.markdown(
                f"""
                <div class="overview-card">
                    <div class="metric-label">{card['label']}</div>
                    <div class="metric-value">{card['title']}</div>
                    <div class="overview-detail">{card['detail']}</div>
                    <div style="margin-top:14px"><span class="{card['class']}">{card['badge']}</span></div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ============================================================
#  VERİ MOTORU — cache'li (3dk)
# ============================================================
@st.cache_data(ttl=180)
def veri_motoru():
    v = {}

    # 1. BTC
    try:
        r = requests.get("https://api.coinpaprika.com/v1/tickers/btc-bitcoin",
                         headers=HEADERS, timeout=8).json()
        q = r["quotes"]["USD"]
        v["BTC_P"]   = f"${q['price']:,.0f}"
        v["BTC_C"]   = f"{q['percent_change_24h']:.2f}%"
        v["BTC_7D"]  = f"{q['percent_change_7d']:.2f}%"
        v["Vol_24h"] = f"${q['volume_24h']:,.0f}"
        v["BTC_MCap"]= f"${q['market_cap']/1e9:.0f}B"
    except:
        v["BTC_P"]="—"; v["BTC_C"]="—"; v["BTC_7D"]="—"; v["Vol_24h"]="—"; v["BTC_MCap"]="—"

    # 2. Altcoinler
    alt_ids = {
        "ETH":"eth-ethereum","SOL":"sol-solana","BNB":"bnb-binance-coin",
        "XRP":"xrp-xrp","ADA":"ada-cardano","AVAX":"avax-avalanche",
        "DOT":"dot-polkadot","LINK":"link-chainlink"
    }
    for sym, cid in alt_ids.items():
        try:
            r = requests.get(f"https://api.coinpaprika.com/v1/tickers/{cid}",
                             headers=HEADERS, timeout=6).json()
            q = r["quotes"]["USD"]
            v[f"{sym}_P"]  = f"${q['price']:,.2f}"
            v[f"{sym}_C"]  = f"{q['percent_change_24h']:.2f}%"
            v[f"{sym}_7D"] = f"{q['percent_change_7d']:.2f}%"
        except:
            v[f"{sym}_P"]="—"; v[f"{sym}_C"]="—"; v[f"{sym}_7D"]="—"

    # 3. Global piyasa (Coinpaprika)
    try:
        g = fetch_json_without_env_proxy("https://api.coinpaprika.com/v1/global", timeout=6)
        v["Total_MCap_Num"] = g["market_cap_usd"]
        v["Dom"]        = f"%{g['bitcoin_dominance_percentage']:.2f}"
        v["Total_MCap"] = f"${g['market_cap_usd']/1e12:.2f}T"
        v["Total_Vol"]  = f"${g['volume_24h_usd']/1e9:.1f}B"
    except:
        v["Dom"]="—"; v["Total_MCap"]="—"; v["Total_Vol"]="—"; v["Total_MCap_Num"]=None

    # ETH dominance
    try:
        eth = requests.get("https://api.coinpaprika.com/v1/tickers/eth-ethereum",
                           headers=HEADERS, timeout=5).json()
        dom_val = float(v["Dom"].replace("%","")) if v["Dom"] != "—" else 0
        btc_mc  = float(v["BTC_MCap"].replace("$","").replace("B",""))*1e9 if v["BTC_MCap"] != "—" else 0
        total_mc= btc_mc / (dom_val/100) if dom_val > 0 else 0
        if total_mc > 0:
            v["ETH_Dom"] = f"%{float(eth['quotes']['USD']['market_cap'])/total_mc*100:.2f}"
        else:
            v["ETH_Dom"] = "—"
    except:
        v["ETH_Dom"] = "—"

    # 4. BTC ETF fiyatlari (yFinance) + gunluk netflow (Farside)
    for sym in ["IBIT","FBTC","BITB","ARKB"]:
        try:
            df   = yf.Ticker(sym).history(period="10d")
            if df.empty: raise ValueError
            curr = df["Close"].iloc[-1]; prev = df["Close"].iloc[-2]
            v[f"{sym}_P"]   = f"${curr:.2f}"
            v[f"{sym}_C"]   = f"{(curr-prev)/prev*100:.2f}%"
            v[f"{sym}_Vol"] = f"{int(df['Volume'].iloc[-1]):,}"
        except:
            v[f"{sym}_P"]="—"; v[f"{sym}_C"]="—"; v[f"{sym}_Vol"]="—"

    for symbol in ETF_FLOW_COLUMNS:
        v[f"ETF_FLOW_{symbol}"] = "—"
    v["ETF_FLOW_DATE"] = "—"

    v["ETF_FLOW_SOURCE"] = "—"

    for flow_url in [
        "https://r.jina.ai/http://farside.co.uk/bitcoin-etf-flow-all-data/",
        "https://r.jina.ai/http://farside.co.uk/btc/",
        "https://farside.co.uk/bitcoin-etf-flow-all-data/",
    ]:
        try:
            flow_text = fetch_text_without_env_proxy(flow_url, timeout=20)
            latest_row = parse_latest_etf_flow_row(flow_text)
            if not latest_row:
                continue

            v["ETF_FLOW_DATE"] = latest_row[0]
            for symbol, raw_value in zip(ETF_FLOW_COLUMNS, latest_row[1]):
                v[f"ETF_FLOW_{symbol}"] = format_flow_millions(raw_value)
            v["ETF_FLOW_SOURCE"] = "Farside"
            break
        except:
            pass

    # 5. Hisse endeksleri
    endeksler = {
        "SP500":"^GSPC","NASDAQ":"^IXIC","DOW":"^DJI","DAX":"^GDAXI",
        "FTSE":"^FTSE","NIKKEI":"^N225","HSI":"^HSI","BIST100":"XU100.IS","VIX":"^VIX"
    }
    for key, sym in endeksler.items():
        try:
            df   = yf.Ticker(sym).history(period="5d")
            curr = df["Close"].iloc[-1]; prev = df["Close"].iloc[-2]
            v[key]          = f"{curr:,.2f}"
            v[f"{key}_C"]   = f"{(curr-prev)/prev*100:.2f}%"
        except:
            v[key]="—"; v[f"{key}_C"]="—"

    # 6. Emtialar
    emtialar = {"GOLD":"GC=F","SILVER":"SI=F","OIL":"CL=F","NATGAS":"NG=F","COPPER":"HG=F","WHEAT":"ZW=F"}
    for key, sym in emtialar.items():
        try:
            df   = yf.Ticker(sym).history(period="5d")
            curr = df["Close"].iloc[-1]; prev = df["Close"].iloc[-2]
            v[key]        = f"${curr:,.2f}"
            v[f"{key}_C"] = f"{(curr-prev)/prev*100:.2f}%"
        except:
            v[key]="—"; v[f"{key}_C"]="—"

    # 7. Forex + makro faiz
    forex = {
        "DXY":"DX-Y.NYB","EURUSD":"EURUSD=X","GBPUSD":"GBPUSD=X",
        "USDJPY":"JPY=X","USDTRY":"TRY=X","USDCHF":"CHF=X",
        "AUDUSD":"AUDUSD=X","US10Y":"^TNX"
    }
    for key, sym in forex.items():
        try:
            df   = yf.Ticker(sym).history(period="5d")
            curr = df["Close"].iloc[-1]; prev = df["Close"].iloc[-2]
            v[key]        = f"{curr:.4f}"
            v[f"{key}_C"] = f"{(curr-prev)/prev*100:.2f}%"
        except:
            v[key]="—"; v[f"{key}_C"]="—"

    # 8. BTC Korelasyon (30 gün)
    try:
        cd = yf.download(["BTC-USD","^GSPC","GC=F"], period="30d", progress=False)["Close"]
        cm = cd.corr()
        v["Corr_SP500"] = round(cm.loc["BTC-USD","^GSPC"], 2)
        v["Corr_Gold"]  = round(cm.loc["BTC-USD","GC=F"],  2)
    except:
        v["Corr_SP500"]="—"; v["Corr_Gold"]="—"

    # 9. Balina duvarları (Kraken + OKX + KuCoin + Gate.io + Coinbase)
    try:
        ob = fetch_json_without_env_proxy("https://api.kraken.com/0/public/Depth?pair=XBTUSD&count=500", timeout=8)
        pk  = list(ob["result"].keys())[0]
        bids= [(float(p),float(q)) for p,q,_ in ob["result"][pk]["bids"]]
        asks= [(float(p),float(q)) for p,q,_ in ob["result"][pk]["asks"]]
        kraken_levels = extract_wall_levels(bids, asks)
        save_wall_levels(v, "", kraken_levels)
    except:
        clear_wall_levels(v, "")

    try:
        okx = fetch_json_without_env_proxy("https://www.okx.com/api/v5/market/books?instId=BTC-USDT&sz=400", timeout=8)
        okx_book = okx["data"][0]
        bids = [(float(p), float(q)) for p, q, *_ in okx_book["bids"]]
        asks = [(float(p), float(q)) for p, q, *_ in okx_book["asks"]]
        okx_levels = extract_wall_levels(bids, asks)
        save_wall_levels(v, "OKX", okx_levels)
    except:
        clear_wall_levels(v, "OKX")

    try:
        kucoin = fetch_json_without_env_proxy("https://api.kucoin.com/api/v1/market/orderbook/level2_100?symbol=BTC-USDT", timeout=8)
        kucoin_book = kucoin["data"]
        bids = [(float(p), float(q)) for p, q, *_ in kucoin_book["bids"]]
        asks = [(float(p), float(q)) for p, q, *_ in kucoin_book["asks"]]
        kucoin_levels = extract_wall_levels(bids, asks)
        save_wall_levels(v, "KUCOIN", kucoin_levels)
    except:
        clear_wall_levels(v, "KUCOIN")

    try:
        gate = fetch_json_without_env_proxy("https://api.gateio.ws/api/v4/spot/order_book?currency_pair=BTC_USDT&limit=200&with_id=true", timeout=8)
        bids = [(float(p), float(q)) for p, q, *_ in gate["bids"]]
        asks = [(float(p), float(q)) for p, q, *_ in gate["asks"]]
        gate_levels = extract_wall_levels(bids, asks)
        save_wall_levels(v, "GATE", gate_levels)
    except:
        clear_wall_levels(v, "GATE")

    try:
        coinbase = fetch_json_without_env_proxy("https://api.exchange.coinbase.com/products/BTC-USD/book?level=2", timeout=8)
        bids = [(float(p), float(q)) for p, q, *_ in coinbase["bids"]]
        asks = [(float(p), float(q)) for p, q, *_ in coinbase["asks"]]
        coinbase_levels = extract_wall_levels(bids, asks)
        save_wall_levels(v, "COINBASE", coinbase_levels)
    except:
        clear_wall_levels(v, "COINBASE")

    orderbook_signal = build_orderbook_signal(v)
    v["ORDERBOOK_SIGNAL"] = orderbook_signal["title"]
    v["ORDERBOOK_SIGNAL_DETAIL"] = orderbook_signal["detail"]
    v["ORDERBOOK_SIGNAL_BADGE"] = orderbook_signal["badge"]
    v["ORDERBOOK_SIGNAL_CLASS"] = orderbook_signal["class"]
    v["ORDERBOOK_SOURCES"] = "Kraken · OKX · KuCoin · Gate.io · Coinbase"

    # 10. Stablecoin (DeFiLlama)
    try:
        sc = fetch_json_without_env_proxy(
            "https://stablecoins.llama.fi/stablecoins?includePrices=true",
            timeout=8,
        )["peggedAssets"]
        total = sum(c.get("circulating",{}).get("peggedUSD",0) for c in sc)
        def gcap(sym):
            c = next((x for x in sc if x["symbol"].upper()==sym), None)
            return c["circulating"]["peggedUSD"] if c else 0
        usdt_c = gcap("USDT"); usdc_c = gcap("USDC"); dai_c = gcap("DAI")
        v["Total_Stable_Num"] = total
        v["Total_Stable"]   = f"${total/1e9:.1f}B"
        v["USDT_MCap"]      = f"${usdt_c/1e9:.1f}B"
        v["USDC_MCap"]      = f"${usdc_c/1e9:.1f}B"
        v["DAI_MCap"]       = f"${dai_c/1e9:.1f}B"
        v["USDT_Dom_Stable"]= f"%{usdt_c/total*100:.1f}" if total > 0 else "—"
        v["STABLE_C_D"]     = f"%{total/v['Total_MCap_Num']*100:.2f}" if v.get("Total_MCap_Num") else "—"
    except:
        v["Total_Stable"]="—"; v["USDT_MCap"]="—"; v["USDC_MCap"]="—"
        v["DAI_MCap"]="—"; v["USDT_Dom_Stable"]="—"; v["Total_Stable_Num"]=None; v["STABLE_C_D"]="—"

    # USDT.D — canli market cap yuzdesi, ana cache'ten ayri hizda yenilenir
    v.update(fetch_live_usdt_d())

    # OI + FR + L/S (placeholder — turev_cek() ile doldurulacak)
    v["OI"]="—"; v["FR"]="—"; v["Taker"]="—"
    v["LS_Ratio"]="—"; v["Long_Pct"]="—"; v["Short_Pct"]="—"; v["LS_Signal"]="—"

    # 11. FRED (M2, FED)
    try:
        m2 = requests.get(
            f"https://api.stlouisfed.org/fred/series/observations?series_id=M2SL"
            f"&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=13",
            timeout=6).json()["observations"]
        v["M2"] = f"%{(float(m2[0]['value'])-float(m2[12]['value']))/float(m2[12]['value'])*100:.2f}"
    except:
        v["M2"] = "—"
    try:
        fed = requests.get(
            f"https://api.stlouisfed.org/fred/series/observations?series_id=FEDFUNDS"
            f"&api_key={FRED_API_KEY}&file_type=json&sort_order=desc&limit=1",
            timeout=6).json()["observations"]
        v["FED"] = f"%{fed[0]['value']}"
    except:
        v["FED"] = "—"

    # 12. On-chain (Blockchain.info)
    try:
        s = requests.get("https://api.blockchain.info/stats", timeout=5).json()
        v["Hash"] = f"{s['hash_rate']/1e9:.2f} EH/s"
        v["Active"] = f"{s['n_blocks_mined']*2100:,}"
    except:
        v["Hash"]="—"; v["Active"]="—"

    # 13. Korku/Açgözlülük
    try:
        fng = requests.get("https://api.alternative.me/fng/?limit=2", timeout=5).json()["data"]
        v["FNG"]      = f"{fng[0]['value']} ({fng[0]['value_classification']})"
        v["FNG_PREV"] = f"{fng[1]['value']} ({fng[1]['value_classification']})"
        v["FNG_NUM"]  = int(fng[0]["value"])
    except:
        v["FNG"]="—"; v["FNG_PREV"]="—"; v["FNG_NUM"]=0

    # 14. Haberler (CoinDesk RSS)
    try:
        rss    = requests.get("https://www.coindesk.com/arc/outboundfeeds/rss/",
                              headers=HEADERS, timeout=8).text
        titles = re.findall(r"<title><!\[CDATA\[(.*?)\]\]></title>", rss)[1:11]
        links  = re.findall(r"<link>(https://www\.coindesk\.com.*?)</link>", rss)[:10]
        dates  = re.findall(r"<pubDate>(.*?)</pubDate>", rss)[:10]
        v["NEWS"] = [
            {"title": t, "url": links[i] if i<len(links) else "#",
             "source": "CoinDesk", "time": dates[i][:16] if i<len(dates) else ""}
            for i, t in enumerate(titles)
        ]
    except:
        try:
            nr = requests.get(
                "https://min-api.cryptocompare.com/data/v2/news/?lang=EN&sortOrder=latest&limit=10",
                headers=HEADERS, timeout=6).json()
            v["NEWS"] = [
                {"title": n["title"], "url": n["url"], "source": n["source_info"]["name"],
                 "time": pd.Timestamp(n["published_on"], unit="s").strftime("%d %b %H:%M")}
                for n in nr["Data"][:10]
            ]
        except:
            v["NEWS"] = []

    return v


# ============================================================
#  TÜREV VERİLERİ — cache'siz, her yüklemede taze
# ============================================================
def turev_cek():
    t = {}

    # OI + FR (OKX)
    try:
        fr_r = requests.get(
            "https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP",
            headers=HEADERS, timeout=6).json()
        t["FR"] = f"%{float(fr_r['data'][0]['fundingRate'])*100:.4f}"
    except:
        t["FR"] = "—"
    try:
        oi_r = requests.get(
            "https://www.okx.com/api/v5/public/open-interest?instType=SWAP&instId=BTC-USDT-SWAP",
            headers=HEADERS, timeout=6).json()
        t["OI"] = f"{float(oi_r['data'][0]['oi']):,.0f} BTC"
    except:
        t["OI"] = "—"

    # Taker B/S (OKX)
    try:
        tk = requests.get(
            "https://www.okx.com/api/v5/rubik/stat/taker-volume?ccy=BTC&instType=contracts&period=1H",
            headers=HEADERS, timeout=6).json()
        bv = float(tk["data"][0][1]); sv = float(tk["data"][0][2])
        t["Taker"] = f"{bv/sv:.3f}" if sv > 0 else "1.000"
    except:
        t["Taker"] = "1.000"

    # L/S Oranı
    ls_done = False
    for url in [
        "https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio-contract-top-trader?instId=BTC-USDT-SWAP&period=1H",
        "https://www.okx.com/api/v5/rubik/stat/contracts/long-short-account-ratio?ccy=BTC&period=1H"
    ]:
        if ls_done: break
        try:
            r = requests.get(url, headers=HEADERS, timeout=6).json()
            d = r.get("data", [])
            if not d: continue
            d0  = d[0]
            if isinstance(d0, dict) and "longRatio" in d0:
                lp    = float(d0["longRatio"])*100
                sp    = float(d0["shortRatio"])*100
                ratio = lp/sp if sp > 0 else 1
            else:
                ratio = float(d0[1]) if isinstance(d0, list) else 1
                lp    = ratio/(1+ratio)*100
                sp    = 100-lp
            t["LS_Ratio"]  = f"{ratio:.3f}"
            t["Long_Pct"]  = f"%{lp:.1f}"
            t["Short_Pct"] = f"%{sp:.1f}"
            t["LS_Signal"] = "🟢 Long Ağırlıklı" if ratio > 1 else "🔴 Short Ağırlıklı"
            ls_done = True
        except: pass

    if not ls_done:
        try:
            gate = requests.get(
                "https://api.gateio.ws/api/v4/futures/usdt/contract_stats?contract=BTC_USDT&interval=1h&limit=1",
                headers=HEADERS, timeout=6).json()
            lp    = float(gate[0].get("lsr_taker",1))
            lp_pct= lp/(1+lp)*100
            t["LS_Ratio"]  = f"{lp:.3f}"
            t["Long_Pct"]  = f"%{lp_pct:.1f}"
            t["Short_Pct"] = f"%{100-lp_pct:.1f}"
            t["LS_Signal"] = "🟢 Long Ağırlıklı" if lp > 1 else "🔴 Short Ağırlıklı"
            ls_done = True
        except: pass

    if not ls_done:
        t["LS_Ratio"]="—"; t["Long_Pct"]="—"; t["Short_Pct"]="—"; t["LS_Signal"]="—"

    return t


# ============================================================
#  SAYFA YÜKLEMESİ
# ============================================================
son_guncelleme = pd.Timestamp.now(tz="Europe/Istanbul").strftime("%d.%m.%Y %H:%M:%S")
with st.spinner("Piyasa verileri ve türev akışı yükleniyor..."):
    data = veri_motoru()
    data.update(turev_cek())
    data.update(fetch_live_usdt_d())
    data.update(fetch_live_market_cap_segments())
    if data.get("Total_Stable_Num") and data.get("TOTAL_CAP_NUM"):
        data["STABLE_C_D"] = f"%{data['Total_Stable_Num']/data['TOTAL_CAP_NUM']*100:.2f}"

brief = build_market_brief(data)

# Header
st.markdown(
    f"""
    <div class="terminal-header">
        <div>
            <div class="hero-kicker">Digital Asset Intelligence</div>
            <h1>⚡ SA Finance Alpha Terminal</h1>
            <div class="header-subtitle">
                Kripto, makro ve likidite verilerini tek ekranda toplayan daha net bir karar paneli.
                Önce kısa özeti gör, sonra sekmelerde detaya in.
            </div>
        </div>
        <div class="header-meta">
            <span class="header-pill"><span class="status-dot"></span> Canlı veri akışı</span>
            <span class="header-pill">İstanbul · {son_guncelleme}</span>
            <span class="badge">v18.0</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "<div class='section-lead'>Bugünün en kritik sinyallerini öne çıkaran kısa özet kartları.</div>",
    unsafe_allow_html=True,
)
render_market_brief(brief)

# Sidebar
with st.sidebar:
    st.markdown("### 🛰️ Kontrol Merkezi")
    st.caption(f"⏱️ Son güncelleme: {son_guncelleme}")
    st.divider()

    if st.button("🔄 Verileri Yenile", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    df_exp = pd.DataFrame([(k, v) for k, v in data.items() if k != "NEWS"], columns=["Metrik", "Değer"])
    csv = df_exp.to_csv(index=False, sep=";").encode("utf-8-sig")
    st.download_button(
        "💾 CSV İndir",
        csv,
        file_name=f"AlphaTerminal_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.divider()
    render_info_panel(
        "Quick Pulse",
        "Bugünün Nabzı",
        [
            ("BTC fiyat", data.get("BTC_P", "—")),
            ("Korku / Açgözlülük", data.get("FNG", "—")),
            ("Funding", data.get("FR", "—")),
            ("VIX", data.get("VIX", "—")),
        ],
        badge_text=brief["regime"]["title"],
        badge_kind=brief["regime"]["class"],
        copy="Yönü anlamak için fiyat, duygu ve volatilite aynı blokta toplandı.",
    )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    render_info_panel(
        "Watchlist",
        "İzlenecek Seviyeler",
        [
            ("Order book sinyali", data.get("ORDERBOOK_SIGNAL", "—")),
            ("Kraken ana seviye", f"{data.get('Sup_Wall', '—')} / {data.get('Res_Wall', '—')}"),
            ("Günlük ETF Netflow", f"{data.get('ETF_FLOW_TOTAL', '—')} · {data.get('ETF_FLOW_DATE', '—')}"),
            ("USD/TRY", data.get("USDTRY", "—")),
        ],
        badge_text=brief["focus"]["badge"],
        badge_kind=brief["focus"]["class"],
        copy="Coklu borsa order book ozeti ile kurumsal akis ayni izleme panelinde toplandi.",
    )

    st.divider()
    st.markdown("""
**Veri Kaynakları:**  
`Coinpaprika` · `Kraken` · `OKX` · `KuCoin` · `Gate.io` · `Coinbase`  
`DeFiLlama` · `yFinance` · `TradingView`  
`FRED` · `CoinDesk`

**Model:** `Gemini 2.5 Flash`  
**Cache:** 3 dk | Türev: Canlı
""")

# Tab yapısı
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "₿  BİTCOİN & KRİPTO",
    "🌍  MAKRO & PİYASALAR",
    "📊  GRAFİK & RAPOR",
    "📰  HABERLER",
    "⚙️  TÜM METRİKLER"
])


# ── TAB 1: BİTCOİN & KRİPTO ─────────────────────────────────
with tab1:

    btc_c = data.get("BTC_C", "")
    btc_num = parse_number(btc_c)
    btc_color = "var(--green)" if btc_num is not None and btc_num >= 0 else ("var(--red)" if btc_num is not None else "var(--muted)")
    btc_arrow = "▲" if btc_num is not None and btc_num >= 0 else ("▼" if btc_num is not None else "")

    ls_signal = data.get("LS_Signal", "—")
    fr_val = data.get("FR", "—")
    fr_num = parse_number(fr_val)
    if fr_num is not None and fr_num > 0:
        fr_label = "Pozitif funding, long tarafına prim ödeniyor."
        fr_badge = "signal-long"
    elif fr_num is not None and fr_num < 0:
        fr_label = "Negatif funding, short tarafı baskın."
        fr_badge = "signal-short"
    else:
        fr_label = "Funding dengeli, tek taraflı kalabalık yok."
        fr_badge = "signal-neutral"

    hero_col, context_col = st.columns([1.75, 1.05])
    with hero_col:
        st.markdown(f"""
        <div class="btc-hero">
            <div class="metric-label">BITCOIN / USD — CANLI FİYAT</div>
            <div class="price">{data.get('BTC_P','—')}</div>
            <div class="sub">
                <span style="color:{btc_color}; font-weight:700;">{btc_arrow} 24s: {btc_c}</span>
                &nbsp;·&nbsp; 7g: {data.get('BTC_7D','—')}
                &nbsp;·&nbsp; Hacim: {data.get('Vol_24h','—')}
                &nbsp;·&nbsp; MCap: {data.get('BTC_MCap','—')}
            </div>
            <div class="hero-caption">
                Fiyat, duygu ve likidite verileri daha hızlı okunabilsin diye ilk blokta sadeleştirildi.
            </div>
        </div>
        """, unsafe_allow_html=True)
    with context_col:
        render_info_panel(
            "Executive View",
            "Bugünün Oyun Planı",
            [
                ("Piyasa rejimi", brief["regime"]["title"]),
                ("Pozisyonlanma", brief["positioning"]["title"]),
                ("Likidite modu", brief["liquidity"]["title"]),
                ("Odak seviye", brief["focus"]["detail"]),
            ],
            badge_text=brief["focus"]["title"],
            badge_kind=brief["focus"]["class"],
            copy="Kısa vadeli karar almadan önce yön, kalabalık taraf ve kritik seviyeler tek panelde toplandı.",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    cat("HIZLI NABIZ", "📡")
    render_cards([
        ("Fear & Greed", data.get("FNG", "—"), ""),
        ("Funding Rate", data.get("FR", "—"), ""),
        ("Open Interest", data.get("OI", "—"), ""),
        ("Günlük ETF Netflow", data.get("ETF_FLOW_TOTAL", "—"), data.get("ETF_FLOW_DATE", "—")),
        ("BTC Dominance", data.get("Dom", "—"), ""),
        ("ETH Dominance", data.get("ETH_Dom", "—"), ""),
        ("Taker B/S", data.get("Taker", "—"), ""),
        ("Toplam Piyasa Hacmi", data.get("Total_Vol", "—"), ""),
    ], cols=4)

    st.markdown("<br>", unsafe_allow_html=True)

    cat("POZİSYONLAMA & SEVİYELER", "🧭")
    col_sentiment, col_orderbook = st.columns([1.15, 1])
    with col_sentiment:
        render_info_panel(
            "Positioning",
            "Türev Piyasa Özeti",
            [
                ("Long / Short", ls_signal),
                ("L/S oranı", data.get("LS_Ratio", "—")),
                ("Long / Short %", f"{data.get('Long_Pct', '—')} / {data.get('Short_Pct', '—')}"),
                ("Funding", data.get("FR", "—")),
                ("Taker B/S", data.get("Taker", "—")),
                ("Open Interest", data.get("OI", "—")),
            ],
            badge_text=fr_label,
            badge_kind=fr_badge,
            copy="Kalabalık tarafı ve olası squeeze riskini tek bakışta okumak için türev verileri bir araya getirildi.",
        )
    with col_orderbook:
        render_info_panel(
            data.get("ORDERBOOK_SOURCES", "Kraken · OKX · KuCoin · Gate.io · Coinbase"),
            "Order Book Seviyeleri",
            [
                ("Birlesik sinyal", data.get("ORDERBOOK_SIGNAL", "—")),
                ("Kraken destek", f"{data.get('Sup_Wall', '—')} · {data.get('Sup_Vol', '—')}"),
                ("Kraken direnç", f"{data.get('Res_Wall', '—')} · {data.get('Res_Vol', '—')}"),
                ("OKX destek", f"{data.get('OKX_Sup_Wall', '—')} · {data.get('OKX_Sup_Vol', '—')}"),
                ("OKX direnç", f"{data.get('OKX_Res_Wall', '—')} · {data.get('OKX_Res_Vol', '—')}"),
                ("KuCoin destek", f"{data.get('KUCOIN_Sup_Wall', '—')} · {data.get('KUCOIN_Sup_Vol', '—')}"),
                ("KuCoin direnç", f"{data.get('KUCOIN_Res_Wall', '—')} · {data.get('KUCOIN_Res_Vol', '—')}"),
                ("Gate.io destek", f"{data.get('GATE_Sup_Wall', '—')} · {data.get('GATE_Sup_Vol', '—')}"),
                ("Gate.io direnç", f"{data.get('GATE_Res_Wall', '—')} · {data.get('GATE_Res_Vol', '—')}"),
                ("Coinbase destek", f"{data.get('COINBASE_Sup_Wall', '—')} · {data.get('COINBASE_Sup_Vol', '—')}"),
                ("Coinbase direnç", f"{data.get('COINBASE_Res_Wall', '—')} · {data.get('COINBASE_Res_Vol', '—')}"),
            ],
            badge_text=data.get("ORDERBOOK_SIGNAL", "—"),
            badge_kind=data.get("ORDERBOOK_SIGNAL_CLASS", "signal-neutral"),
            copy="Tek tek borsa durumlari yerine coklu borsa teyidi tek satirlik sinyalde toplanir; detay seviyeler asagida okunur.",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    cat("KURUMSAL AKIŞ & LİKİDİTE", "🏦")
    col_etf, col_liquidity = st.columns([1.25, 1])
    with col_etf:
        render_info_panel(
            "ETF Flow",
            "Günlük ETF Netflow Özeti",
            [
                ("Son dolu gün", data.get("ETF_FLOW_DATE", "—")),
                ("Toplam netflow", data.get("ETF_FLOW_TOTAL", "—")),
                ("Kaynak", data.get("ETF_FLOW_SOURCE", "Farside")),
                ("Detay görünümü", "Tüm Metrikler sekmesinde"),
            ],
            badge_text=brief["liquidity"]["title"],
            badge_kind=brief["liquidity"]["class"],
            copy="İlk sayfada yalnızca toplam kurumsal akış özeti tutuldu. ETF bazlı dağılım detayları Tüm Metrikler sekmesinde yer alıyor.",
        )
    with col_liquidity:
        render_info_panel(
            "Dry Powder",
            "Stablecoin Dominance",
            [
                ("Toplam stable", data.get("Total_Stable", "—")),
                ("Stable.C.D", data.get("STABLE_C_D", "—")),
                ("USDT market cap", data.get("USDT_MCap", "—")),
                ("USDT.D", data.get("USDT_D", "—")),
                ("USDC market cap", data.get("USDC_MCap", "—")),
                ("DAI market cap", data.get("DAI_MCap", "—")),
                ("USDT stable dominance", data.get("USDT_Dom_Stable", "—")),
            ],
            badge_text=brief["liquidity"]["title"],
            badge_kind=brief["liquidity"]["class"],
            copy=f"Günlük ETF netflow {data.get('ETF_FLOW_TOTAL', '—')} ({data.get('ETF_FLOW_DATE', '—')}) ile toplam stable dominance ve USDT payı aynı panelde; savunmacı akış daha net okunur.",
        )

    st.markdown("<br>", unsafe_allow_html=True)

    cat("MARKET CAP BREADTH", "📊")
    render_info_panel(
        "Breadth",
        "Piyasa Genisligi",
        [
            ("TOTAL", data.get("TOTAL_CAP", "—")),
            ("TOTAL2", data.get("TOTAL2_CAP", "—")),
            ("TOTAL3", data.get("TOTAL3_CAP", "—")),
            ("OTHERS", data.get("OTHERS_CAP", "—")),
            ("Kaynak", data.get("TOTAL_CAP_SOURCE", "—")),
        ],
        badge_text=data.get("TOTAL_CAP_SOURCE", "—"),
        badge_kind="signal-neutral",
        copy="TOTAL ailesi ayri bolume alindi; BTC harici ve genis altcoin evrenindeki risk istahi daha net okunur.",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    cat("ALTCOIN RADARI", "🪙")
    render_cards([
        ("Ethereum (ETH)", data.get("ETH_P", "—"), data.get("ETH_C", "")),
        ("Solana (SOL)", data.get("SOL_P", "—"), data.get("SOL_C", "")),
        ("BNB Chain (BNB)", data.get("BNB_P", "—"), data.get("BNB_C", "")),
        ("Ripple (XRP)", data.get("XRP_P", "—"), data.get("XRP_C", "")),
        ("Cardano (ADA)", data.get("ADA_P", "—"), data.get("ADA_C", "")),
        ("Avalanche (AVAX)", data.get("AVAX_P", "—"), data.get("AVAX_C", "")),
        ("Polkadot (DOT)", data.get("DOT_P", "—"), data.get("DOT_C", "")),
        ("Chainlink (LINK)", data.get("LINK_P", "—"), data.get("LINK_C", "")),
    ], cols=4)

    st.markdown("<br>", unsafe_allow_html=True)

    cat("7 GÜNLÜK GÖRELİ GÜÇ", "📅")
    render_cards([
        ("ETH 7g", data.get("ETH_7D", "—"), ""),
        ("SOL 7g", data.get("SOL_7D", "—"), ""),
        ("BNB 7g", data.get("BNB_7D", "—"), ""),
        ("XRP 7g", data.get("XRP_7D", "—"), ""),
        ("ADA 7g", data.get("ADA_7D", "—"), ""),
        ("AVAX 7g", data.get("AVAX_7D", "—"), ""),
        ("DOT 7g", data.get("DOT_7D", "—"), ""),
        ("LINK 7g", data.get("LINK_7D", "—"), ""),
    ], cols=4)

    top_news = data.get("NEWS", [])[:3]
    if top_news:
        st.markdown("<br>", unsafe_allow_html=True)
        cat("BUGÜNÜN HABER BAŞLIKLARI", "📰")
        news_cols = st.columns(len(top_news))
        for col, item in zip(news_cols, top_news):
            with col:
                st.markdown(f"""
                <div class="news-card">
                    <a href="{item['url']}" target="_blank">{item['title']}</a>
                    <div class="news-meta">🕐 {item['time']} · {item['source']}</div>
                </div>
                """, unsafe_allow_html=True)


# ── TAB 2: MAKRO & PIYASALAR ───────────────────────────────
with tab2:

    cat("MAKRO PARA POLİTİKASI", "🏦")
    render_cards([
        ("FED Faiz Oranı", data.get("FED", "—"), ""),
        ("M2 Büyümesi (YoY)", data.get("M2", "—"), ""),
        ("ABD 10Y Tahvil", data.get("US10Y", "—"), data.get("US10Y_C", "")),
        ("DXY Dolar Endeksi", data.get("DXY", "—"), data.get("DXY_C", "")),
        ("VIX Volatilite", data.get("VIX", "—"), data.get("VIX_C", "")),
        ("BTC ↔ S&P500 Kor.", str(data.get("Corr_SP500", "—")), ""),
        ("BTC ↔ Altın Kor.", str(data.get("Corr_Gold", "—")), ""),
    ], cols=4)

    st.markdown("<br>", unsafe_allow_html=True)

    cat("GLOBAL HİSSE SENEDİ ENDEKSLERİ", "📈")
    col_us, col_eu, col_asia = st.columns(3)
    with col_us:
        st.markdown('<div class="metric-label" style="margin-bottom:8px;">🇺🇸 AMERİKA</div>', unsafe_allow_html=True)
        render_cards([
            ("S&P 500", data.get("SP500", "—"), data.get("SP500_C", "")),
            ("NASDAQ", data.get("NASDAQ", "—"), data.get("NASDAQ_C", "")),
            ("Dow Jones", data.get("DOW", "—"), data.get("DOW_C", "")),
        ], cols=1)
    with col_eu:
        st.markdown('<div class="metric-label" style="margin-bottom:8px;">🇪🇺 AVRUPA</div>', unsafe_allow_html=True)
        render_cards([
            ("DAX (Almanya)", data.get("DAX", "—"), data.get("DAX_C", "")),
            ("FTSE 100 (UK)", data.get("FTSE", "—"), data.get("FTSE_C", "")),
            ("BIST 100 (TÜRKİYE)", data.get("BIST100", "—"), data.get("BIST100_C", "")),
        ], cols=1)
    with col_asia:
        st.markdown('<div class="metric-label" style="margin-bottom:8px;">🌏 ASYA</div>', unsafe_allow_html=True)
        render_cards([
            ("Nikkei 225 (JP)", data.get("NIKKEI", "—"), data.get("NIKKEI_C", "")),
            ("Hang Seng (HK)", data.get("HSI", "—"), data.get("HSI_C", "")),
        ], cols=1)

    st.markdown("<br>", unsafe_allow_html=True)

    cat("EMTİALAR — GLOBAL HAM MADDE", "🏭")
    col_metal, col_enerji = st.columns(2)
    with col_metal:
        st.markdown('<div class="metric-label" style="margin-bottom:8px;">METALLER</div>', unsafe_allow_html=True)
        render_cards([
            ("Altın / oz", data.get("GOLD", "—"), data.get("GOLD_C", "")),
            ("Gümüş / oz", data.get("SILVER", "—"), data.get("SILVER_C", "")),
            ("Bakır", data.get("COPPER", "—"), data.get("COPPER_C", "")),
        ], cols=1)
    with col_enerji:
        st.markdown('<div class="metric-label" style="margin-bottom:8px;">ENERJİ & TARIM</div>', unsafe_allow_html=True)
        render_cards([
            ("Ham Petrol (WTI)", data.get("OIL", "—"), data.get("OIL_C", "")),
            ("Doğalgaz", data.get("NATGAS", "—"), data.get("NATGAS_C", "")),
            ("Buğday", data.get("WHEAT", "—"), data.get("WHEAT_C", "")),
        ], cols=1)

    st.markdown("<br>", unsafe_allow_html=True)

    cat("DÖVİZ KURLARI", "💱")
    render_cards([
        ("EUR / USD", data.get("EURUSD", "—"), data.get("EURUSD_C", "")),
        ("GBP / USD", data.get("GBPUSD", "—"), data.get("GBPUSD_C", "")),
        ("USD / JPY", data.get("USDJPY", "—"), data.get("USDJPY_C", "")),
        ("USD / CHF", data.get("USDCHF", "—"), data.get("USDCHF_C", "")),
        ("AUD / USD", data.get("AUDUSD", "—"), data.get("AUDUSD_C", "")),
        ("USD / TRY", data.get("USDTRY", "—"), data.get("USDTRY_C", "")),
    ], cols=3)
# ── TAB 3: GRAFİK & RAPOR ────────────────────────────────────
with tab3:
    col_chart, col_side = st.columns([2.2, 1.2])
    with col_chart:
        st.subheader("📊 Canlı BTC/USDT Grafiği")
        components.html("""
        <div style="height:520px;">
        <script src="https://s3.tradingview.com/tv.js"></script>
        <script>new TradingView.widget({autosize:true,symbol:"BINANCE:BTCUSDT",
        interval:"D",theme:"dark",style:"1",locale:"tr",toolbar_bg:"#070d1a",
        container_id:"tv_main"});</script>
        <div id="tv_main" style="height:100%;"></div></div>""", height=540)

    with col_side:
        st.subheader("📅 Ekonomik Takvim")
        components.html("""
        <div class="tradingview-widget-container">
        <div class="tradingview-widget-container__widget"></div>
        <script src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
        {"colorTheme":"dark","isTransparent":true,"width":"100%","height":"480",
        "locale":"tr","importanceFilter":"0,1","currencyFilter":"USD,EUR"}</script></div>""", height=500)

        st.divider()
        st.subheader("🤖 God Mode Strateji Raporu")
        if st.button("🚀 AI RAPORU OLUŞTUR", use_container_width=True):
            with st.spinner("Gemini 2.5 Flash analiz ediyor — derin rapor hazırlanıyor..."):
                bugun = pd.Timestamp.now(tz="Europe/Istanbul").strftime("%d %B %Y, %A — %H:%M")
                news_str = "\n".join(f"• {n['title']} ({n['source']})" for n in data.get("NEWS",[])[:6])

                prompt = f"""Sen 20 yıllık deneyime sahip bir makro-kripto fon yöneticisi ve quant analistsin.
Aşağıdaki TÜM gerçek piyasa verilerini kullanarak Serhat için derinlikli, rakamsal ve eyleme dönüşebilir bir strateji raporu yaz.
Türkçe yaz. Rapor profesyonel, yapılandırılmış ve her iddia rakamla desteklenmiş olmalı.

TEMEL KURALLAR:
- Her iddiayı mutlaka rakamla destekle. "VIX yüksek" değil, "VIX {data.get('VIX','—')} seviyesinde" yaz.
- Seviyeleri kesin belirt: "$84,200 kırılırsa..." gibi somut eşikler ver.
- Yüzeysel geçme, her bölüm derinlikli analiz içersin.
- Tüm veri kategorilerini (makro, türev, on-chain, ETF, forex, emtia, altcoin) mutlaka kullan.
- "Dikkatli ol" gibi genel laflar yerine somut aksiyon ver.

YAZIM KURALLARI:
- Asla "bu rapor yatırım tavsiyesi değildir" veya benzeri yasal uyarı yazma.
- Asla LaTeX formatı ($65,000 yerine $65.000 gibi) kullanma, düz metin yaz.
- Markdown formatı kullan: **kalın**, başlıklar için ## kullan.
- Fiyatları her zaman düz yazı olarak yaz: 65000 dolar veya $65,000

━━━━━━━━ CANLI VERİLER ({bugun}) ━━━━━━━━

📌 BİTCOİN:
Fiyat: {data.get('BTC_P','—')} | 24s: {data.get('BTC_C','—')} | 7g: {data.get('BTC_7D','—')}
Hacim 24s: {data.get('Vol_24h','—')} | MCap: {data.get('BTC_MCap','—')}
BTC Dominance: {data.get('Dom','—')} | ETH Dominance: {data.get('ETH_Dom','—')}
Total MCap: {data.get('Total_MCap','—')} | Total Hacim: {data.get('Total_Vol','—')}

📌 TÜREV PİYASALAR:
Open Interest: {data.get('OI','—')}
Funding Rate: {data.get('FR','—')}
Taker Buy/Sell: {data.get('Taker','—')}
Long/Short Oranı: {data.get('LS_Ratio','—')} → {data.get('LS_Signal','—')}
Long %: {data.get('Long_Pct','—')} | Short %: {data.get('Short_Pct','—')}

📌 BALİNA DUVARLARI (Kraken + OKX + KuCoin + Gate.io + Coinbase):
Birleşik sinyal: {data.get('ORDERBOOK_SIGNAL','—')} | Detay: {data.get('ORDERBOOK_SIGNAL_DETAIL','—')}
Kraken → 🟢 Destek: {data.get('Sup_Wall','—')} — {data.get('Sup_Vol','—')} | 🔴 Direnç: {data.get('Res_Wall','—')} — {data.get('Res_Vol','—')} | Durum: {data.get('Wall_Status','—')}
OKX → 🟢 Destek: {data.get('OKX_Sup_Wall','—')} — {data.get('OKX_Sup_Vol','—')} | 🔴 Direnç: {data.get('OKX_Res_Wall','—')} — {data.get('OKX_Res_Vol','—')} | Durum: {data.get('OKX_Wall_Status','—')}
KuCoin → 🟢 Destek: {data.get('KUCOIN_Sup_Wall','—')} — {data.get('KUCOIN_Sup_Vol','—')} | 🔴 Direnç: {data.get('KUCOIN_Res_Wall','—')} — {data.get('KUCOIN_Res_Vol','—')} | Durum: {data.get('KUCOIN_Wall_Status','—')}
Gate.io → 🟢 Destek: {data.get('GATE_Sup_Wall','—')} — {data.get('GATE_Sup_Vol','—')} | 🔴 Direnç: {data.get('GATE_Res_Wall','—')} — {data.get('GATE_Res_Vol','—')} | Durum: {data.get('GATE_Wall_Status','—')}
Coinbase → 🟢 Destek: {data.get('COINBASE_Sup_Wall','—')} — {data.get('COINBASE_Sup_Vol','—')} | 🔴 Direnç: {data.get('COINBASE_Res_Wall','—')} — {data.get('COINBASE_Res_Vol','—')} | Durum: {data.get('COINBASE_Wall_Status','—')}

📌 KORKU & DUYGU:
Fear & Greed Index: {data.get('FNG','—')} (dün: {data.get('FNG_PREV','—')})

📌 GÜNLÜK ETF NETFLOW (Farside):
Tarih: {data.get('ETF_FLOW_DATE','—')} | Toplam: {data.get('ETF_FLOW_TOTAL','—')}
IBIT: {data.get('ETF_FLOW_IBIT','—')} | FBTC: {data.get('ETF_FLOW_FBTC','—')} | BITB: {data.get('ETF_FLOW_BITB','—')} | ARKB: {data.get('ETF_FLOW_ARKB','—')}
BTCO: {data.get('ETF_FLOW_BTCO','—')} | EZBC: {data.get('ETF_FLOW_EZBC','—')} | BRRR: {data.get('ETF_FLOW_BRRR','—')} | HODL: {data.get('ETF_FLOW_HODL','—')}
BTCW: {data.get('ETF_FLOW_BTCW','—')} | GBTC: {data.get('ETF_FLOW_GBTC','—')} | BTC: {data.get('ETF_FLOW_BTC','—')}

📌 STABLECOİN LİKİDİTESİ:
TOTAL: {data.get('TOTAL_CAP','—')} | TOTAL2: {data.get('TOTAL2_CAP','—')} | TOTAL3: {data.get('TOTAL3_CAP','—')} | OTHERS: {data.get('OTHERS_CAP','—')}
Toplam: {data.get('Total_Stable','—')} | USDT: {data.get('USDT_MCap','—')} | USDC: {data.get('USDC_MCap','—')} | DAI: {data.get('DAI_MCap','—')}
Stable.C.D (Piyasa %): {data.get('STABLE_C_D','—')} | USDT.D (Piyasa %): {data.get('USDT_D','—')} | USDT Dom (Stable içi): {data.get('USDT_Dom_Stable','—')}

📌 ON-CHAIN:
Hashrate: {data.get('Hash','—')} | Aktif Adres (est): {data.get('Active','—')}
BTC ↔ S&P500 Korelasyon (30g): {data.get('Corr_SP500','—')}
BTC ↔ Altın Korelasyon (30g): {data.get('Corr_Gold','—')}

📌 MAKRO PARA POLİTİKASI:
FED Faizi: {data.get('FED','—')} | M2 Büyümesi (YoY): {data.get('M2','—')}
ABD 10Y Tahvil: {data.get('US10Y','—')} ({data.get('US10Y_C','—')})
DXY: {data.get('DXY','—')} ({data.get('DXY_C','—')})
VIX: {data.get('VIX','—')} ({data.get('VIX_C','—')})

📌 GLOBAL HİSSE ENDEKSLERİ:
S&P500: {data.get('SP500','—')} ({data.get('SP500_C','—')})
NASDAQ: {data.get('NASDAQ','—')} ({data.get('NASDAQ_C','—')})
DOW: {data.get('DOW','—')} ({data.get('DOW_C','—')})
DAX: {data.get('DAX','—')} ({data.get('DAX_C','—')})
FTSE: {data.get('FTSE','—')} ({data.get('FTSE_C','—')})
NIKKEI: {data.get('NIKKEI','—')} ({data.get('NIKKEI_C','—')})
BIST100: {data.get('BIST100','—')} ({data.get('BIST100_C','—')})

📌 FOREX:
DXY: {data.get('DXY','—')} | EUR/USD: {data.get('EURUSD','—')} ({data.get('EURUSD_C','—')})
GBP/USD: {data.get('GBPUSD','—')} | USD/JPY: {data.get('USDJPY','—')} ({data.get('USDJPY_C','—')})
USD/TRY: {data.get('USDTRY','—')} ({data.get('USDTRY_C','—')}) | USD/CHF: {data.get('USDCHF','—')}

📌 EMTİALAR:
Altın: {data.get('GOLD','—')} ({data.get('GOLD_C','—')})
Gümüş: {data.get('SILVER','—')} ({data.get('SILVER_C','—')})
Ham Petrol: {data.get('OIL','—')} ({data.get('OIL_C','—')})
Doğalgaz: {data.get('NATGAS','—')} ({data.get('NATGAS_C','—')})
Bakır: {data.get('COPPER','—')} ({data.get('COPPER_C','—')})
Buğday: {data.get('WHEAT','—')} ({data.get('WHEAT_C','—')})

📌 ALTCOİNLER:
ETH: {data.get('ETH_P','—')} | 24s: {data.get('ETH_C','—')} | 7g: {data.get('ETH_7D','—')}
SOL: {data.get('SOL_P','—')} | 24s: {data.get('SOL_C','—')} | 7g: {data.get('SOL_7D','—')}
BNB: {data.get('BNB_P','—')} | 24s: {data.get('BNB_C','—')}
XRP: {data.get('XRP_P','—')} | 24s: {data.get('XRP_C','—')}
ADA: {data.get('ADA_P','—')} | AVAX: {data.get('AVAX_P','—')}
DOT: {data.get('DOT_P','—')} | LINK: {data.get('LINK_P','—')}

📌 SON KRİPTO HABERLERİ:
{news_str if news_str else 'Haber alınamadı'}

━━━━━━━━ RAPOR YAPISI (her bölümü eksiksiz doldur) ━━━━━━━━

**🌍 1. MAKRO ORTAM ANALİZİ**
- SP500 {data.get('SP500_C','—')}, NASDAQ {data.get('NASDAQ_C','—')}, VIX {data.get('VIX','—')} — risk iştahı ne söylüyor?
- DXY {data.get('DXY','—')} ve tahvil faizi {data.get('US10Y','—')} BTC için ne anlam taşıyor?
- M2 {data.get('M2','—')} + FED {data.get('FED','—')}: likidite koşulları gevşiyor mu sıkışıyor mu?
- BTC↔SP500 korelasyon {data.get('Corr_SP500','—')}: hangi yönde kullanılabilir?
- Altın {data.get('GOLD','—')} ve petrol {data.get('OIL','—')} enflasyon/risk sinyali ne veriyor?
- USDTRY {data.get('USDTRY','—')}: TL bazlı yatırımcı için BTC avantajlı mı?

**₿ 2. BİTCOİN TEKNİK & TÜREV ANALİZİ**
- Fiyat {data.get('BTC_P','—')}, hacim {data.get('Vol_24h','—')}, 24s {data.get('BTC_C','—')}, 7g {data.get('BTC_7D','—')} trendini yorumla.
- OI {data.get('OI','—')}: pozisyon birikimi tehlikeli seviyede mi?
- Funding Rate {data.get('FR','—')}: short squeeze mu long liquidation mu daha olası?
- L/S {data.get('LS_Ratio','—')} ({data.get('LS_Signal','—')}): kalabalık taraf nerede, squeeze ihtimali?
- Taker B/S {data.get('Taker','—')}: piyasaya agresif alıcı mı satıcı mı hakim?
- Birleşik sinyal {data.get('ORDERBOOK_SIGNAL','—')}: Kraken, OKX, KuCoin, Gate.io ve Coinbase seviyeleri aynı yöne bakıyor mu?
- Kraken destek {data.get('Sup_Wall','—')} ({data.get('Sup_Vol','—')}), OKX destek {data.get('OKX_Sup_Wall','—')} ({data.get('OKX_Sup_Vol','—')}), KuCoin destek {data.get('KUCOIN_Sup_Wall','—')} ({data.get('KUCOIN_Sup_Vol','—')}), Gate.io destek {data.get('GATE_Sup_Wall','—')} ({data.get('GATE_Sup_Vol','—')}) ve Coinbase destek {data.get('COINBASE_Sup_Wall','—')} ({data.get('COINBASE_Sup_Vol','—')}): ortak destek gerçekten güçlü mü?
- Kraken direnç {data.get('Res_Wall','—')} ({data.get('Res_Vol','—')}), OKX direnç {data.get('OKX_Res_Wall','—')} ({data.get('OKX_Res_Vol','—')}), KuCoin direnç {data.get('KUCOIN_Res_Wall','—')} ({data.get('KUCOIN_Res_Vol','—')}), Gate.io direnç {data.get('GATE_Res_Wall','—')} ({data.get('GATE_Res_Vol','—')}) ve Coinbase direnç {data.get('COINBASE_Res_Wall','—')} ({data.get('COINBASE_Res_Vol','—')}): kırılabilir mi?

**🏦 3. KURUMSAL AKIŞ & LİKİDİTE ANALİZİ**
- Günlük ETF netflow {data.get('ETF_FLOW_TOTAL','—')} ({data.get('ETF_FLOW_DATE','—')}): kurumsal para girişi/çıkışı trendi ne?
- ETF bazlı akış dağılımı BTC fiyatıyla örtüşüyor mu?
- TOTAL {data.get('TOTAL_CAP','—')}, TOTAL2 {data.get('TOTAL2_CAP','—')}, TOTAL3 {data.get('TOTAL3_CAP','—')} ve OTHERS {data.get('OTHERS_CAP','—')}: risk iştahı büyüklerde mi, geniş altcoin tarafında mı yoğunlaşıyor?
- Stablecoin toplam {data.get('Total_Stable','—')}: piyasaya hazır "barut" var mı?
- Stable.C.D {data.get('STABLE_C_D','—')} ve USDT.D {data.get('USDT_D','—')}: toplam stable parkı ile USDT özel talebi aynı şeyi mi söylüyor?
- Likidite analizi: para kripto'ya mı giriyor, stablecoin'de mi bekliyor?

**🪙 4. ALTCOİN & DOMAİNANCE ANALİZİ**
- BTC dominance {data.get('Dom','—')}, ETH dominance {data.get('ETH_Dom','—')}: dominance trendi yükseliyor mu?
- ETH ({data.get('ETH_C','—')} / 7g: {data.get('ETH_7D','—')}), SOL ({data.get('SOL_C','—')} / 7g: {data.get('SOL_7D','—')}) BTC'ye göre güçlü mü zayıf mı?
- Hangi altcoin rölatif güç gösteriyor? Hangisi zayıf?
- Bu dominance seviyesinde altcoin pozisyonu mantıklı mı?

**📰 5. HABER & KATALIZÖR ANALİZİ**
- Yukarıdaki haberlerin BTC/kripto piyasasına olası etkisini değerlendir.
- Önümüzdeki 1-3 gün için izlenmesi gereken kritik gelişmeler neler?

**🎯 6. GÜNLÜK AKSİYON PLANI (1-3 Gün)**

📗 LONG (Alış) Senaryosu:
  - Giriş seviyesi: (kesin rakam)
  - Stop-Loss: (kesin rakam)
  - Hedef 1 / Hedef 2: (kesin rakamlar)
  - Gerekçe: (hangi koşul sağlanırsa giriş yapılır)

📕 SHORT (Satış) Senaryosu:
  - Giriş seviyesi: (kesin rakam)
  - Stop-Loss: (kesin rakam)
  - Hedef 1 / Hedef 2: (kesin rakamlar)
  - Gerekçe: (hangi koşul sağlanırsa giriş yapılır)

📒 BEKLE Senaryosu:
  - Hangi koşulda beklenmeli?
  - Beklerken izlenecek tetikleyici seviyeler neler?

**⚠️ 7. KRİTİK RİSK & ÖZET**
- Bugünün en kritik riski (tek cümle, rakamsal)
- Genel piyasa pozisyonu özeti (1-2 cümle)
- BTC için en olası senaryo (rakamsal eşiklerle)
"""
                try:
                    resp = client.chat.completions.create(
                        model="google/gemini-2.5-flash",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=8000
                    )
                    rapor_md = resp.choices[0].message.content
                    st.markdown(f'<div class="report-box">{rapor_md}</div>', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"AI hatası: {e}")


# ── TAB 4: HABERLER ──────────────────────────────────────────
with tab4:
    col_news, col_tv = st.columns([1, 1])
    with col_news:
        st.subheader("📰 Son Kripto Haberleri (CoinDesk)")
        news = data.get("NEWS", [])
        if news:
            for item in news:
                st.markdown(f"""
                <div class="news-card">
                    <a href="{item['url']}" target="_blank">{item['title']}</a>
                    <div class="news-meta">🕐 {item['time']} · {item['source']}</div>
                </div>""", unsafe_allow_html=True)
        else:
            st.info("Haber yüklenemedi.")
    with col_tv:
        st.subheader("📡 Canlı Haber Bandı (TradingView)")
        components.html("""
        <div class="tradingview-widget-container">
        <div class="tradingview-widget-container__widget"></div>
        <script src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>
        {"feedMode":"all_symbols","isTransparent":true,"displayMode":"regular",
        "width":"100%","height":"800","colorTheme":"dark","locale":"tr"}</script></div>""", height=820)


# ── TAB 5: TÜM METRİKLER ─────────────────────────────────────
with tab5:
    st.subheader("⚙️ Tüm Metrikler — Ham Veri")
    sections = {
        "₿ BTC & Kripto": [
            ("BTC Fiyatı","BTC_P"),("BTC 24s","BTC_C"),("BTC 7g","BTC_7D"),
            ("BTC MCap","BTC_MCap"),("24s Hacim","Vol_24h"),
            ("BTC Dominance","Dom"),("ETH Dominance","ETH_Dom"),
            ("Total MCap","Total_MCap"),("Total Hacim","Total_Vol"),
        ],
        "📊 Türev & Sentiment": [
            ("OI","OI"),("Funding Rate","FR"),("Taker B/S","Taker"),
            ("L/S Oranı","LS_Ratio"),("Long %","Long_Pct"),("Short %","Short_Pct"),
            ("L/S Sinyal","LS_Signal"),("Korku/Açgözlülük","FNG"),("FNG Dün","FNG_PREV"),
        ],
        "🐋 Order Book & ETF": [
            ("Destek Duvarı","Sup_Wall"),("Destek Hacim","Sup_Vol"),
            ("Direnç Duvarı","Res_Wall"),("Direnç Hacim","Res_Vol"),
            ("Tahta Durumu","Wall_Status"),("Birleşik Sinyal","ORDERBOOK_SIGNAL"),
            ("Birleşik Detay","ORDERBOOK_SIGNAL_DETAIL"),("Kaynaklar","ORDERBOOK_SOURCES"),
            ("OKX Destek","OKX_Sup_Wall"),("OKX Destek Hacim","OKX_Sup_Vol"),
            ("OKX Direnç","OKX_Res_Wall"),("OKX Direnç Hacim","OKX_Res_Vol"),
            ("OKX Durum","OKX_Wall_Status"),("KuCoin Destek","KUCOIN_Sup_Wall"),
            ("KuCoin Destek Hacim","KUCOIN_Sup_Vol"),("KuCoin Direnç","KUCOIN_Res_Wall"),
            ("KuCoin Direnç Hacim","KUCOIN_Res_Vol"),("KuCoin Durum","KUCOIN_Wall_Status"),
            ("Gate.io Destek","GATE_Sup_Wall"),("Gate.io Destek Hacim","GATE_Sup_Vol"),
            ("Gate.io Direnç","GATE_Res_Wall"),("Gate.io Direnç Hacim","GATE_Res_Vol"),
            ("Gate.io Durum","GATE_Wall_Status"),
            ("Coinbase Destek","COINBASE_Sup_Wall"),("Coinbase Destek Hacim","COINBASE_Sup_Vol"),
            ("Coinbase Direnç","COINBASE_Res_Wall"),("Coinbase Direnç Hacim","COINBASE_Res_Vol"),
            ("Coinbase Durum","COINBASE_Wall_Status"),
            ("ETF Tarih","ETF_FLOW_DATE"),("ETF Netflow Toplam","ETF_FLOW_TOTAL"),
            ("IBIT Netflow","ETF_FLOW_IBIT"),("FBTC Netflow","ETF_FLOW_FBTC"),
            ("BITB Netflow","ETF_FLOW_BITB"),("ARKB Netflow","ETF_FLOW_ARKB"),
            ("BTCO Netflow","ETF_FLOW_BTCO"),("EZBC Netflow","ETF_FLOW_EZBC"),
            ("BRRR Netflow","ETF_FLOW_BRRR"),("HODL Netflow","ETF_FLOW_HODL"),
            ("BTCW Netflow","ETF_FLOW_BTCW"),("GBTC Netflow","ETF_FLOW_GBTC"),
            ("BTC Netflow","ETF_FLOW_BTC"),
        ],
        "📊 Market Cap Breadth": [
            ("TOTAL","TOTAL_CAP"),("TOTAL2","TOTAL2_CAP"),
            ("TOTAL3","TOTAL3_CAP"),("OTHERS","OTHERS_CAP"),
            ("Kaynak","TOTAL_CAP_SOURCE"),
        ],
        "💵 Stablecoin & On-Chain": [
            ("Toplam Stable","Total_Stable"),("USDT","USDT_MCap"),
            ("USDC","USDC_MCap"),("DAI","DAI_MCap"),
            ("Stable.C.D","STABLE_C_D"),("USDT.D","USDT_D"),("USDT Dom Stable","USDT_Dom_Stable"),
            ("Hashrate","Hash"),("Aktif Adres (est)","Active"),
        ],
        "🌍 Makro & Para Politikası": [
            ("FED Faizi","FED"),("M2 YoY","M2"),("ABD 10Y","US10Y"),
            ("DXY","DXY"),("VIX","VIX"),
            ("BTC↔SP500","Corr_SP500"),("BTC↔Altın","Corr_Gold"),
        ],
        "📈 Endeksler & Emtia": [
            ("S&P 500","SP500"),("NASDAQ","NASDAQ"),("DAX","DAX"),
            ("NIKKEI","NIKKEI"),("BIST100","BIST100"),
            ("Altın","GOLD"),("Gümüş","SILVER"),("Petrol","OIL"),
            ("Doğalgaz","NATGAS"),("Bakır","COPPER"),
        ],
        "💱 Forex": [
            ("EUR/USD","EURUSD"),("GBP/USD","GBPUSD"),("USD/JPY","USDJPY"),
            ("USD/TRY","USDTRY"),("USD/CHF","USDCHF"),("AUD/USD","AUDUSD"),
        ],
    }

    # 4 sütun grid
    sec_list = list(sections.items())
    for row_start in range(0, len(sec_list), 4):
        cols = st.columns(4)
        for i, (sec_name, items) in enumerate(sec_list[row_start:row_start+4]):
            with cols[i]:
                st.markdown(f"**{sec_name}**")
                df = pd.DataFrame(
                    [(lbl, data.get(key, "—")) for lbl, key in items],
                    columns=["Metrik", "Değer"]
                )
                st.dataframe(df, use_container_width=True, hide_index=True)

import os

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError

from domain.market_brief import build_market_brief
from domain.parsers import parse_number
from services.ai_service import build_openrouter_client, generate_strategy_report
from services.health import build_health_summary, merge_source_health
from services.market_data import load_terminal_data
from ui.components import cat, render_cards, render_info_panel, render_market_brief
from ui.layout import render_health_alerts, render_page_header, render_sidebar

load_dotenv()
FRED_API_KEY       = os.getenv("FRED_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

if not OPENROUTER_API_KEY:
    st.error("❌ OPENROUTER_API_KEY eksik!")
    st.stop()

client = build_openrouter_client(OPENROUTER_API_KEY)

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


# ============================================================
#  SAYFA YÜKLEMESİ
# ============================================================
son_guncelleme = pd.Timestamp.now(tz="Europe/Istanbul").strftime("%d.%m.%Y %H:%M:%S")
with st.spinner("Piyasa verileri ve türev akışı yükleniyor..."):
    data = load_terminal_data(FRED_API_KEY)
    current_health = merge_source_health(st.session_state.get("source_health"), data.pop("_health", {}))
    data["_health"] = current_health
    st.session_state["source_health"] = current_health

health_summary = build_health_summary(data.get("_health", {}))

brief = build_market_brief(data)

render_page_header(son_guncelleme)
render_health_alerts(health_summary)
render_market_brief(brief)
render_sidebar(data, brief, son_guncelleme, health_summary)

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
            with st.spinner("Gemini 2.5 Flash analiz ediyor - derin rapor hazirlaniyor..."):
                try:
                    rapor_md = generate_strategy_report(client, data)
                    st.markdown(f'<div class="report-box">{rapor_md}</div>', unsafe_allow_html=True)
                except (APIConnectionError, APITimeoutError, RateLimitError, APIError, ValueError) as e:
                    st.error(f"AI hatasi: {e}")


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

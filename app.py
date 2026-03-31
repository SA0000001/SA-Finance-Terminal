import os

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from openai import APIConnectionError, APIError, APITimeoutError, RateLimitError

from domain.analytics import (
    DEFAULT_PINNED_METRICS,
    METRIC_LABELS,
    build_alerts,
    build_analytics_payload,
    build_daily_summary_markdown,
    build_pinned_metrics,
    markdown_to_basic_pdf_bytes,
)
from domain.market_brief import build_market_brief
from services.ai_service import build_openrouter_client, generate_strategy_report
from services.health import build_health_summary, merge_source_health
from services.market_data import load_terminal_data
from services.preferences import load_preferences, save_preferences
from ui.components import cat, clean_text, render_cards, render_info_panel, render_market_brief
from ui.layout import render_health_alerts, render_page_header, render_sidebar

load_dotenv()
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

st.set_page_config(
    page_title="SA Finance Alpha Terminal",
    page_icon="SA",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;600;700;800&display=swap');

:root {
    --bg: #070d1a;
    --bg2: #0b1425;
    --bg3: #0f1e35;
    --border: #1a2d4a;
    --accent: #00e5ff;
    --accent2: #ff6b35;
    --green: #00ff88;
    --red: #ff3b5c;
    --yellow: #ffd600;
    --text: #c8d8e8;
    --muted: #4a6080;
    --mono: 'Space Mono', monospace;
    --sans: 'Syne', sans-serif;
}

html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg) !important;
    font-family: var(--sans) !important;
    color: var(--text) !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #070d1a 0%, #0b1425 100%) !important;
    border-right: 1px solid var(--border) !important;
}

#MainMenu, footer, header { visibility: hidden; }

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
    display: flex;
    gap: 18px;
}

.hero-kicker, .cat-header, .metric-label, .header-pill, .health-pill {
    font-family: var(--mono);
}

.hero-kicker {
    font-size: 0.72em;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 10px;
}

.terminal-header h1 {
    margin: 0;
    color: #ffffff;
    font-size: 2.1rem;
}

.header-subtitle, .section-lead, .panel-copy, .overview-detail, .why-item {
    color: var(--text);
    opacity: 0.85;
}

.header-meta {
    display: flex;
    align-items: center;
    gap: 10px;
    flex-wrap: wrap;
    justify-content: flex-end;
}

.header-pill, .health-pill {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 9px 12px;
    border-radius: 999px;
    border: 1px solid rgba(55, 91, 137, 0.9);
    background: rgba(7, 16, 30, 0.78);
    color: #eff8ff;
    font-size: 0.74em;
}

.badge {
    background: var(--accent);
    color: #000;
    padding: 8px 12px;
    border-radius: 8px;
    font-weight: 700;
    font-family: var(--mono);
}

.health-strip {
    display: flex;
    gap: 10px;
    margin: 0 0 18px 0;
    flex-wrap: wrap;
}

.health-ok { border-color: rgba(0,255,136,0.45); }
.health-fail { border-color: rgba(255,59,92,0.45); }
.health-stale { border-color: rgba(255,214,0,0.45); }

.metric-card, .overview-card, .info-panel, .pin-board, .score-card, .matrix-card, .alert-card {
    background: linear-gradient(180deg, rgba(12,20,37,0.95), rgba(10,17,31,0.96));
    border: 1px solid rgba(32, 53, 84, 0.95);
    border-radius: 18px;
    padding: 18px;
    box-shadow: 0 14px 34px rgba(0,0,0,0.18);
}

.metric-card { border-radius: 10px; }

.metric-card::before {
    content: '';
    display: block;
    height: 2px;
    margin: -18px -18px 12px -18px;
    background: linear-gradient(90deg, var(--card-accent, var(--accent)), transparent);
    border-top-left-radius: 18px;
    border-top-right-radius: 18px;
}

.metric-value {
    font-family: var(--mono);
    font-size: 1.2rem;
    color: #fff;
    font-weight: 700;
}

.metric-delta-pos { color: var(--green); font-size: 0.8rem; font-family: var(--mono); }
.metric-delta-neg { color: var(--red); font-size: 0.8rem; font-family: var(--mono); }
.metric-delta-neu { color: var(--muted); font-size: 0.8rem; font-family: var(--mono); }

.panel-row {
    display: flex;
    justify-content: space-between;
    gap: 14px;
    padding: 10px 0;
    border-bottom: 1px solid rgba(30, 45, 70, 0.92);
}

.panel-row:last-child { border-bottom: none; }
.panel-row span { color: var(--muted); }
.panel-row strong { color: #f4fbff; text-align: right; }

.signal-long, .signal-short, .signal-neutral {
    font-family: var(--mono);
    font-size: 0.72em;
    padding: 4px 10px;
    border-radius: 6px;
    display: inline-block;
    font-weight: 700;
}

.signal-long { background: rgba(0,255,136,0.12); border: 1px solid var(--green); color: var(--green); }
.signal-short { background: rgba(255,59,92,0.12); border: 1px solid var(--red); color: var(--red); }
.signal-neutral { background: rgba(255,214,0,0.10); border: 1px solid var(--yellow); color: var(--yellow); }

.why-list { margin-top: 14px; display: grid; gap: 6px; }
.why-item {
    padding: 8px 10px;
    border-radius: 10px;
    background: rgba(255,255,255,0.03);
    font-size: 0.82rem;
}

.pin-board, .score-card, .matrix-card, .alert-card { height: 100%; }

.alert-card { border-left: 3px solid var(--accent2); }

.report-box {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 24px 28px;
    line-height: 1.8;
    font-size: 0.95em;
}

[data-testid="stTabs"] { margin-top: 12px; }
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

.news-card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.news-card a { color: #e0eef8; text-decoration: none; font-weight: 600; }
.news-meta { color: var(--muted); font-size: 0.72em; margin-top: 5px; font-family: var(--mono); }

@media (max-width: 900px) {
    .terminal-header {
        padding: 22px 20px;
        align-items: flex-start;
        flex-direction: column;
    }
    .header-meta { justify-content: flex-start; }
}
</style>
""",
    unsafe_allow_html=True,
)


def init_preferences():
    if "preferences" not in st.session_state:
        st.session_state["preferences"] = load_preferences()


def render_preferences_panel():
    preferences = st.session_state["preferences"]
    with st.sidebar.expander("Kisisel Ayarlar", expanded=True):
        view_mode = st.radio(
            "Gorunum modu", ["Basit", "Pro"], index=0 if preferences.get("view_mode") == "Basit" else 1
        )
        report_depth = st.selectbox(
            "Rapor seviyesi",
            ["Kisa", "Orta", "Derin"],
            index=["Kisa", "Orta", "Derin"].index(preferences.get("report_depth", "Orta")),
        )
        pinned_metrics = st.multiselect(
            "Pinli metrikler",
            options=list(METRIC_LABELS),
            default=preferences.get("pinned_metrics", DEFAULT_PINNED_METRICS),
            format_func=lambda key: METRIC_LABELS.get(key, key),
        )
        funding_above = st.number_input(
            "Funding > X", value=float(preferences["thresholds"].get("funding_above", 0.01)), step=0.005, format="%.4f"
        )
        vix_above = st.number_input(
            "VIX > Y", value=float(preferences["thresholds"].get("vix_above", 25.0)), step=0.5, format="%.2f"
        )
        etf_flow_below = st.number_input(
            "ETF netflow < Z",
            value=float(preferences["thresholds"].get("etf_flow_below", 0.0)),
            step=10.0,
            format="%.1f",
        )
        if st.button("Ayarlari Kaydet", use_container_width=True):
            preferences["view_mode"] = view_mode
            preferences["report_depth"] = report_depth
            preferences["pinned_metrics"] = pinned_metrics[:8]
            preferences["thresholds"] = {
                "funding_above": funding_above,
                "vix_above": vix_above,
                "etf_flow_below": etf_flow_below,
            }
            save_preferences(preferences)
            st.session_state["preferences"] = preferences
            st.success("Ayarlar kaydedildi.")


def render_pinned_dashboard(data: dict, pinned_metrics: list[str]):
    pinned_items = build_pinned_metrics(data, pinned_metrics)
    st.markdown("<div class='pin-board'>", unsafe_allow_html=True)
    cat("Pinli Dashboard")
    render_cards(pinned_items, cols=4)
    st.markdown("</div>", unsafe_allow_html=True)


def render_score_panel(analytics: dict):
    scores = analytics["scores"]
    st.markdown("<div class='score-card'>", unsafe_allow_html=True)
    cat("Rejim Skorlama")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Genel", f"{scores['overall']}/100")
    for col, (label, value) in zip([col2, col3, col4, col5], scores["subscores"].items()):
        col.metric(label, f"{value}/100")
    st.markdown("</div>", unsafe_allow_html=True)


def render_scenario_matrix(analytics: dict):
    st.markdown("<div class='matrix-card'>", unsafe_allow_html=True)
    cat("Senaryo Matrisi")
    st.dataframe(pd.DataFrame(analytics["scenarios"]), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_alert_panel(alerts: list[dict]):
    st.markdown("<div class='alert-card'>", unsafe_allow_html=True)
    cat("Alarm Kurallari")
    if alerts:
        for alert in alerts:
            st.markdown(f"**{clean_text(alert['title'])}**")
            st.caption(clean_text(alert["detail"]))
    else:
        st.caption("Aktif alarm yok. Funding, VIX ve ETF esikleri sessiz.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_reasoning_panel(brief: dict):
    cat("Neden Boyle Dusunuyorum?")
    cols = st.columns(2)
    items = list(brief.items())
    for column, (key, card) in zip(cols * 2, items):
        with column:
            render_info_panel(
                key.replace("_", " ").title(),
                card["title"],
                [(f"Neden {idx + 1}", reason) for idx, reason in enumerate(card.get("why", []))],
                badge_text=card["badge"],
                badge_kind=card["class"],
                copy=card["detail"],
            )


def render_downloads(data: dict, brief: dict, analytics: dict, alerts: list[dict], health_summary: dict):
    summary_md = build_daily_summary_markdown(data, brief, analytics, alerts, health_summary)
    summary_pdf = markdown_to_basic_pdf_bytes(summary_md)
    col1, col2 = st.columns(2)
    col1.download_button(
        "Gunluk ozet indir (Markdown)",
        summary_md,
        file_name="gunluk_ozet.md",
        mime="text/markdown",
        use_container_width=True,
    )
    col2.download_button(
        "Gunluk ozet indir (PDF)",
        summary_pdf,
        file_name="gunluk_ozet.pdf",
        mime="application/pdf",
        use_container_width=True,
    )


def render_ai_report(client, data: dict, report_depth: str):
    st.subheader("AI Strateji Raporu")
    st.caption(f"Prompt seviyesi: {report_depth}")
    if not client:
        st.info("OPENROUTER_API_KEY yok. AI raporu pasif.")
        return
    if st.button("AI raporu olustur", use_container_width=True):
        with st.spinner("AI raporu hazirlaniyor..."):
            try:
                report = generate_strategy_report(client, data, depth=report_depth)
                st.markdown(f"<div class='report-box'>{report}</div>", unsafe_allow_html=True)
            except (APIConnectionError, APITimeoutError, RateLimitError, APIError, ValueError) as exc:
                st.error(f"AI hatasi: {exc}")


def render_news_tab(data: dict):
    col_news, col_tv = st.columns([1, 1])
    with col_news:
        st.subheader("Son Kripto Haberleri")
        news = data.get("NEWS", [])
        if news:
            for item in news:
                st.markdown(
                    f"""
                    <div class="news-card">
                        <a href="{item['url']}" target="_blank">{clean_text(item['title'])}</a>
                        <div class="news-meta">{clean_text(item['time'])} | {clean_text(item['source'])}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Haber yuklenemedi.")
    with col_tv:
        st.subheader("Canli Haber Bandi")
        components.html(
            """
            <div class="tradingview-widget-container">
            <div class="tradingview-widget-container__widget"></div>
            <script src="https://s3.tradingview.com/external-embedding/embed-widget-timeline.js" async>
            {"feedMode":"all_symbols","isTransparent":true,"displayMode":"regular",
            "width":"100%","height":"800","colorTheme":"dark","locale":"tr"}</script></div>
            """,
            height=820,
        )


def render_all_metrics_tab(data: dict):
    st.subheader("Tum Metrikler")
    rows = [(key, clean_text(value)) for key, value in data.items() if key != "_health"]
    st.dataframe(pd.DataFrame(rows, columns=["Metrik", "Deger"]), use_container_width=True, hide_index=True)


def render_overview_tab(data: dict, brief: dict, analytics: dict, alerts: list[dict]):
    hero_col, context_col = st.columns([1.75, 1.05])
    with hero_col:
        st.markdown(
            f"""
            <div class="info-panel">
                <div class="panel-kicker">Bitcoin / USD</div>
                <div class="panel-title">{clean_text(data.get('BTC_P', '-'))}</div>
                <div class="panel-copy">
                    24s {clean_text(data.get('BTC_C', '-'))} | 7g {clean_text(data.get('BTC_7D', '-'))} |
                    Hacim {clean_text(data.get('Vol_24h', '-'))} | MCap {clean_text(data.get('BTC_MCap', '-'))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with context_col:
        render_info_panel(
            "Executive View",
            "Bugunun Oyun Plani",
            [
                ("Piyasa rejimi", brief["regime"]["title"]),
                ("Pozisyonlanma", brief["positioning"]["title"]),
                ("Likidite", brief["liquidity"]["title"]),
                ("Odak seviye", brief["focus"]["detail"]),
            ],
            badge_text=brief["focus"]["badge"],
            badge_kind=brief["focus"]["class"],
            copy="Rozetlerin arkasindaki nedenler hemen asagida detayli aciklanir.",
        )

    st.markdown("<br>", unsafe_allow_html=True)
    render_market_brief(brief)
    st.markdown("<br>", unsafe_allow_html=True)

    col_scores, col_matrix = st.columns([1.1, 1.2])
    with col_scores:
        render_score_panel(analytics)
    with col_matrix:
        render_scenario_matrix(analytics)

    st.markdown("<br>", unsafe_allow_html=True)
    col_alerts, col_reasons = st.columns([0.9, 1.3])
    with col_alerts:
        render_alert_panel(alerts)
    with col_reasons:
        render_reasoning_panel(brief)


def render_macro_tab(data: dict):
    cat("Makro Para Politikasi")
    render_cards(
        [
            ("FED", data.get("FED", "-"), ""),
            ("M2 YoY", data.get("M2", "-"), ""),
            ("US10Y", data.get("US10Y", "-"), data.get("US10Y_C", "")),
            ("DXY", data.get("DXY", "-"), data.get("DXY_C", "")),
            ("VIX", data.get("VIX", "-"), data.get("VIX_C", "")),
            ("BTC-SP500", str(data.get("Corr_SP500", "-")), ""),
            ("BTC-Gold", str(data.get("Corr_Gold", "-")), ""),
            ("USD/TRY", data.get("USDTRY", "-"), data.get("USDTRY_C", "")),
        ],
        cols=4,
    )
    st.markdown("<br>", unsafe_allow_html=True)
    cat("Likidite ve Breadth")
    render_cards(
        [
            ("ETF Netflow", data.get("ETF_FLOW_TOTAL", "-"), data.get("ETF_FLOW_DATE", "")),
            ("USDT.D", data.get("USDT_D", "-"), ""),
            ("Stable.C.D", data.get("STABLE_C_D", "-"), ""),
            ("TOTAL", data.get("TOTAL_CAP", "-"), ""),
            ("TOTAL2", data.get("TOTAL2_CAP", "-"), ""),
            ("TOTAL3", data.get("TOTAL3_CAP", "-"), ""),
            ("OTHERS", data.get("OTHERS_CAP", "-"), ""),
            ("Total Stable", data.get("Total_Stable", "-"), ""),
        ],
        cols=4,
    )


def render_report_tab(
    client, data: dict, brief: dict, analytics: dict, alerts: list[dict], health_summary: dict, report_depth: str
):
    col_chart, col_side = st.columns([2.0, 1.1])
    with col_chart:
        st.subheader("Canli BTC/USDT Grafigi")
        components.html(
            """
            <div style="height:520px;">
            <script src="https://s3.tradingview.com/tv.js"></script>
            <script>new TradingView.widget({autosize:true,symbol:"BINANCE:BTCUSDT",
            interval:"D",theme:"dark",style:"1",locale:"tr",toolbar_bg:"#070d1a",
            container_id:"tv_main"});</script>
            <div id="tv_main" style="height:100%;"></div></div>
            """,
            height=540,
        )
        st.divider()
        render_downloads(data, brief, analytics, alerts, health_summary)
    with col_side:
        st.subheader("Ekonomik Takvim")
        components.html(
            """
            <div class="tradingview-widget-container">
            <div class="tradingview-widget-container__widget"></div>
            <script src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
            {"colorTheme":"dark","isTransparent":true,"width":"100%","height":"480",
            "locale":"tr","importanceFilter":"0,1","currencyFilter":"USD,EUR"}</script></div>
            """,
            height=500,
        )
        st.divider()
        render_ai_report(client, data, report_depth)


init_preferences()
preferences = st.session_state["preferences"]
client = build_openrouter_client(OPENROUTER_API_KEY) if OPENROUTER_API_KEY else None
render_preferences_panel()
preferences = st.session_state["preferences"]

last_updated = pd.Timestamp.now(tz="Europe/Istanbul").strftime("%d.%m.%Y %H:%M:%S")
with st.spinner("Piyasa verileri yukleniyor..."):
    data = load_terminal_data(FRED_API_KEY)
    current_health = merge_source_health(st.session_state.get("source_health"), data.pop("_health", {}))
    data["_health"] = current_health
    st.session_state["source_health"] = current_health

health_summary = build_health_summary(data.get("_health", {}))
brief = build_market_brief(data)
analytics = build_analytics_payload(data)
alerts = build_alerts(data, preferences.get("thresholds", {}))

render_page_header(last_updated, health_summary)
render_health_alerts(health_summary)
render_sidebar(data, brief, last_updated, health_summary, preferences, alerts)
render_pinned_dashboard(data, preferences.get("pinned_metrics", DEFAULT_PINNED_METRICS))

if preferences.get("view_mode") == "Basit":
    tabs = st.tabs(["Genel Bakis", "Makro", "Rapor"])
    with tabs[0]:
        render_overview_tab(data, brief, analytics, alerts)
    with tabs[1]:
        render_macro_tab(data)
    with tabs[2]:
        render_report_tab(
            client, data, brief, analytics, alerts, health_summary, preferences.get("report_depth", "Orta")
        )
else:
    tabs = st.tabs(["Genel Bakis", "Makro", "Rapor", "Haberler", "Tum Metrikler"])
    with tabs[0]:
        render_overview_tab(data, brief, analytics, alerts)
    with tabs[1]:
        render_macro_tab(data)
    with tabs[2]:
        render_report_tab(
            client, data, brief, analytics, alerts, health_summary, preferences.get("report_depth", "Orta")
        )
    with tabs[3]:
        render_news_tab(data)
    with tabs[4]:
        render_all_metrics_tab(data)

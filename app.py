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
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #07111f;
    --bg2: #0b1626;
    --bg3: #102136;
    --panel: rgba(10, 18, 30, 0.82);
    --panel-strong: rgba(12, 24, 39, 0.95);
    --border: rgba(126, 158, 197, 0.16);
    --border-strong: rgba(126, 158, 197, 0.28);
    --accent: #59d4ff;
    --accent-soft: rgba(89, 212, 255, 0.14);
    --green: #38d996;
    --red: #ff7384;
    --yellow: #f1c56c;
    --text: #f4f7fb;
    --muted: #92a6bf;
    --mono: 'IBM Plex Mono', monospace;
    --sans: 'Manrope', sans-serif;
}

html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top right, rgba(89, 212, 255, 0.08), transparent 26%),
        linear-gradient(180deg, #07111f 0%, #091321 100%) !important;
    font-family: var(--sans) !important;
    color: var(--text) !important;
}

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #081221 0%, #0c1728 100%) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="block-container"] {
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

#MainMenu, footer, header { visibility: hidden; }

.terminal-header {
    display: flex;
    justify-content: space-between;
    align-items: stretch;
    padding: 30px 32px;
    margin: 8px 0 16px 0;
    border: 1px solid var(--border-strong);
    border-radius: 24px;
    background:
        radial-gradient(circle at top right, rgba(89, 212, 255, 0.14), transparent 30%),
        linear-gradient(135deg, rgba(10, 18, 31, 0.98) 0%, rgba(10, 27, 43, 0.98) 100%);
    box-shadow: 0 24px 60px rgba(0, 0, 0, 0.24);
    gap: 24px;
}

.hero-kicker, .section-heading, .metric-label, .header-pill, .health-pill, .score-label, .table-head {
    font-family: var(--mono);
}

.hero-kicker {
    font-size: 0.72rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 12px;
}

.terminal-header h1 {
    margin: 0;
    color: #ffffff;
    font-size: 2.45rem;
    line-height: 1.02;
    letter-spacing: -0.05em;
    max-width: 12ch;
}

.header-copy {
    display: grid;
    gap: 12px;
}

.header-subtitle, .section-lead, .panel-copy, .overview-detail, .why-item {
    color: var(--muted);
    opacity: 0.98;
}

.header-subtitle {
    max-width: 70ch;
    font-size: 0.96rem;
    line-height: 1.7;
}

.header-summary {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.summary-chip {
    min-width: 168px;
    padding: 12px 14px;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(126, 158, 197, 0.12);
}

.summary-chip span {
    display: block;
    font-family: var(--mono);
    font-size: 0.66rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 6px;
}

.summary-chip strong {
    display: block;
    color: var(--text);
    font-size: 0.96rem;
    line-height: 1.45;
}

.header-meta {
    min-width: 260px;
    display: grid;
    align-content: space-between;
    justify-items: end;
    gap: 16px;
}

.meta-stack {
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
    font-size: 0.72rem;
}

.status-badge {
    background: var(--accent);
    color: #041624;
    padding: 9px 12px;
    border-radius: 999px;
    font-weight: 700;
    font-family: var(--mono);
    letter-spacing: 0.02em;
}

.meta-caption {
    text-align: right;
    color: var(--muted);
    font-size: 0.82rem;
    line-height: 1.6;
    max-width: 30ch;
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

.section-heading {
    margin: 8px 0 12px 0;
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--accent);
}

.section-lead {
    margin: 0 0 14px 0;
    padding: 13px 16px;
    border-radius: 16px;
    border: 1px solid var(--border);
    background: rgba(12, 22, 35, 0.74);
    font-size: 0.9rem;
    line-height: 1.6;
}

.notice-bar {
    margin-bottom: 10px;
    padding: 12px 14px;
    border-radius: 14px;
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    background: rgba(11, 19, 31, 0.82);
    color: var(--text);
    font-size: 0.88rem;
}

.notice-warning { border-left-color: var(--yellow); }
.notice-error { border-left-color: var(--red); }

.metric-card, .overview-card, .info-panel, .surface {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 18px 36px rgba(0, 0, 0, 0.16);
    height: 100%;
}

.surface-compact {
    padding: 18px 20px;
}

.metric-card {
    min-height: 116px;
    border-radius: 16px;
    padding: 18px;
}

.metric-card::before {
    content: none;
}

.metric-value {
    font-family: var(--sans);
    font-size: 1.5rem;
    color: #fff;
    font-weight: 800;
    line-height: 1.15;
    letter-spacing: -0.04em;
    margin-top: 10px;
}

.metric-delta-pos { color: var(--green); font-size: 0.8rem; font-family: var(--mono); }
.metric-delta-neg { color: var(--red); font-size: 0.8rem; font-family: var(--mono); }
.metric-delta-neu { color: var(--muted); font-size: 0.8rem; font-family: var(--mono); }

.metric-label {
    color: var(--muted);
    font-size: 0.68rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
}

.panel-kicker {
    color: var(--accent);
    font-size: 0.72rem;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    font-family: var(--mono);
}

.panel-title {
    margin-top: 8px;
    font-size: 1.28rem;
    font-weight: 700;
    letter-spacing: -0.03em;
    color: var(--text);
}

.spotlight-price {
    margin-top: 12px;
    font-size: 2.8rem;
    line-height: 0.98;
    font-weight: 800;
    letter-spacing: -0.06em;
    color: #ffffff;
}

.spotlight-meta {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
    margin-top: 18px;
}

.meta-tile {
    padding: 14px 15px;
    border-radius: 14px;
    border: 1px solid rgba(126, 158, 197, 0.12);
    background: rgba(255, 255, 255, 0.03);
}

.meta-tile-label {
    display: block;
    font-family: var(--mono);
    font-size: 0.66rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 8px;
}

.meta-tile-value {
    display: block;
    color: var(--text);
    font-size: 0.94rem;
    line-height: 1.5;
    font-weight: 700;
}

.panel-row {
    display: grid;
    grid-template-columns: minmax(110px, 0.9fr) minmax(0, 1.2fr);
    gap: 14px;
    padding: 10px 0;
    border-bottom: 1px solid rgba(30, 45, 70, 0.92);
}

.panel-row:last-child { border-bottom: none; }
.panel-row span { color: var(--muted); }
.panel-row strong { color: #f4fbff; text-align: right; line-height: 1.55; }

.signal-long, .signal-short, .signal-neutral {
    font-family: var(--mono);
    font-size: 0.68rem;
    padding: 5px 10px;
    border-radius: 999px;
    display: inline-block;
    font-weight: 700;
    letter-spacing: 0.03em;
}

.signal-long { background: rgba(0,255,136,0.12); border: 1px solid var(--green); color: var(--green); }
.signal-short { background: rgba(255,59,92,0.12); border: 1px solid var(--red); color: var(--red); }
.signal-neutral { background: rgba(255,214,0,0.10); border: 1px solid var(--yellow); color: var(--yellow); }

.why-list { margin-top: 14px; display: grid; gap: 6px; }
.why-item {
    padding-top: 8px;
    border-top: 1px solid rgba(126, 158, 197, 0.12);
    font-size: 0.84rem;
    line-height: 1.55;
}

.report-box {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 24px 28px;
    line-height: 1.8;
    font-size: 0.95em;
}

[data-testid="stTabs"] {
    margin-top: 14px;
}

[data-testid="stTabs"] { margin-top: 12px; }
[data-testid="stTab"] {
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    border-radius: 0 !important;
    padding: 12px 2px !important;
    margin-right: 22px !important;
    color: var(--muted) !important;
    font-weight: 600 !important;
}
[data-testid="stTab"][aria-selected="true"] {
    background: transparent !important;
    border-color: var(--accent) !important;
    color: var(--text) !important;
}

.news-card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.news-card a { color: #e0eef8; text-decoration: none; font-weight: 600; }
.news-meta { color: var(--muted); font-size: 0.72em; margin-top: 5px; font-family: var(--mono); }

.score-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 12px;
    margin-top: 18px;
}

.score-pill {
    padding: 14px 15px;
    border-radius: 16px;
    border: 1px solid rgba(126, 158, 197, 0.12);
    background: rgba(255, 255, 255, 0.03);
}

.score-label {
    display: block;
    color: var(--muted);
    font-size: 0.66rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.score-value {
    display: block;
    margin-top: 8px;
    color: var(--text);
    font-size: 1.8rem;
    line-height: 1;
    font-weight: 800;
    letter-spacing: -0.05em;
}

.matrix-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 14px;
}

.matrix-table th,
.matrix-table td {
    padding: 12px 10px;
    border-bottom: 1px solid rgba(126, 158, 197, 0.12);
    text-align: left;
    vertical-align: top;
}

.matrix-table th {
    color: var(--muted);
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    font-family: var(--mono);
}

.matrix-table td {
    color: var(--text);
    font-size: 0.9rem;
    line-height: 1.6;
}

.alert-list {
    display: grid;
    gap: 10px;
    margin-top: 16px;
}

.alert-item {
    padding: 12px 14px;
    border-radius: 14px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(126, 158, 197, 0.1);
}

.alert-item strong {
    display: block;
    color: var(--text);
    margin-bottom: 4px;
}

.alert-item span {
    color: var(--muted);
    line-height: 1.55;
    font-size: 0.88rem;
}

.sidebar-note {
    padding: 12px 14px;
    border-radius: 14px;
    border: 1px solid var(--border);
    background: rgba(255, 255, 255, 0.03);
    color: var(--muted);
    font-size: 0.84rem;
    line-height: 1.6;
}

[data-testid="stButton"] > button,
[data-testid="stDownloadButton"] > button {
    border-radius: 14px !important;
    border: 1px solid var(--border-strong) !important;
    background: rgba(14, 28, 46, 0.92) !important;
    color: var(--text) !important;
    font-weight: 700 !important;
}

[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid var(--border);
}

@media (max-width: 900px) {
    .terminal-header {
        padding: 22px 20px;
        align-items: flex-start;
        flex-direction: column;
    }
    .header-meta { justify-items: start; min-width: 0; }
    .meta-stack { justify-content: flex-start; }
    .meta-caption { text-align: left; }
    .header-summary { display: grid; }
    .spotlight-meta { grid-template-columns: 1fr; }
    .score-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .panel-row { grid-template-columns: 1fr; }
    .panel-row strong { text-align: left; }
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
    with st.sidebar.expander("Gorunum ve Uyarilar", expanded=False):
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
    cat("Market Pulse")
    render_cards(pinned_items, cols=4)


def render_score_panel(analytics: dict):
    scores = analytics["scores"]
    score_items = [("Genel", scores["overall"]), *scores["subscores"].items()]
    score_html = "".join(
        f"""
        <div class="score-pill">
            <span class="score-label">{clean_text(label)}</span>
            <span class="score-value">{clean_text(value)}/100</span>
        </div>
        """
        for label, value in score_items
    )
    st.markdown(
        f"""
        <div class="surface">
            <div class="panel-kicker">Risk Skoru</div>
            <div class="panel-title">Rejim Haritasi</div>
            <div class="panel-copy">Likidite, volatilite, pozisyonlanma ve breadth ayni tabloda okunur.</div>
            <div class="score-grid">{score_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_scenario_matrix(analytics: dict):
    rows_html = "".join(
        f"""
        <tr>
            <td>{clean_text(row['Scenario'])}</td>
            <td>{clean_text(row['Trigger'])}</td>
            <td>{clean_text(row['Follow-through'])}</td>
        </tr>
        """
        for row in analytics["scenarios"]
    )
    st.markdown(
        f"""
        <div class="surface">
            <div class="panel-kicker">Execution Map</div>
            <div class="panel-title">Senaryo Matrisi</div>
            <div class="panel-copy">Bir sonraki hareketin hangi kosullarda teyit edilecegini tek tabloda gosterir.</div>
            <table class="matrix-table">
                <thead>
                    <tr>
                        <th>Senaryo</th>
                        <th>Trigger</th>
                        <th>Takip sinyali</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_alert_panel(alerts: list[dict]):
    if alerts:
        alert_html = "".join(
            f"""
            <div class="alert-item">
                <strong>{clean_text(alert['title'])}</strong>
                <span>{clean_text(alert['detail'])}</span>
            </div>
            """
            for alert in alerts
        )
        title = "Aktif alarmlar esiklerin ustune cikti."
    else:
        alert_html = """
        <div class="alert-item">
            <strong>Aktif alarm yok</strong>
            <span>Funding, VIX ve ETF esikleri su an sessiz. Esik asiminda uyarilar burada toplanir.</span>
        </div>
        """
        title = "Esik bazli risk akisi sakin."
    st.markdown(
        f"""
        <div class="surface">
            <div class="panel-kicker">Alert Feed</div>
            <div class="panel-title">{title}</div>
            <div class="panel-copy">Panelin operasyonel uyarilari bu kutuda tutulur; gereksiz tekrarlar ana yuzeyden kaldirildi.</div>
            <div class="alert-list">{alert_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
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
            "width":"100%","height":"620","colorTheme":"dark","locale":"tr"}</script></div>
            """,
            height=640,
        )


def render_all_metrics_tab(data: dict):
    st.subheader("Tum Metrikler")
    rows = [(key, clean_text(value)) for key, value in data.items() if key not in {"_health", "NEWS"}]
    st.dataframe(pd.DataFrame(rows, columns=["Metrik", "Deger"]), use_container_width=True, hide_index=True)


def render_overview_tab(data: dict, brief: dict, analytics: dict, alerts: list[dict]):
    hero_col, context_col = st.columns([1.45, 0.95])
    with hero_col:
        st.markdown(
            f"""
            <div class="surface">
                <div class="panel-kicker">Primary Market</div>
                <div class="panel-title">Bitcoin / USD</div>
                <div class="spotlight-price">{clean_text(data.get('BTC_P', '-'))}</div>
                <div class="panel-copy">
                    Ana fiyat kutusu sadece calisma yuzeyi icin gerekli bilgiyi bir arada tutar.
                </div>
                <div class="spotlight-meta">
                    <div class="meta-tile">
                        <span class="meta-tile-label">24 Saat</span>
                        <span class="meta-tile-value">{clean_text(data.get('BTC_C', '-'))}</span>
                    </div>
                    <div class="meta-tile">
                        <span class="meta-tile-label">7 Gun</span>
                        <span class="meta-tile-value">{clean_text(data.get('BTC_7D', '-'))}</span>
                    </div>
                    <div class="meta-tile">
                        <span class="meta-tile-label">Hacim</span>
                        <span class="meta-tile-value">{clean_text(data.get('Vol_24h', '-'))}</span>
                    </div>
                    <div class="meta-tile">
                        <span class="meta-tile-label">Piyasa Degeri</span>
                        <span class="meta-tile-value">{clean_text(data.get('BTC_MCap', '-'))}</span>
                    </div>
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
            copy="Sag kolonu not ve takip listesi icin ayirdim; ana yuzeyde tekrar eden ozet kartlarini kaldirdim.",
        )

    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
    render_market_brief(brief)
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    col_matrix, col_side = st.columns([1.3, 0.9])
    with col_matrix:
        render_scenario_matrix(analytics)
    with col_side:
        render_score_panel(analytics)
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        render_alert_panel(alerts)


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
            <div id="tv_main" style="height:100%;"></div>
            <script src="https://s3.tradingview.com/tv.js"></script>
            <script>new TradingView.widget({autosize:true,symbol:"BINANCE:BTCUSDT",
            interval:"D",theme:"dark",style:"1",locale:"tr",toolbar_bg:"#070d1a",
            container_id:"tv_main"});</script>
            </div>
            """,
            height=540,
        )
        st.divider()
        render_downloads(data, brief, analytics, alerts, health_summary)
    with col_side:
        st.subheader("Makro Takvim")
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

render_page_header(last_updated, health_summary, brief, preferences)
render_health_alerts(health_summary)
render_sidebar(data, brief, last_updated, health_summary, preferences, alerts)
render_pinned_dashboard(data, preferences.get("pinned_metrics", DEFAULT_PINNED_METRICS))

if preferences.get("view_mode") == "Basit":
    tabs = st.tabs(["Terminal", "Makro", "Strateji"])
    with tabs[0]:
        render_overview_tab(data, brief, analytics, alerts)
    with tabs[1]:
        render_macro_tab(data)
    with tabs[2]:
        render_report_tab(
            client, data, brief, analytics, alerts, health_summary, preferences.get("report_depth", "Orta")
        )
else:
    tabs = st.tabs(["Terminal", "Makro", "Strateji", "Haber Akisi", "Veri Tablosu"])
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

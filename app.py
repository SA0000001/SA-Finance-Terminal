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
    markdown_to_basic_pdf_bytes,
)
from domain.market_brief import build_market_brief
from services.ai_service import build_openrouter_client, generate_strategy_report
from services.health import build_health_summary, merge_source_health
from services.market_data import load_terminal_data
from services.preferences import load_preferences, save_preferences
from ui.components import (
    cat,
    clean_text,
    display_value,
    render_cards,
    render_data_table_card,
    render_info_panel,
    render_market_brief,
)
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
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Manrope:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #07111f;
    --bg2: #0b1626;
    --bg3: #102136;
    --panel: rgba(10, 18, 30, 0.82);
    --panel-soft: rgba(12, 20, 32, 0.72);
    --panel-strong: rgba(12, 24, 39, 0.95);
    --border: rgba(126, 158, 197, 0.16);
    --border-strong: rgba(126, 158, 197, 0.28);
    --accent: #59d4ff;
    --accent-soft: rgba(89, 212, 255, 0.14);
    --accent-line: rgba(89, 212, 255, 0.34);
    --green: #38d996;
    --red: #ff7384;
    --yellow: #f1c56c;
    --text: #f4f7fb;
    --muted: #92a6bf;
    --text-soft: #b4c3d6;
    --mono: 'IBM Plex Mono', monospace;
    --sans: 'Manrope', sans-serif;
    --radius-sm: 14px;
    --radius-md: 20px;
    --radius-lg: 26px;
    --space-1: 8px;
    --space-2: 12px;
    --space-3: 16px;
    --space-4: 24px;
    --shadow-soft: 0 18px 36px rgba(0, 0, 0, 0.16);
    --shadow-strong: 0 24px 60px rgba(0, 0, 0, 0.24);
    --hover-bg: rgba(255, 255, 255, 0.045);
}

html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at top right, rgba(89, 212, 255, 0.08), transparent 26%),
        linear-gradient(180deg, #07111f 0%, #091321 100%) !important;
    font-family: var(--sans) !important;
    color: var(--text) !important;
}

[data-testid="stSidebar"] {
    background:
        linear-gradient(180deg, rgba(8, 18, 33, 0.98) 0%, rgba(12, 23, 40, 0.98) 100%) !important;
    border-right: 1px solid var(--border) !important;
}

[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
    padding-top: 1.2rem;
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
    box-shadow: var(--shadow-strong);
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
    box-shadow: var(--shadow-soft);
    height: 100%;
    backdrop-filter: blur(14px);
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

.metric-placeholder {
    color: var(--muted);
    font-size: 1rem;
    letter-spacing: 0;
    line-height: 1.4;
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

[data-testid="stTab"] {
    background: rgba(10, 17, 29, 0.62) !important;
    border: 1px solid rgba(126, 158, 197, 0.08) !important;
    border-bottom: 1px solid rgba(126, 158, 197, 0.08) !important;
    border-radius: 999px !important;
    padding: 10px 16px !important;
    margin-right: 12px !important;
    color: var(--muted) !important;
    font-weight: 600 !important;
    transition: all 180ms ease !important;
}
[data-testid="stTab"][aria-selected="true"] {
    background: rgba(14, 27, 42, 0.98) !important;
    border-color: var(--accent-line) !important;
    color: var(--text) !important;
    box-shadow: inset 0 -2px 0 rgba(89, 212, 255, 0.9);
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

.regime-panel {
    padding: 24px;
}

.regime-top {
    display: grid;
    grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.85fr);
    gap: 16px;
    margin-top: 18px;
}

.regime-hero,
.fragility-card,
.factor-card {
    border: 1px solid rgba(126, 158, 197, 0.12);
    border-radius: 22px;
    background: rgba(255, 255, 255, 0.025);
    backdrop-filter: blur(12px);
}

.regime-hero {
    padding: 22px;
}

.regime-hero-head,
.factor-head,
.factor-meta,
.contribution-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    align-items: flex-start;
}

.regime-overlay {
    display: inline-flex;
    align-items: center;
    padding: 7px 12px;
    border-radius: 999px;
    border: 1px solid rgba(126, 158, 197, 0.16);
    background: rgba(13, 26, 42, 0.74);
    color: var(--text);
    font-size: 0.76rem;
    font-family: var(--mono);
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.regime-main-score {
    margin-top: 18px;
    font-size: 4.1rem;
    line-height: 0.92;
    font-weight: 800;
    letter-spacing: -0.08em;
    color: #ffffff;
}

.regime-score-copy {
    margin-top: 10px;
    color: var(--muted);
    font-size: 0.95rem;
    line-height: 1.65;
    max-width: 56ch;
}

.regime-summary-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 12px;
    margin-top: 18px;
}

.summary-stat {
    padding: 14px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid rgba(126, 158, 197, 0.08);
}

.summary-stat-label {
    display: block;
    color: var(--muted);
    font-size: 0.66rem;
    font-family: var(--mono);
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.summary-stat-value {
    display: block;
    margin-top: 8px;
    color: var(--text);
    font-size: 1rem;
    line-height: 1.4;
    font-weight: 700;
}

.contribution-list {
    margin-top: 18px;
    display: grid;
    gap: 10px;
}

.contribution-meta {
    min-width: 86px;
    text-align: right;
    color: var(--text);
    font-weight: 700;
    font-size: 0.84rem;
}

.contribution-copy {
    color: var(--text-soft);
    font-size: 0.86rem;
    line-height: 1.5;
}

.contribution-bar {
    position: relative;
    width: 100%;
    height: 8px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.06);
    margin-top: 6px;
    overflow: hidden;
}

.contribution-bar-fill {
    position: absolute;
    inset: 0 auto 0 0;
    height: 100%;
    border-radius: 999px;
    background: linear-gradient(90deg, rgba(89, 212, 255, 0.82), rgba(89, 212, 255, 0.28));
}

.fragility-card {
    padding: 20px;
}

.fragility-score {
    margin-top: 14px;
    font-size: 2.8rem;
    line-height: 0.95;
    font-weight: 800;
    letter-spacing: -0.07em;
    color: #fff;
}

.fragility-label {
    margin-top: 8px;
    color: var(--yellow);
    font-size: 0.9rem;
    font-family: var(--mono);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.fragility-flags {
    display: grid;
    gap: 8px;
    margin-top: 16px;
}

.fragility-flag {
    padding: 10px 12px;
    border-radius: 14px;
    border: 1px solid rgba(126, 158, 197, 0.1);
    background: rgba(255, 255, 255, 0.03);
    color: var(--text-soft);
    font-size: 0.85rem;
    line-height: 1.5;
}

.factor-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px;
    margin-top: 16px;
}

.factor-card {
    padding: 18px;
}

.factor-name {
    color: var(--text);
    font-size: 1rem;
    font-weight: 700;
}

.factor-weight {
    color: var(--muted);
    font-size: 0.74rem;
    font-family: var(--mono);
    letter-spacing: 0.08em;
}

.factor-score-row {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    gap: 12px;
    margin-top: 14px;
}

.factor-score {
    color: var(--text);
    font-size: 2.2rem;
    line-height: 0.95;
    font-weight: 800;
    letter-spacing: -0.07em;
}

.factor-delta {
    font-size: 0.84rem;
    font-family: var(--mono);
    letter-spacing: 0.05em;
}

.delta-up { color: var(--green); }
.delta-down { color: var(--red); }
.delta-flat { color: var(--muted); }

.factor-copy {
    margin-top: 10px;
    color: var(--text-soft);
    font-size: 0.88rem;
    line-height: 1.6;
}

.factor-meta {
    margin-top: 12px;
    color: var(--muted);
    font-size: 0.8rem;
    line-height: 1.5;
}

.driver-list {
    margin-top: 14px;
    display: grid;
    gap: 8px;
}

.driver-item {
    padding-top: 8px;
    border-top: 1px solid rgba(126, 158, 197, 0.1);
    color: var(--text-soft);
    font-size: 0.84rem;
    line-height: 1.55;
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

[data-testid="stExpander"] {
    border: 1px solid rgba(126, 158, 197, 0.12) !important;
    border-radius: 18px !important;
    background: linear-gradient(180deg, rgba(12, 21, 34, 0.82), rgba(9, 17, 28, 0.9)) !important;
    overflow: hidden;
}

[data-testid="stExpander"] details summary {
    padding: 0.2rem 0.35rem !important;
}

[data-testid="stExpanderDetails"] {
    padding-top: 0.3rem !important;
}

.health-alert-surface {
    margin: 0 0 18px 0;
}

.health-issue-list,
.source-health-list {
    display: grid;
    gap: 10px;
    margin-top: 16px;
}

.health-issue-row,
.source-health-row {
    display: flex;
    justify-content: space-between;
    gap: 14px;
    padding: 14px 16px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.028);
    border: 1px solid rgba(126, 158, 197, 0.1);
}

.health-issue-source,
.source-health-source {
    color: var(--text);
    font-size: 0.92rem;
    font-weight: 700;
}

.health-issue-error,
.source-health-detail {
    color: var(--muted);
    font-size: 0.84rem;
    line-height: 1.6;
    margin-top: 4px;
}

.health-issue-meta,
.source-health-meta {
    min-width: 180px;
    text-align: right;
    display: grid;
    justify-items: end;
    gap: 6px;
    color: var(--muted);
    font-size: 0.78rem;
}

.health-issue-status,
.source-health-status {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 6px 10px;
    border-radius: 999px;
    font-family: var(--mono);
    font-size: 0.68rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    border: 1px solid rgba(126, 158, 197, 0.16);
    color: var(--text);
}

.health-issue-fail,
.source-status-fail {
    border-color: rgba(255, 115, 132, 0.38);
    color: var(--red);
}

.health-issue-stale,
.source-status-stale {
    border-color: rgba(241, 197, 108, 0.38);
    color: var(--yellow);
}

.health-issue-ok,
.source-status-ok {
    border-color: rgba(56, 217, 150, 0.34);
    color: var(--green);
}

.control-rail-meta {
    color: var(--muted);
    font-size: 0.88rem;
    line-height: 1.65;
    padding-top: 8px;
}

.decision-grid {
    display: grid;
    grid-template-columns: 1.15fr 0.85fr;
    gap: 18px;
    align-items: start;
}

.command-surface {
    display: grid;
    gap: 18px;
}

.command-title {
    color: var(--text);
    font-size: 1.72rem;
    line-height: 1.08;
    font-weight: 780;
    letter-spacing: -0.04em;
}

.command-copy {
    color: var(--text-soft);
    font-size: 0.96rem;
    line-height: 1.75;
    max-width: 60ch;
}

.command-stat-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 12px;
}

.command-stat {
    padding: 14px;
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.028);
    border: 1px solid rgba(126, 158, 197, 0.12);
}

.command-stat-label {
    color: var(--muted);
    font-size: 0.68rem;
    font-family: var(--mono);
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.command-stat-value {
    display: block;
    margin-top: 8px;
    color: var(--text);
    font-size: 0.98rem;
    line-height: 1.55;
    font-weight: 720;
}

.command-columns {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 14px;
}

.command-block {
    padding: 16px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.022);
    border: 1px solid rgba(126, 158, 197, 0.1);
}

.command-block-title {
    color: var(--text);
    font-size: 0.86rem;
    font-weight: 720;
    letter-spacing: -0.01em;
}

.command-list {
    display: grid;
    gap: 10px;
    margin-top: 12px;
}

.command-list-item {
    color: var(--muted);
    font-size: 0.88rem;
    line-height: 1.65;
    padding-left: 14px;
    position: relative;
}

.command-list-item::before {
    content: "";
    width: 6px;
    height: 6px;
    border-radius: 999px;
    background: var(--accent);
    position: absolute;
    left: 0;
    top: 0.62rem;
    opacity: 0.8;
}

.signal-deck-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
}

.signal-deck {
    background: linear-gradient(180deg, rgba(12, 20, 33, 0.92), rgba(8, 15, 24, 0.95));
    border: 1px solid rgba(126, 158, 197, 0.12);
    border-radius: 22px;
    padding: 18px;
    box-shadow: 0 18px 40px rgba(0, 0, 0, 0.15);
    height: 100%;
}

.signal-deck-top {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
}

.signal-deck-title {
    color: var(--text);
    font-size: 1.14rem;
    font-weight: 740;
    letter-spacing: -0.03em;
}

.signal-deck-score {
    text-align: right;
}

.signal-deck-score strong {
    display: block;
    color: var(--text);
    font-size: 1.18rem;
    font-weight: 780;
}

.signal-deck-score span {
    color: var(--muted);
    font-size: 0.72rem;
    font-family: var(--mono);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.signal-deck-copy {
    color: var(--muted);
    font-size: 0.88rem;
    line-height: 1.65;
    margin-top: 10px;
}

.signal-chip-row {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-top: 14px;
}

.signal-chip {
    display: inline-flex;
    align-items: center;
    padding: 6px 10px;
    border-radius: 999px;
    font-size: 0.7rem;
    font-family: var(--mono);
    color: var(--text-soft);
    border: 1px solid rgba(126, 158, 197, 0.14);
    background: rgba(255, 255, 255, 0.028);
}

.signal-mini-list {
    display: grid;
    gap: 10px;
    margin-top: 16px;
}

.signal-mini-row {
    display: flex;
    justify-content: space-between;
    gap: 12px;
    border-bottom: 1px solid rgba(126, 158, 197, 0.08);
    padding-bottom: 9px;
}

.signal-mini-row:last-child {
    border-bottom: none;
    padding-bottom: 0;
}

.signal-mini-row span {
    color: var(--muted);
    font-size: 0.82rem;
    line-height: 1.5;
}

.signal-mini-row strong {
    color: var(--text);
    font-size: 0.84rem;
    line-height: 1.5;
    text-align: right;
}

.reports-grid {
    display: grid;
    grid-template-columns: 1.2fr 0.8fr;
    gap: 18px;
}

[data-testid="stButton"] > button,
[data-testid="stDownloadButton"] > button {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border-strong) !important;
    background: linear-gradient(180deg, rgba(18, 31, 47, 0.96), rgba(11, 21, 34, 0.96)) !important;
    color: var(--text) !important;
    font-weight: 700 !important;
    transition: transform 160ms ease, border-color 160ms ease, background 160ms ease !important;
    min-height: 2.8rem !important;
}

[data-testid="stButton"] > button:hover,
[data-testid="stDownloadButton"] > button:hover {
    border-color: rgba(116, 193, 233, 0.42) !important;
    transform: translateY(-1px);
}

[data-testid="stDataFrame"] {
    border-radius: 16px;
    overflow: hidden;
    border: 1px solid var(--border);
}

.hero-grid {
    display: grid;
    grid-template-columns: 1.55fr 1fr;
    gap: 18px;
}

.signal-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 16px;
}

.atlas-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 16px;
}

.data-card {
    background:
        linear-gradient(180deg, rgba(12, 21, 34, 0.92), rgba(8, 15, 25, 0.96));
    border: 1px solid rgba(126, 158, 197, 0.12);
    border-radius: 22px;
    padding: 18px 18px 16px;
    height: 100%;
    box-shadow: 0 18px 42px rgba(0, 0, 0, 0.15);
    backdrop-filter: blur(12px);
}

.data-card-head {
    padding-bottom: 12px;
    margin-bottom: 12px;
    border-bottom: 1px solid rgba(126, 158, 197, 0.12);
}

.table-kicker {
    color: var(--accent);
    font-family: var(--mono);
    font-size: 0.66rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-bottom: 8px;
}

.table-title {
    color: var(--text);
    font-size: 1.08rem;
    font-weight: 700;
    letter-spacing: -0.02em;
}

.table-caption {
    color: var(--muted);
    font-size: 0.84rem;
    line-height: 1.55;
    margin: 8px 0 14px;
}

.data-grid-head {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(120px, 0.9fr);
    gap: 14px;
    padding: 0 2px 10px;
    border-bottom: 1px solid rgba(126, 158, 197, 0.12);
    color: var(--muted);
    font-size: 0.68rem;
    font-family: var(--mono);
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

.data-grid-head span:last-child {
    text-align: right;
}

.data-rows {
    display: grid;
}

.data-row {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(120px, 0.9fr);
    gap: 14px;
    padding: 12px 2px;
    border-bottom: 1px solid rgba(126, 158, 197, 0.10);
    transition: background 160ms ease;
}

.data-row:last-child {
    border-bottom: none;
}

.data-row:hover {
    background: rgba(255, 255, 255, 0.02);
}

.data-key {
    color: var(--text-soft);
    font-size: 0.88rem;
    line-height: 1.55;
}

.data-value {
    color: var(--text);
    font-size: 0.9rem;
    line-height: 1.55;
    font-weight: 650;
    text-align: right;
    word-break: break-word;
}

.table-section-title {
    color: var(--text);
    font-size: 1.6rem;
    font-weight: 760;
    letter-spacing: -0.04em;
    margin: 8px 0 6px;
}

.table-section-copy {
    color: var(--muted);
    font-size: 0.92rem;
    line-height: 1.65;
    margin-bottom: 16px;
}

.deck-card {
    background: linear-gradient(180deg, rgba(11, 19, 31, 0.92), rgba(8, 15, 24, 0.94));
    border: 1px solid rgba(126, 158, 197, 0.14);
    border-radius: 24px;
    padding: 24px;
    box-shadow: 0 22px 54px rgba(0, 0, 0, 0.18);
    height: 100%;
    backdrop-filter: blur(14px);
}

.deck-title {
    color: var(--text);
    font-size: 1.56rem;
    font-weight: 760;
    letter-spacing: -0.05em;
}

.deck-copy {
    color: var(--muted);
    line-height: 1.65;
    font-size: 0.92rem;
    margin-top: 10px;
}

.deck-stats {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
    margin-top: 18px;
}

.deck-stat {
    padding: 14px;
    border-radius: 16px;
    border: 1px solid rgba(126, 158, 197, 0.1);
    background: rgba(255, 255, 255, 0.025);
}

.deck-stat span {
    display: block;
}

.deck-stat-label {
    color: var(--muted);
    font-size: 0.66rem;
    font-family: var(--mono);
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.deck-stat-value {
    margin-top: 8px;
    color: var(--text);
    font-weight: 750;
    font-size: 1rem;
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
    .regime-top,
    .factor-grid,
    .regime-summary-grid,
    .decision-grid,
    .command-stat-grid,
    .command-columns,
    .signal-deck-grid,
    .reports-grid { grid-template-columns: 1fr; }
    .panel-row { grid-template-columns: 1fr; }
    .panel-row strong { text-align: left; }
    .hero-grid,
    .signal-grid,
    .atlas-grid,
    .deck-stats { grid-template-columns: 1fr; }
}
</style>
""",
    unsafe_allow_html=True,
)

MACRO_MARKET_SECTIONS = [
    {
        "title": "Global Hisse Endeksleri",
        "kicker": "US Amerika",
        "caption": "Risk istahini ve global equity yonunu tek bolumde toplar.",
        "rows": [("S&P 500", "SP500"), ("NASDAQ", "NASDAQ"), ("Dow Jones", "DOW")],
    },
    {
        "title": "Global Hisse Endeksleri",
        "kicker": "Avrupa",
        "caption": "Avrupa cekirdegi ve yerel risk tonu.",
        "rows": [("DAX", "DAX"), ("FTSE 100", "FTSE"), ("BIST 100", "BIST100")],
    },
    {
        "title": "Global Hisse Endeksleri",
        "kicker": "Asya",
        "caption": "Asya seansinin risk aktarimi.",
        "rows": [("Nikkei 225", "NIKKEI"), ("Hang Seng", "HSI"), ("VIX", "VIX")],
    },
    {
        "title": "Emtialar",
        "kicker": "Metaller",
        "caption": "Defansif ve endustriyel emtia akisi.",
        "rows": [("Altin / oz", "GOLD"), ("Gumus / oz", "SILVER"), ("Bakir", "COPPER")],
    },
    {
        "title": "Emtialar",
        "kicker": "Enerji ve Tarim",
        "caption": "Enflasyon ve buyume baskisinin hizli ozeti.",
        "rows": [("Ham Petrol (WTI)", "OIL"), ("Dogalgaz", "NATGAS"), ("Bugday", "WHEAT")],
    },
    {
        "title": "Doviz Kurlari",
        "kicker": "Majors",
        "caption": "Global dolar akisina karsi ana pariteler.",
        "rows": [("EUR / USD", "EURUSD"), ("GBP / USD", "GBPUSD"), ("USD / JPY", "USDJPY")],
    },
    {
        "title": "Doviz Kurlari",
        "kicker": "Crosses",
        "caption": "Yerel baski ve carry etkisi.",
        "rows": [("USD / CHF", "USDCHF"), ("AUD / USD", "AUDUSD"), ("USD / TRY", "USDTRY")],
    },
    {
        "title": "Makro ve Para Politikasi",
        "kicker": "Core Macro",
        "caption": "Likidite ve policy rejimini okuyan cekirdek set.",
        "rows": [
            ("FED Faizi", "FED"),
            ("M2 YoY", "M2"),
            ("ABD 10Y", "US10Y"),
            ("DXY", "DXY"),
            ("BTC <> SP500", "Corr_SP500"),
            ("BTC <> Altin", "Corr_Gold"),
        ],
    },
]

FLOW_RISK_SECTIONS = [
    {
        "title": "Turev ve Sentiment",
        "kicker": "Positioning Deck",
        "caption": "Turev akis, leverage ve duygu teyidi.",
        "rows": [
            ("Open Interest", "OI"),
            ("Funding Rate", "FR"),
            ("Taker B/S", "Taker"),
            ("L/S Orani", "LS_Ratio"),
            ("Long %", "Long_Pct"),
            ("Short %", "Short_Pct"),
            ("L/S Sinyal", "LS_Signal"),
            ("Korku / Acgozluluk", "FNG"),
            ("FNG Dun", "FNG_PREV"),
        ],
    },
    {
        "title": "Order Book ve ETF",
        "kicker": "Execution Levels",
        "caption": "Destek/direnc ve ETF akisinin ayni masada okunmasi.",
        "rows": [
            ("Destek Duvari", "Sup_Wall"),
            ("Destek Hacmi", "Sup_Vol"),
            ("Direnc Duvari", "Res_Wall"),
            ("Direnc Hacmi", "Res_Vol"),
            ("Tahta Durumu", "Wall_Status"),
            ("Birlesik Sinyal", "ORDERBOOK_SIGNAL"),
            ("Birlesik Detay", "ORDERBOOK_SIGNAL_DETAIL"),
            ("ETF Netflow", "ETF_FLOW_TOTAL"),
            ("ETF Tarih", "ETF_FLOW_DATE"),
            ("Kaynaklar", "ORDERBOOK_SOURCES"),
        ],
    },
    {
        "title": "Stablecoin ve On-Chain",
        "kicker": "Liquidity Plumbing",
        "caption": "Likidite rezervi ve zincir ustu aktivite.",
        "rows": [
            ("Toplam Stable", "Total_Stable"),
            ("USDT", "USDT_MCap"),
            ("USDC", "USDC_MCap"),
            ("DAI", "DAI_MCap"),
            ("Stable.C.D", "STABLE_C_D"),
            ("USDT.D", "USDT_D"),
            ("USDT.D Kaynak", "USDT_D_SOURCE"),
            ("USDT Dominance", "USDT_Dom_Stable"),
            ("Hashrate", "Hash"),
            ("Aktif Adres (est.)", "Active"),
        ],
    },
    {
        "title": "Market Cap Breadth",
        "kicker": "Breadth Layers",
        "caption": "Sermayenin piyasa katmanlarina dagilimi.",
        "rows": [
            ("TOTAL", "TOTAL_CAP"),
            ("TOTAL2", "TOTAL2_CAP"),
            ("TOTAL3", "TOTAL3_CAP"),
            ("OTHERS", "OTHERS_CAP"),
            ("Kaynak", "TOTAL_CAP_SOURCE"),
        ],
    },
]

DATA_ATLAS_SECTIONS = [
    {"title": "BTC ve Kripto", "rows": [("BTC Fiyati", "BTC_P"), ("BTC 24s", "BTC_C"), ("BTC 7g", "BTC_7D"), ("BTC MCap", "BTC_MCap"), ("24s Hacim", "Vol_24h"), ("BTC Dominance", "Dom"), ("ETH Dominance", "ETH_Dom"), ("Total MCap", "TOTAL_CAP"), ("Total Hacim", "Total_Vol")]},
    {"title": "Turev ve Sentiment", "rows": [("OI", "OI"), ("Funding Rate", "FR"), ("Taker B/S", "Taker"), ("L/S Orani", "LS_Ratio"), ("Long %", "Long_Pct"), ("Short %", "Short_Pct"), ("L/S Sinyal", "LS_Signal"), ("Korku/Acgozluluk", "FNG"), ("FNG Dun", "FNG_PREV")]},
    {"title": "Order Book ve ETF", "rows": [("Destek Duvari", "Sup_Wall"), ("Destek Hacmi", "Sup_Vol"), ("Direnc Duvari", "Res_Wall"), ("Direnc Hacmi", "Res_Vol"), ("Tahta Durumu", "Wall_Status"), ("Birlesik Sinyal", "ORDERBOOK_SIGNAL"), ("Birlesik Detay", "ORDERBOOK_SIGNAL_DETAIL"), ("Kaynaklar", "ORDERBOOK_SOURCES"), ("ETF Netflow", "ETF_FLOW_TOTAL"), ("ETF Tarih", "ETF_FLOW_DATE"), ("ETF Kaynak", "ETF_FLOW_SOURCE"), ("OKX Destek", "OKX_Sup_Wall")]},
    {"title": "Market Cap Breadth", "rows": [("TOTAL", "TOTAL_CAP"), ("TOTAL2", "TOTAL2_CAP"), ("TOTAL3", "TOTAL3_CAP"), ("OTHERS", "OTHERS_CAP"), ("Kaynak", "TOTAL_CAP_SOURCE")]},
    {"title": "Stablecoin ve On-Chain", "rows": [("Toplam Stable", "Total_Stable"), ("USDT", "USDT_MCap"), ("USDC", "USDC_MCap"), ("DAI", "DAI_MCap"), ("Stable.C.D", "STABLE_C_D"), ("USDT.D", "USDT_D"), ("USDT Dom Stable", "USDT_Dom_Stable"), ("Hashrate", "Hash"), ("Aktif Adres", "Active")]},
    {"title": "Makro ve Para Politikasi", "rows": [("FED Faizi", "FED"), ("M2 YoY", "M2"), ("ABD 10Y", "US10Y"), ("DXY", "DXY"), ("VIX", "VIX"), ("BTC<>SP500", "Corr_SP500"), ("BTC<>Altin", "Corr_Gold")]},
    {"title": "Endeksler ve Emtia", "rows": [("S&P 500", "SP500"), ("NASDAQ", "NASDAQ"), ("DAX", "DAX"), ("NIKKEI", "NIKKEI"), ("BIST100", "BIST100"), ("Altin", "GOLD"), ("Gumus", "SILVER"), ("Petrol", "OIL"), ("Dogalgaz", "NATGAS"), ("Bakir", "COPPER")]},
    {"title": "Forex", "rows": [("EUR/USD", "EURUSD"), ("GBP/USD", "GBPUSD"), ("USD/JPY", "USDJPY"), ("USD/TRY", "USDTRY"), ("USD/CHF", "USDCHF"), ("AUD/USD", "AUDUSD")]},
]

DERIVATIVE_SOURCE_NAMES = [
    "Derivatives Pipeline",
    "OKX Funding",
    "OKX Open Interest",
    "OKX Taker Volume",
    "OKX Long/Short",
    "Gate.io Long/Short",
]


def data_rows(data: dict, items):
    return [(label, data.get(key, "-")) for label, key in items]


def render_table_row(data: dict, sections: list[dict], cols: int):
    columns = st.columns(cols)
    for column, section in zip(columns, sections):
        with column:
            render_data_table_card(
                section["title"],
                data_rows(data, section["rows"]),
                kicker=section.get("kicker", ""),
                caption=section.get("caption", ""),
            )


def init_preferences():
    if "preferences" not in st.session_state:
        st.session_state["preferences"] = load_preferences()


def init_ui_state():
    if "control_rail_open" not in st.session_state:
        st.session_state["control_rail_open"] = True


def render_preferences_panel(host, key_prefix: str = "prefs", *, expanded: bool = False):
    preferences = st.session_state["preferences"]
    with host.expander("Gorunum ve Uyarilar", expanded=expanded):
        view_mode = host.radio(
            "Gorunum modu",
            ["Basit", "Pro"],
            index=0 if preferences.get("view_mode") == "Basit" else 1,
            key=f"{key_prefix}_view_mode",
        )
        report_depth = host.selectbox(
            "Rapor seviyesi",
            ["Kisa", "Orta", "Derin"],
            index=["Kisa", "Orta", "Derin"].index(preferences.get("report_depth", "Orta")),
            key=f"{key_prefix}_report_depth",
        )
        pinned_metrics = host.multiselect(
            "Pinli metrikler",
            options=list(METRIC_LABELS),
            default=preferences.get("pinned_metrics", DEFAULT_PINNED_METRICS),
            format_func=lambda key: METRIC_LABELS.get(key, key),
            key=f"{key_prefix}_pinned_metrics",
        )
        funding_above = host.number_input(
            "Funding > X",
            value=float(preferences["thresholds"].get("funding_above", 0.01)),
            step=0.005,
            format="%.4f",
            key=f"{key_prefix}_funding_above",
        )
        vix_above = host.number_input(
            "VIX > Y",
            value=float(preferences["thresholds"].get("vix_above", 25.0)),
            step=0.5,
            format="%.2f",
            key=f"{key_prefix}_vix_above",
        )
        etf_flow_below = host.number_input(
            "ETF netflow < Z",
            value=float(preferences["thresholds"].get("etf_flow_below", 0.0)),
            step=10.0,
            format="%.1f",
            key=f"{key_prefix}_etf_flow_below",
        )
        if host.button("Ayarlari Kaydet", key=f"{key_prefix}_save", use_container_width=True):
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
            host.success("Ayarlar kaydedildi.")


def get_source_health_rows(health_summary: dict, sources: list[str] | None = None, *, include_ok: bool = False) -> list[dict]:
    rows = list(health_summary.get("rows", []))
    if sources:
        source_set = set(sources)
        rows = [row for row in rows if row.get("Kaynak") in source_set]
    if not include_ok:
        rows = [row for row in rows if row.get("Durum") != "OK"]
    return rows


def render_source_health_surface(title: str, caption: str, rows: list[dict], *, empty_copy: str):
    if not rows:
        st.markdown(
            f"""
            <div class="surface">
                <div class="panel-kicker">Source Health</div>
                <div class="panel-title">{clean_text(title)}</div>
                <div class="panel-copy">{clean_text(empty_copy)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    row_html = "".join(
        f"""
        <div class="source-health-row">
            <div>
                <div class="source-health-source">{clean_text(row['Kaynak'])}</div>
                <div class="source-health-detail">{clean_text(row['Hata'] if row['Hata'] != '-' else 'Son basarili: ' + row['Son basarili'])}</div>
            </div>
            <div class="source-health-meta">
                <span class="source-health-status source-status-{row['Durum'].lower()}">{clean_text(row['Durum'])}</span>
                <span>{clean_text(row['Gecikme'])}</span>
            </div>
        </div>
        """
        for row in rows
    )
    st.markdown(
        f"""
        <div class="surface">
            <div class="panel-kicker">Source Health</div>
            <div class="panel-title">{clean_text(title)}</div>
            <div class="panel-copy">{clean_text(caption)}</div>
            <div class="source-health-list">{row_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_control_rail(data: dict, brief: dict, last_updated: str, health_summary: dict, alerts: list[dict]):
    toolbar_left, toolbar_mid, toolbar_right = st.columns([1.1, 1.0, 2.4])
    rail_open = st.session_state.get("control_rail_open", True)

    with toolbar_left:
        if st.button(
            "Komuta panelini gizle" if rail_open else "Komuta panelini goster",
            key="toggle_control_rail",
            use_container_width=True,
        ):
            st.session_state["control_rail_open"] = not rail_open
            st.rerun()

    with toolbar_mid:
        if st.button("Verileri yenile", key="refresh_main_control", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    with toolbar_right:
        st.markdown(
            f"""
            <div class="control-rail-meta">
                Control rail artik sadece sol sidebar'a bagli degil. Ayarlar, alarm esikleri ve kaynak sagligi
                ana yuzeyde de kalici olarak acilabiliyor. Son guncelleme: {last_updated}. Odak seviye:
                {clean_text(brief['focus']['detail'])}.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if not st.session_state.get("control_rail_open", True):
        st.markdown(
            "<div class='section-lead'>Komuta paneli gizli. Yukaridaki buton ile ayarlar, alarm esikleri ve veri sagligi alanini tekrar acabilirsin.</div>",
            unsafe_allow_html=True,
        )
        return

    col_ops, col_alerts, col_health = st.columns([1.1, 1.0, 1.2])

    with col_ops:
        st.markdown("#### Komuta Paneli")
        export_df = pd.DataFrame(
            [(key, value) for key, value in data.items() if key not in {"NEWS", "_health"}],
            columns=["Metrik", "Deger"],
        )
        st.download_button(
            "CSV indir",
            export_df.to_csv(index=False, sep=";").encode("utf-8-sig"),
            file_name=f"AlphaTerminal_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            key="download_main_control",
            use_container_width=True,
        )
        render_preferences_panel(st, key_prefix="main_control", expanded=True)

    with col_alerts:
        st.markdown("#### Alarm ve Notlar")
        if alerts:
            for alert in alerts:
                st.markdown(
                    f"""
                    <div class="alert-item">
                        <strong>{clean_text(alert['title'])}</strong>
                        <span>{clean_text(alert['detail'])}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                """
                <div class="alert-item">
                    <strong>Aktif alarm yok</strong>
                    <span>Funding, VIX ve ETF esikleri su an sessiz. Yeni esik asimlari burada toplanir.</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown(
            f"""
            <div class="alert-item" style="margin-top:12px">
                <strong>Canli Notlar</strong>
                <span>Piyasa rejimi: {clean_text(brief['regime']['title'])}<br/>Likidite: {clean_text(brief['liquidity']['title'])}<br/>Pozisyonlanma: {clean_text(brief['positioning']['title'])}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_health:
        issue_rows = get_source_health_rows(health_summary, include_ok=False)
        render_source_health_surface(
            "Kaynak Sagligi",
            "Fail ve stale kaynaklar burada acik hata metniyle listelenir. Boylece hangi veri yuzeyinin neden bos kaldigi dogrudan gorunur.",
            issue_rows[:6],
            empty_copy="Tum veri kaynaklari su an saglikli. Bu panel sadece problem oldugunda detay gosterecek.",
        )


def render_pinned_dashboard(data: dict, pinned_metrics: list[str]):
    pulse_items = [
        ("BTC Spot", data.get("BTC_P", "-"), data.get("BTC_C", "")),
        ("Funding", data.get("FR", "-"), ""),
        ("Fear & Greed", data.get("FNG", "-"), ""),
        ("USDT.D", data.get("USDT_D", "-"), ""),
        ("ETF Netflow", data.get("ETF_FLOW_TOTAL", "-"), data.get("ETF_FLOW_DATE", "")),
        ("VIX", data.get("VIX", "-"), data.get("VIX_C", "")),
    ]
    cat("Market Pulse")
    render_cards(pulse_items, cols=6)


def score_delta_meta(delta_7d: int) -> tuple[str, str]:
    if delta_7d > 1:
        return f"7g +{delta_7d}", "delta-up"
    if delta_7d < -1:
        return f"7g {delta_7d}", "delta-down"
    return "7g 0", "delta-flat"


def render_signal_deck(
    kicker: str,
    title: str,
    copy: str,
    rows: list[tuple[str, object]],
    *,
    score_value: str,
    score_label: str,
    chips: list[str] | None = None,
):
    rows_html = "".join(
        f"<div class='signal-mini-row'><span>{clean_text(label)}</span><strong>{display_value(value)}</strong></div>"
        for label, value in rows
    )
    chip_html = "".join(f"<span class='signal-chip'>{clean_text(chip)}</span>" for chip in (chips or []))
    st.markdown(
        f"""
        <div class="signal-deck">
            <div class="panel-kicker">{clean_text(kicker)}</div>
            <div class="signal-deck-top">
                <div class="signal-deck-title">{clean_text(title)}</div>
                <div class="signal-deck-score">
                    <strong>{clean_text(score_value)}</strong>
                    <span>{clean_text(score_label)}</span>
                </div>
            </div>
            <div class="signal-deck-copy">{clean_text(copy)}</div>
            <div class="signal-chip-row">{chip_html}</div>
            <div class="signal-mini-list">{rows_html}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_command_surface(data: dict, brief: dict, analytics: dict, alerts: list[dict], health_summary: dict):
    scores = analytics["scores"]
    what_matters = (
        brief["regime"].get("why", [])[:1]
        + brief["liquidity"].get("why", [])[:1]
        + brief["positioning"].get("why", [])[:1]
    )
    invalidate_items = scores.get("invalidate_conditions", [])
    watch_items = scores.get("watch_next", [])
    issue_count = len(health_summary.get("failed_sources", [])) + len(health_summary.get("stale_sources", []))

    stat_html = "".join(
        f"""
        <div class="command-stat">
            <span class="command-stat-label">{clean_text(label)}</span>
            <span class="command-stat-value">{clean_text(value)}</span>
        </div>
        """
        for label, value in [
            ("Current Bias", scores["bias"]),
            ("Focus Level", brief["focus"]["title"]),
            ("Dominant Driver", scores["dominant_driver"]),
            ("Weakest Link", scores["weakest_driver"]),
        ]
    )
    matters_html = "".join(f"<div class='command-list-item'>{clean_text(item)}</div>" for item in what_matters[:3])
    invalidate_html = "".join(
        f"<div class='command-list-item'>{clean_text(item)}</div>" for item in invalidate_items[:3]
    )
    watch_html = "".join(f"<div class='command-list-item'>{clean_text(item)}</div>" for item in watch_items[:3])

    st.markdown(
        f"""
        <div class="surface command-surface">
            <div>
                <div class="panel-kicker">Command Surface</div>
                <div class="command-title">{clean_text(scores['overlay'])}</div>
                <div class="command-copy">
                    {clean_text(scores['summary'])} Bugunun ana tezi; {clean_text(brief['regime']['title'])},
                    {clean_text(brief['liquidity']['title'])} ve {clean_text(brief['positioning']['title'])}
                    katmanlarinin birlikte okunmasi gerekiyor.
                </div>
            </div>
            <div class="command-stat-grid">{stat_html}</div>
            <div class="command-columns">
                <div class="command-block">
                    <div class="command-block-title">What Matters Now</div>
                    <div class="command-list">{matters_html}</div>
                </div>
                <div class="command-block">
                    <div class="command-block-title">Invalidate If</div>
                    <div class="command-list">{invalidate_html}</div>
                </div>
            </div>
            <div class="command-columns">
                <div class="command-block">
                    <div class="command-block-title">Watch Next</div>
                    <div class="command-list">{watch_html}</div>
                </div>
                <div class="command-block">
                    <div class="command-block-title">Operating Context</div>
                    <div class="command-list">
                        <div class="command-list-item">Confidence {scores['confidence']}/100 | {clean_text(scores['confidence_label'])}</div>
                        <div class="command-list-item">Aktif alarm {len(alerts)} | veri sorunu {issue_count}</div>
                        <div class="command-list-item">Odak seviye: {clean_text(brief['focus']['detail'])}</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_catalyst_stream(data: dict, analytics: dict, alerts: list[dict], health_summary: dict):
    scores = analytics["scores"]
    issue_rows = get_source_health_rows(health_summary, include_ok=False)[:3]
    alert_rows = alerts[:3] or [
        {"title": "Aktif alarm yok", "detail": "Esik bazli alarm akisi su an sessiz; rejim okumasi sinyal deck'lerde."}
    ]
    alert_html = "".join(
        f"<div class='command-list-item'><strong>{clean_text(item['title'])}</strong> | {clean_text(item['detail'])}</div>"
        for item in alert_rows
    )
    watch_html = "".join(
        f"<div class='command-list-item'>{clean_text(item)}</div>" for item in scores.get("watch_next", [])[:3]
    )
    issue_html = "".join(
        f"<div class='command-list-item'>{clean_text(row['Kaynak'])} | {clean_text(row['Durum'])} | {clean_text(row['Hata'])}</div>"
        for row in issue_rows
    ) or "<div class='command-list-item'>Kritik veri problemi yok; kaynak akisinda anlamli bir bozulma görünmuyor.</div>"

    st.markdown(
        f"""
        <div class="surface">
            <div class="panel-kicker">Catalyst Stream</div>
            <div class="panel-title">Bugun neyi izleyecegiz?</div>
            <div class="panel-copy">
                Bu alan alarm, dikkat gerektiren tetikleyici ve veri sagligi sinyallerini tek operasyon akisi halinde toplar.
            </div>
            <div class="command-columns">
                <div class="command-block">
                    <div class="command-block-title">Active Alerts</div>
                    <div class="command-list">{alert_html}</div>
                </div>
                <div class="command-block">
                    <div class="command-block-title">Next Checkpoints</div>
                    <div class="command-list">{watch_html}</div>
                </div>
            </div>
            <div class="command-block">
                <div class="command-block-title">Diagnostics</div>
                <div class="command-list">{issue_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_score_panel(analytics: dict):
    scores = analytics["scores"]
    contribution_html = "".join(
        f"""
        <div class="contribution-row">
            <div style="flex:1">
                <div class="contribution-copy">{clean_text(factor['label'])} katkisi</div>
                <div class="contribution-bar">
                    <div class="contribution-bar-fill" style="width:{factor['score']}%"></div>
                </div>
            </div>
            <div class="contribution-meta">{factor['contribution']:.1f} puan</div>
        </div>
        """
        for factor in sorted(scores["factors"], key=lambda item: item["contribution"], reverse=True)
    )
    fragility_html = "".join(
        f"<div class='fragility-flag'>{clean_text(flag)}</div>" for flag in scores["fragility"]["flags"]
    )
    factor_html = ""
    for factor in scores["factors"]:
        delta_text, delta_class = score_delta_meta(factor["delta_7d"])
        drivers_html = "".join(f"<div class='driver-item'>{clean_text(driver)}</div>" for driver in factor["drivers"])
        factor_html += f"""
        <div class="factor-card">
            <div class="factor-head">
                <span class="factor-name">{clean_text(factor['label'])}</span>
                <span class="factor-weight">Weight {factor['weight_pct']}%</span>
            </div>
            <div class="factor-score-row">
                <div class="factor-score">{factor['score']}/100</div>
                <div class="factor-delta {delta_class}">{delta_text}</div>
            </div>
            <div class="factor-copy">{clean_text(factor['summary'])}</div>
            <div class="factor-meta">
                <span>Katki {factor['contribution']:.1f} puan</span>
                <span>{clean_text(factor['trend_text'])}</span>
            </div>
            <div class="driver-list">{drivers_html}</div>
        </div>
        """
    st.markdown(
        f"""
        <div class="surface regime-panel">
            <div class="panel-kicker">Risk Engine</div>
            <div class="panel-title">Rejim Haritasi</div>
            <div class="panel-copy">{clean_text(scores['summary'])}</div>
            <div class="regime-top">
                <div class="regime-hero">
                    <div class="regime-hero-head">
                        <div>
                            <div class="metric-label">Genel Rejim</div>
                            <div class="regime-main-score">{scores['overall']}/100</div>
                        </div>
                        <div class="regime-overlay">{clean_text(scores['overlay'])}</div>
                    </div>
                    <div class="regime-score-copy">
                        {clean_text(scores['regime_band'])}. Dominant surucu {clean_text(scores['dominant_driver'])};
                        en zayif halka ise {clean_text(scores['weakest_driver'])}.
                    </div>
                    <div class="regime-summary-grid">
                        <div class="summary-stat">
                            <span class="summary-stat-label">Base Score</span>
                            <span class="summary-stat-value">{scores['base_score']}/100</span>
                        </div>
                        <div class="summary-stat">
                            <span class="summary-stat-label">Fragility Penalty</span>
                            <span class="summary-stat-value">-{scores['penalty']}</span>
                        </div>
                        <div class="summary-stat">
                            <span class="summary-stat-label">Dominant Driver</span>
                            <span class="summary-stat-value">{clean_text(scores['dominant_driver'])}</span>
                        </div>
                        <div class="summary-stat">
                            <span class="summary-stat-label">Weakest Link</span>
                            <span class="summary-stat-value">{clean_text(scores['weakest_driver'])}</span>
                        </div>
                    </div>
                    <div class="contribution-list">{contribution_html}</div>
                </div>
                <div class="fragility-card">
                    <div class="metric-label">Fragility Overlay</div>
                    <div class="fragility-score">{scores['fragility']['score']}/100</div>
                    <div class="fragility-label">{clean_text(scores['fragility']['label'])}</div>
                    <div class="panel-copy" style="margin-top:10px">
                        Rejim skoru ile kirilganlik ayrildi. Yani yuksek skor, otomatik olarak saglikli ve genis tabanli ortam demek degil.
                    </div>
                    <div class="fragility-flags">{fragility_html}</div>
                </div>
            </div>
            <div class="factor-grid">{factor_html}</div>
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
    st.markdown("<div class='table-section-title'>Tum Metrikler - Ham Veri</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='table-section-copy'>Tum ana veri basinliklarini tek bir atlas icinde topladim; terminalin veri tabani burada gruplu sekilde okunuyor.</div>",
        unsafe_allow_html=True,
    )
    render_table_row(data, DATA_ATLAS_SECTIONS[:4], 4)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    render_table_row(data, DATA_ATLAS_SECTIONS[4:], 4)


def render_overview_tab(data: dict, brief: dict, analytics: dict, alerts: list[dict], health_summary: dict):
    scores = analytics["scores"]
    factors = {factor["key"]: factor for factor in scores["factors"]}

    st.markdown("<div class='table-section-title'>Terminal</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='table-section-copy'>Ana ekran artik tek bir command center gibi calisiyor: once rejim, sonra bugunun okuması, sonra da trade'i bozabilecek sinyaller okunuyor.</div>",
        unsafe_allow_html=True,
    )

    left_col, right_col = st.columns([1.12, 0.88])
    with left_col:
        render_score_panel(analytics)
    with right_col:
        render_command_surface(data, brief, analytics, alerts, health_summary)

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    deck_cols = st.columns(4)
    with deck_cols[0]:
        factor = factors["liquidity"]
        delta_text, _ = score_delta_meta(factor["delta_7d"])
        render_signal_deck(
            "Liquidity Deck",
            brief["liquidity"]["title"],
            factor["summary"],
            [
                ("ETF Flow", data.get("ETF_FLOW_TOTAL", "-")),
                ("DXY", data.get("DXY", "-")),
                ("USDT.D", data.get("USDT_D", "-")),
            ],
            score_value=f"{factor['score']}/100",
            score_label=factor["confidence_label"],
            chips=[factor["state"], f"Weight {factor['weight_pct']}%", delta_text, factor["primary_risk"]],
        )
    with deck_cols[1]:
        factor = factors["positioning"]
        delta_text, _ = score_delta_meta(factor["delta_7d"])
        render_signal_deck(
            "Positioning Deck",
            brief["positioning"]["title"],
            factor["summary"],
            [
                ("Funding", data.get("FR", "-")),
                ("L/S", data.get("LS_Ratio", "-")),
                ("Taker", data.get("Taker", "-")),
            ],
            score_value=f"{factor['score']}/100",
            score_label=factor["confidence_label"],
            chips=[factor["state"], f"Weight {factor['weight_pct']}%", delta_text, factor["primary_risk"]],
        )
    with deck_cols[2]:
        factor = factors["breadth"]
        delta_text, _ = score_delta_meta(factor["delta_7d"])
        render_signal_deck(
            "Breadth Deck",
            "Participation Quality",
            factor["summary"],
            [
                ("TOTAL2", data.get("TOTAL2_CAP", "-")),
                ("TOTAL3", data.get("TOTAL3_CAP", "-")),
                ("BTC Dom", data.get("Dom", "-")),
            ],
            score_value=f"{factor['score']}/100",
            score_label=factor["confidence_label"],
            chips=[factor["state"], f"Weight {factor['weight_pct']}%", delta_text, factor["primary_risk"]],
        )
    with deck_cols[3]:
        render_signal_deck(
            "Execution Deck",
            brief["focus"]["title"],
            "Destek/direnc, order book uyumu ve fiyat teyidini ayni deck'te verir.",
            [
                ("Support", data.get("Sup_Wall", "-")),
                ("Resistance", data.get("Res_Wall", "-")),
                ("Signal", data.get("ORDERBOOK_SIGNAL", "-")),
            ],
            score_value=display_value(data.get("BTC_P", "-")),
            score_label=brief["focus"]["badge"],
            chips=[brief["regime"]["title"], brief["focus"]["badge"], brief["focus"]["class"].replace("signal-", "")],
        )

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    lower_left, lower_right = st.columns([1.08, 0.92])
    with lower_left:
        render_scenario_matrix(analytics)
    with lower_right:
        render_catalyst_stream(data, analytics, alerts, health_summary)


def render_macro_tab(data: dict):
    st.markdown("<div class='table-section-title'>Macro and Markets</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='table-section-copy'>Global equity, emtia, doviz ve policy setini bolgesel bir terminal akisi halinde yeniden kurdum.</div>",
        unsafe_allow_html=True,
    )
    render_table_row(data, MACRO_MARKET_SECTIONS[:3], 3)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    render_table_row(data, MACRO_MARKET_SECTIONS[3:5], 2)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    render_table_row(data, MACRO_MARKET_SECTIONS[5:], 3)


def render_flow_risk_tab(data: dict, health_summary: dict):
    st.markdown("<div class='table-section-title'>Flow and Risk Surfaces</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='table-section-copy'>Bu ekran ham veri tablosu degil; positioning, liquidity, breadth ve execution katmanlarini once yorumlar, sonra detay yuzeylerine iner.</div>",
        unsafe_allow_html=True,
    )
    scores = build_analytics_payload(data)["scores"]
    factors = {factor["key"]: factor for factor in scores["factors"]}
    top_cols = st.columns(2)
    with top_cols[0]:
        factor = factors["positioning"]
        delta_text, _ = score_delta_meta(factor["delta_7d"])
        render_signal_deck(
            "Positioning",
            factor["state"],
            factor["summary"],
            [("OI", data.get("OI", "-")), ("Funding", data.get("FR", "-")), ("L/S", data.get("LS_Ratio", "-")), ("Taker", data.get("Taker", "-"))],
            score_value=f"{factor['score']}/100",
            score_label=factor["confidence_label"],
            chips=[delta_text, factor["primary_risk"], f"Weight {factor['weight_pct']}%"],
        )
    with top_cols[1]:
        factor = factors["liquidity"]
        delta_text, _ = score_delta_meta(factor["delta_7d"])
        render_signal_deck(
            "Liquidity",
            factor["state"],
            factor["summary"],
            [("ETF", data.get("ETF_FLOW_TOTAL", "-")), ("DXY", data.get("DXY", "-")), ("US10Y", data.get("US10Y", "-")), ("USDT.D", data.get("USDT_D", "-"))],
            score_value=f"{factor['score']}/100",
            score_label=factor["confidence_label"],
            chips=[delta_text, factor["primary_risk"], f"Weight {factor['weight_pct']}%"],
        )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    mid_cols = st.columns(2)
    with mid_cols[0]:
        factor = factors["breadth"]
        delta_text, _ = score_delta_meta(factor["delta_7d"])
        render_signal_deck(
            "Breadth",
            factor["state"],
            factor["summary"],
            [("TOTAL2", data.get("TOTAL2_CAP", "-")), ("TOTAL3", data.get("TOTAL3_CAP", "-")), ("OTHERS", data.get("OTHERS_CAP", "-")), ("BTC Dom", data.get("Dom", "-"))],
            score_value=f"{factor['score']}/100",
            score_label=factor["confidence_label"],
            chips=[delta_text, factor["primary_risk"], f"Weight {factor['weight_pct']}%"],
        )
    with mid_cols[1]:
        render_signal_deck(
            "Execution",
            display_value(data.get("ORDERBOOK_SIGNAL", "-")),
            "Coklu borsa seviyeleri ile ETF ve fiyat tepkisi bu deck'te birlikte okunur.",
            [("Support", data.get("Sup_Wall", "-")), ("Resistance", data.get("Res_Wall", "-")), ("Wall Status", data.get("Wall_Status", "-")), ("ETF Flow", data.get("ETF_FLOW_TOTAL", "-"))],
            score_value=display_value(data.get("BTC_P", "-")),
            score_label="spot",
            chips=[display_value(data.get("ORDERBOOK_SIGNAL_BADGE", "-"), fallback="watch"), display_value(data.get("ORDERBOOK_SIGNAL_CLASS", "-"), fallback="neutral")],
        )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    render_source_health_surface(
        "Turev Kaynak Durumu",
        "Funding, open interest, taker ve long/short verileri bos kalirsa nedeni artik ayni sekmede hangi endpoint'in fail oldugu ile birlikte gorunur.",
        get_source_health_rows(health_summary, DERIVATIVE_SOURCE_NAMES, include_ok=True),
        empty_copy="Turev kaynaklarina ait health kaydi henuz olusmadi.",
    )
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    st.markdown("<div class='table-section-copy'>Raw surfaces</div>", unsafe_allow_html=True)
    render_table_row(data, FLOW_RISK_SECTIONS[2:], 2)
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    render_table_row(data, FLOW_RISK_SECTIONS[:2], 2)


def render_report_tab(
    client, data: dict, brief: dict, analytics: dict, alerts: list[dict], health_summary: dict, report_depth: str
):
    st.markdown("<div class='table-section-title'>Reports and Catalysts</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='table-section-copy'>Raporlar sekmesi artik sadece widget koleksiyonu degil; senaryo, AI yorumu, takvim ve haber akislarini ayni raporlama yüzeyinde toplar.</div>",
        unsafe_allow_html=True,
    )
    col_chart, col_side = st.columns([1.7, 1.0])
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
        render_scenario_matrix(analytics)
        st.divider()
        render_downloads(data, brief, analytics, alerts, health_summary)
    with col_side:
        render_catalyst_stream(data, analytics, alerts, health_summary)
        st.divider()
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
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    col_news, col_health = st.columns([1.15, 0.85])
    with col_news:
        st.subheader("News and Catalysts")
        news = data.get("NEWS", [])
        if news:
            for item in news[:8]:
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
            st.info("Haber akisi su an yok.")
    with col_health:
        render_source_health_surface(
            "Diagnostics",
            "Raporlama katmaninda kullanilan veri akisinin saglik durumu ve kritik bozulmalar burada toplanir.",
            get_source_health_rows(health_summary, include_ok=False)[:5],
            empty_copy="Raporlama akisini bozacak kritik veri problemi bulunmuyor.",
        )


init_preferences()
init_ui_state()
preferences = st.session_state["preferences"]
client = build_openrouter_client(OPENROUTER_API_KEY) if OPENROUTER_API_KEY else None

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

render_page_header(last_updated, health_summary, brief, preferences, analytics)
render_health_alerts(health_summary)
render_sidebar(data, brief, last_updated, health_summary, preferences, alerts)
render_control_rail(data, brief, last_updated, health_summary, alerts)

tabs = st.tabs(["Terminal", "Macro", "Flow", "Reports", "Atlas"])
with tabs[0]:
    render_overview_tab(data, brief, analytics, alerts, health_summary)
with tabs[1]:
    render_macro_tab(data)
with tabs[2]:
    render_flow_risk_tab(data, health_summary)
with tabs[3]:
    render_report_tab(
        client, data, brief, analytics, alerts, health_summary, preferences.get("report_depth", "Orta")
    )
with tabs[4]:
    render_all_metrics_tab(data)

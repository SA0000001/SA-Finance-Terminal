import html

import pandas as pd
import streamlit as st

from services.health import normalize_health_display_text
from ui.components import bi_label, clean_text, render_health_bar


def _escape_html(value) -> str:
    return html.escape(clean_text(value))


def normalize_health_cell(value) -> str:
    return clean_text(normalize_health_display_text(value))


def render_page_header(last_updated: str, health_summary: dict, brief: dict, preferences: dict, analytics: dict):
    scores = analytics["scores"]
    st.markdown(
        f"""
        <div class="terminal-header">
            <div class="header-copy">
                <div class="hero-kicker">Digital Asset Intelligence</div>
                <h1>SA Finance Alpha Terminal</h1>
                <div class="header-subtitle">
                    Makro rejim, risk akis ve alpha teyitlerini gosterip bunlari tek bir karar akisina indirger.
                </div>
                <div class="header-summary">
                    <div class="summary-chip">
                        <span>{clean_text(bi_label("Market State", "Piyasa Durumu"))}</span>
                        <strong>{clean_text(scores["overlay"])}</strong>
                    </div>
                    <div class="summary-chip">
                        <span>{clean_text(bi_label("Fragility", "Kirilganlik"))}</span>
                        <strong>{clean_text(scores["fragility"]["label"])}</strong>
                    </div>
                    <div class="summary-chip">
                        <span>{clean_text(bi_label("Confidence", "Guven"))}</span>
                        <strong>{scores["confidence"]}/100 | {clean_text(scores["confidence_label"])}</strong>
                    </div>
                </div>
            </div>
            <div class="header-meta">
                <div class="meta-stack">
                    <span class="header-pill">Canli veri akisi</span>
                    <span class="header-pill">Mod | {clean_text(preferences.get("view_mode", "Basit"))}</span>
                    <span class="status-badge">v19.0</span>
                </div>
                <div class="meta-caption">
                    Istanbul | {last_updated}<br/>
                    Bias | {clean_text(scores["bias"])}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_health_bar(health_summary)
    st.markdown(
        "<div class='section-lead'>Merkezde rejim, sekmelerde detay katmanlari var; ust yuzey karar verir, alt yuzeyler teyit eder.</div>",
        unsafe_allow_html=True,
    )


def render_status_hub(last_updated: str, health_summary: dict, alerts: list[dict], analytics: dict):
    issue_rows = [row for row in health_summary.get("rows", []) if row.get("Durum") != "OK"]
    scores = analytics["scores"]
    issue_count = len(issue_rows)
    alert_count = len(alerts)
    summary_copy = (
        f"{issue_count} kaynak dikkat istiyor; detaylar sadece burada tutuluyor."
        if issue_count
        else "Kritik veri problemi yok; health detayi yalnizca gerektiginde acilir."
    )
    stats_html = "".join(
        f"""
        <div class="status-hub-pill">
            <span>{clean_text(label)}</span>
            <strong>{clean_text(value)}</strong>
        </div>
        """
        for label, value in [
            (bi_label("Updated", "Guncelleme"), last_updated),
            (bi_label("Alerts", "Alarmlar"), str(alert_count)),
            (bi_label("Issues", "Sorunlar"), str(issue_count)),
            (bi_label("Confidence", "Guven"), f"{scores['confidence']}/100"),
        ]
    )
    st.markdown(
        f"""
        <div class="surface surface-compact status-hub">
            <div class="panel-kicker">{clean_text(bi_label("Status Hub", "Durum Merkezi"))}</div>
            <div class="status-hub-top">
                <div>
                    <div class="panel-title">Operasyon ozeti tek merkezde</div>
                    <div class="panel-copy">{clean_text(summary_copy)}</div>
                </div>
                <div class="status-hub-stats">{stats_html}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if issue_rows:
        with st.expander("Source health details", expanded=False):
            for row in issue_rows[:6]:
                source = normalize_health_cell(row.get("Kaynak"))
                error = normalize_health_cell(row.get("Hata"))
                status = normalize_health_cell(row.get("Durum"))
                last_success = normalize_health_cell(row.get("Son basarili"))
                left_col, right_col = st.columns([5, 1.2], vertical_alignment="top")
                with left_col:
                    st.markdown(f"<div class='health-issue-source'>{_escape_html(source)}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='health-issue-error'>{_escape_html(error)}</div>", unsafe_allow_html=True)
                with right_col:
                    status_kind = status.lower()
                    st.markdown(
                        (
                            f"<div class='health-issue-meta'>"
                            f"<span class='health-issue-status health-issue-{_escape_html(status_kind)}'>{_escape_html(status)}</span>"
                            f"<span>{_escape_html(last_success)}</span>"
                            f"</div>"
                        ),
                        unsafe_allow_html=True,
                    )
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)


def render_health_panel(health_summary: dict):
    rows = health_summary.get("rows", [])
    if not rows:
        st.info("Veri sagligi bilgisi henuz olusmadi.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Saglikli", health_summary.get("healthy_sources", 0))
    col2.metric("Basarisiz", len(health_summary.get("failed_sources", [])))
    col3.metric("Stale", len(health_summary.get("stale_sources", [])))
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_sidebar(data, brief, last_updated: str, health_summary: dict, preferences: dict, alerts: list[dict]):
    with st.sidebar:
        st.markdown("### Control Rail")
        st.caption(f"Son guncelleme: {last_updated}")
        st.divider()

        if st.button("Verileri Yenile", key="sidebar_refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        export_df = pd.DataFrame(
            [(key, value) for key, value in data.items() if key not in {"NEWS", "_health"}],
            columns=["Metrik", "Deger"],
        )
        st.download_button(
            "CSV indir",
            export_df.to_csv(index=False, sep=";").encode("utf-8-sig"),
            file_name=f"AlphaTerminal_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            key="sidebar_csv_download",
            use_container_width=True,
        )

        st.divider()
        st.markdown(
            f"""
            <div class="sidebar-note">
                Sidebar artik yalnizca operasyon isleri icin ayrildi: yenileme, disa aktarma ve sistem bilgisi.
                Health ve canli durum detaylari ana yuzeydeki Status Hub'a tasindi.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.divider()
        st.markdown(
            """
**Veri Kaynaklari**
`Coinpaprika` | `Kraken` | `OKX` | `KuCoin` | `Gate.io` | `Coinbase`
`DeFiLlama` | `yFinance` | `TradingView` | `FRED` | `CoinDesk`

**Model**
`Gemini 2.5 Flash`
""",
        )

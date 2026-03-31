import pandas as pd
import streamlit as st

from ui.components import clean_text, render_health_bar


def render_page_header(last_updated: str, health_summary: dict, brief: dict, preferences: dict):
    st.markdown(
        f"""
        <div class="terminal-header">
            <div class="header-copy">
                <div class="hero-kicker">Digital Asset Intelligence</div>
                <h1>SA Finance Alpha Terminal</h1>
                <div class="header-subtitle">
                    Makrodan mikroya uzanan piyasa rontgeni, risk akisi ve alpha teyitlerini
                    tek bir ust segment terminal deneyiminde toplar.
                </div>
                <div class="header-summary">
                    <div class="summary-chip">
                        <span>Piyasa Rejimi</span>
                        <strong>{clean_text(brief["regime"]["title"])}</strong>
                    </div>
                    <div class="summary-chip">
                        <span>Pozisyonlanma</span>
                        <strong>{clean_text(brief["positioning"]["title"])}</strong>
                    </div>
                    <div class="summary-chip">
                        <span>Likidite</span>
                        <strong>{clean_text(brief["liquidity"]["title"])}</strong>
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
                    Saglikli kaynak: {health_summary.get("healthy_sources", 0)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_health_bar(health_summary)
    st.markdown(
        "<div class='section-lead'>Ilk katman rejimi ve yonu verir; ikinci katman piyasa, akis ve sinyal yuzeylerini aciklar; derin katmanlar ise detay veri atlasini ve raporlari tasir.</div>",
        unsafe_allow_html=True,
    )


def render_health_alerts(health_summary: dict):
    return


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

        if st.button("Verileri Yenile", use_container_width=True):
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
            use_container_width=True,
        )

        st.divider()
        st.markdown(
            f"""
            <div class="sidebar-note">
                Komuta paneli; yenileme, disa aktarma, veri sagligi ve hizli operasyon notlari icin ayrildi.
                Ana ekran ise tamamen karar destek ve terminal akisina odaklandi.
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("#### Live Notes")
        st.markdown(f"- Piyasa rejimi: {clean_text(brief['regime']['title'])}")
        st.markdown(f"- Izlenen seviye: {clean_text(brief['focus']['detail'])}")
        st.markdown(f"- ETF akisi: {clean_text(data.get('ETF_FLOW_TOTAL', '-'))}")
        if health_summary.get("failed_sources"):
            st.markdown(f"- Fallback kaynaklar: {clean_text(', '.join(health_summary['failed_sources'][:3]))}")
        if health_summary.get("stale_sources"):
            st.markdown(f"- Stale kaynaklar: {clean_text(', '.join(health_summary['stale_sources'][:3]))}")

        if alerts:
            st.divider()
            st.markdown("#### Alert Queue")
            for alert in alerts:
                st.markdown(f"- {clean_text(alert['title'])}: {clean_text(alert['detail'])}")

        st.divider()
        with st.expander("Kaynak Sagligi", expanded=False):
            render_health_panel(health_summary)

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

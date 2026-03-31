import pandas as pd
import streamlit as st

from ui.components import clean_text, render_health_bar, render_info_panel


def render_page_header(last_updated: str, health_summary: dict):
    st.markdown(
        f"""
        <div class="terminal-header">
            <div>
                <div class="hero-kicker">Digital Asset Intelligence</div>
                <h1>SA Finance Alpha Terminal</h1>
                <div class="header-subtitle">
                    Kripto, makro ve likidite verilerini tek ekranda toplayan karar paneli.
                    Basit gorunum hizli okuma icin, Pro gorunum derin analiz icin optimize edildi.
                </div>
            </div>
            <div class="header-meta">
                <span class="header-pill">Canli veri akisi</span>
                <span class="header-pill">Istanbul | {last_updated}</span>
                <span class="badge">v19.0</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_health_bar(health_summary)
    st.markdown(
        "<div class='section-lead'>Bugunun en kritik sinyallerini, veri sagligi ve kullanici tercihleri ile birlikte tek yerde gorun.</div>",
        unsafe_allow_html=True,
    )


def render_health_alerts(health_summary: dict):
    failed_sources = health_summary.get("failed_sources", [])
    stale_sources = health_summary.get("stale_sources", [])

    if failed_sources:
        st.warning(f"Fallback aktif kaynaklar: {', '.join(failed_sources[:5])}")
    if stale_sources:
        st.error(f"10+ dakika stale kaynak uyarisi: {', '.join(stale_sources[:5])}")


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
        st.markdown("### Kontrol Merkezi")
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
        render_info_panel(
            "Quick Pulse",
            "Bugunun Nabzi",
            [
                ("BTC fiyat", data.get("BTC_P", "-")),
                ("Fear & Greed", data.get("FNG", "-")),
                ("Funding", data.get("FR", "-")),
                ("VIX", data.get("VIX", "-")),
            ],
            badge_text=brief["regime"]["title"],
            badge_kind=brief["regime"]["class"],
            copy="Fiyat, duygu ve volatilite ayni blokta toplandi.",
        )

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        render_info_panel(
            "Watchlist",
            "Izlenecek Seviyeler",
            [
                ("Order book", data.get("ORDERBOOK_SIGNAL", "-")),
                ("Kraken ana seviye", f"{data.get('Sup_Wall', '-')} / {data.get('Res_Wall', '-')}"),
                ("ETF netflow", f"{data.get('ETF_FLOW_TOTAL', '-')} | {data.get('ETF_FLOW_DATE', '-')}"),
                ("USD/TRY", data.get("USDTRY", "-")),
            ],
            badge_text=preferences.get("view_mode", "Pro"),
            badge_kind=brief["focus"]["class"],
            copy="Kullanici secimi pinli metrikler ana ekranda gorunur.",
        )

        if alerts:
            st.divider()
            st.markdown("#### Aktif Alarmlar")
            for alert in alerts:
                st.markdown(f"- {clean_text(alert['title'])}: {clean_text(alert['detail'])}")

        st.divider()
        with st.expander("Veri Sagligi", expanded=False):
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

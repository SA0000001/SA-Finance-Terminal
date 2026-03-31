import pandas as pd
import streamlit as st

from ui.components import render_info_panel


def render_page_header(last_updated: str):
    st.markdown(
        f"""
        <div class="terminal-header">
            <div>
                <div class="hero-kicker">Digital Asset Intelligence</div>
                <h1>âš¡ SA Finance Alpha Terminal</h1>
                <div class="header-subtitle">
                    Kripto, makro ve likidite verilerini tek ekranda toplayan daha net bir karar paneli.
                    Ã–nce kÄ±sa Ã¶zeti gÃ¶r, sonra sekmelerde detaya in.
                </div>
            </div>
            <div class="header-meta">
                <span class="header-pill"><span class="status-dot"></span> CanlÄ± veri akÄ±ÅŸÄ±</span>
                <span class="header-pill">Ä°stanbul Â· {last_updated}</span>
                <span class="badge">v18.1</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='section-lead'>BugÃ¼nÃ¼n en kritik sinyallerini Ã¶ne Ã§Ä±karan kÄ±sa Ã¶zet kartlarÄ±.</div>",
        unsafe_allow_html=True,
    )


def render_health_alerts(health_summary: dict):
    failed_sources = health_summary.get("failed_sources", [])
    stale_sources = health_summary.get("stale_sources", [])

    if failed_sources:
        failed_text = ", ".join(failed_sources[:4])
        if len(failed_sources) > 4:
            failed_text = f"{failed_text} +{len(failed_sources) - 4}"
        st.warning(f"Bazi veri kaynaklari fallback ile calisiyor: {failed_text}")

    if stale_sources:
        stale_text = ", ".join(stale_sources[:4])
        if len(stale_sources) > 4:
            stale_text = f"{stale_text} +{len(stale_sources) - 4}"
        st.error(f"Stale veri uyarisi: {stale_text}")


def render_health_panel(health_summary: dict):
    rows = health_summary.get("rows", [])
    if not rows:
        st.info("Veri sagligi bilgisi henuz olusmadi.")
        return

    col1, col2, col3 = st.columns(3)
    col1.metric("Saglikli", health_summary.get("healthy_sources", 0))
    col2.metric("Basarisiz", len(health_summary.get("failed_sources", [])))
    col3.metric("Stale", len(health_summary.get("stale_sources", [])))

    table = pd.DataFrame(rows)
    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Kaynak": st.column_config.TextColumn("Kaynak", width="medium"),
            "Durum": st.column_config.TextColumn("Durum", width="small"),
            "Gecikme": st.column_config.TextColumn("Gecikme", width="small"),
            "Son basarili": st.column_config.TextColumn("Son basarili", width="medium"),
            "Hata": st.column_config.TextColumn("Hata", width="large"),
        },
    )


def render_sidebar(data, brief, last_updated: str, health_summary: dict):
    with st.sidebar:
        st.markdown("### ğŸ›°ï¸ Kontrol Merkezi")
        st.caption(f"â±ï¸ Son gÃ¼ncelleme: {last_updated}")
        st.divider()

        if st.button("ğŸ”„ Verileri Yenile", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        df_exp = pd.DataFrame([(key, value) for key, value in data.items() if key not in {"NEWS", "_health"}], columns=["Metrik", "DeÄŸer"])
        csv = df_exp.to_csv(index=False, sep=";").encode("utf-8-sig")
        st.download_button(
            "ğŸ’¾ CSV Ä°ndir",
            csv,
            file_name=f"AlphaTerminal_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

        st.divider()
        render_info_panel(
            "Quick Pulse",
            "BugÃ¼nÃ¼n NabzÄ±",
            [
                ("BTC fiyat", data.get("BTC_P", "â€”")),
                ("Korku / AÃ§gÃ¶zlÃ¼lÃ¼k", data.get("FNG", "â€”")),
                ("Funding", data.get("FR", "â€”")),
                ("VIX", data.get("VIX", "â€”")),
            ],
            badge_text=brief["regime"]["title"],
            badge_kind=brief["regime"]["class"],
            copy="YÃ¶nÃ¼ anlamak iÃ§in fiyat, duygu ve volatilite aynÄ± blokta toplandÄ±.",
        )

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        render_info_panel(
            "Watchlist",
            "Ä°zlenecek Seviyeler",
            [
                ("Order book sinyali", data.get("ORDERBOOK_SIGNAL", "â€”")),
                ("Kraken ana seviye", f"{data.get('Sup_Wall', 'â€”')} / {data.get('Res_Wall', 'â€”')}"),
                ("GÃ¼nlÃ¼k ETF Netflow", f"{data.get('ETF_FLOW_TOTAL', 'â€”')} Â· {data.get('ETF_FLOW_DATE', 'â€”')}"),
                ("USD/TRY", data.get("USDTRY", "â€”")),
            ],
            badge_text=brief["focus"]["badge"],
            badge_kind=brief["focus"]["class"],
            copy="Coklu borsa order book ozeti ile kurumsal akis ayni izleme panelinde toplandi.",
        )

        st.divider()
        with st.expander("Veri Sagligi", expanded=False):
            render_health_panel(health_summary)

        st.divider()
        st.markdown(
            """
**Veri Kaynaklari:**  
`Coinpaprika` Â· `Kraken` Â· `OKX` Â· `KuCoin` Â· `Gate.io` Â· `Coinbase`  
`DeFiLlama` Â· `yFinance` Â· `TradingView`  
`FRED` Â· `CoinDesk`

**Model:** `Gemini 2.5 Flash`  
**Cache:** 3 dk | Turev: Canli
""",
        )

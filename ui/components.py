import streamlit as st


def mcard(label: str, value: str, delta: str = "", accent_color: str = "--accent"):
    if delta and delta not in ("—", ""):
        try:
            raw = float(delta.replace("%", "").replace(",", ".").strip())
            css_class = "metric-delta-pos" if raw >= 0 else "metric-delta-neg"
            arrow = "▲" if raw >= 0 else "▼"
            delta_html = f'<div class="{css_class}">{arrow} {delta}</div>'
        except ValueError:
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
    columns = st.columns(cols)
    for i, item in enumerate(items):
        label = item[0]
        value = item[1] if len(item) > 1 else "—"
        delta = item[2] if len(item) > 2 else ""
        with columns[i % cols]:
            st.markdown(mcard(label, value, delta, accent), unsafe_allow_html=True)


def cat(title: str, icon: str = ""):
    st.markdown(f'<div class="cat-header">{icon}&nbsp; {title}</div>', unsafe_allow_html=True)


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

import streamlit as st

PLACEHOLDER = "-"
REPLACEMENTS = {
    "â€”": "-",
    "Ã¢â‚¬â€": "-",
    "Â·": " | ",
    "Ã‚Â·": " | ",
    "â–²": "+",
    "â–¼": "-",
}


def clean_text(value):
    if value is None:
        return PLACEHOLDER
    text = str(value)
    for source, target in REPLACEMENTS.items():
        text = text.replace(source, target)
    return text


def is_missing(value) -> bool:
    return clean_text(value).strip() in {PLACEHOLDER, "", "None"}


def display_value(value, fallback: str = "Veri bekleniyor") -> str:
    return fallback if is_missing(value) else clean_text(value)


def mcard(label: str, value: str, delta: str = "", accent_color: str = "--accent"):
    value_missing = is_missing(value)
    value = display_value(value)
    delta = clean_text(delta) if delta else ""
    if delta and delta not in (PLACEHOLDER, ""):
        try:
            raw = float(delta.replace("%", "").replace(",", ".").strip())
            css_class = "metric-delta-pos" if raw >= 0 else "metric-delta-neg"
            arrow = "+" if raw >= 0 else "-"
            delta_html = f'<div class="{css_class}">{arrow} {delta}</div>'
        except ValueError:
            delta_html = f'<div class="metric-delta-neu">{delta}</div>'
    elif delta:
        delta_html = f'<div class="metric-delta-neu">{delta}</div>'
    else:
        delta_html = ""

    value_class = "metric-value metric-placeholder" if value_missing else "metric-value"

    return f"""
    <div class="metric-card" style="--card-accent: var({accent_color});">
        <div class="metric-label">{clean_text(label)}</div>
        <div class="{value_class}">{value}</div>
        {delta_html}
    </div>
    """


def render_cards(items, cols=4, accent="--accent"):
    columns = st.columns(cols)
    for i, item in enumerate(items):
        label = item[0]
        value = item[1] if len(item) > 1 else PLACEHOLDER
        delta = item[2] if len(item) > 2 else ""
        with columns[i % cols]:
            st.markdown(mcard(label, value, delta, accent), unsafe_allow_html=True)


def cat(title: str, icon: str = ""):
    icon_html = f"{clean_text(icon)}&nbsp;" if icon else ""
    st.markdown(f'<div class="section-heading">{icon_html}{clean_text(title)}</div>', unsafe_allow_html=True)


def render_info_panel(
    kicker: str, title: str, rows, badge_text: str = "", badge_kind: str = "signal-neutral", copy: str = ""
):
    rows_html = "".join(
        f"<div class='panel-row'><span>{clean_text(label)}</span><strong>{display_value(value)}</strong></div>"
        for label, value in rows
    )
    copy_html = f"<div class='panel-copy'>{display_value(copy)}</div>" if copy else ""
    badge_html = (
        f"<div style='margin-top:16px'><span class='{badge_kind}'>{clean_text(badge_text)}</span></div>"
        if badge_text
        else ""
    )

    st.markdown(
        f"""
        <div class="info-panel surface-compact">
            <div class="panel-kicker">{clean_text(kicker)}</div>
            <div class="panel-title">{clean_text(title)}</div>
            {copy_html}
            <div class="panel-list">{rows_html}</div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_market_brief(brief):
    cols = st.columns(2)
    for col, card in zip(cols * 2, brief.values()):
        why_html = "".join(f"<div class='why-item'>{clean_text(reason)}</div>" for reason in card.get("why", []))
        with col:
            st.markdown(
                f"""
                <div class="overview-card">
                    <div class="metric-label">{clean_text(card['label'])}</div>
                    <div class="metric-value">{display_value(card['title'])}</div>
                    <div class="overview-detail">{display_value(card['detail'])}</div>
                    <div style="margin-top:14px"><span class="{card['class']}">{clean_text(card['badge'])}</span></div>
                    <div class="why-list">{why_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_health_bar(health_summary: dict):
    healthy = health_summary.get("healthy_sources", 0)
    failed = len(health_summary.get("failed_sources", []))
    stale = len(health_summary.get("stale_sources", []))
    st.markdown(
        f"""
        <div class="health-strip">
            <span class="health-pill health-ok">OK {healthy}</span>
            <span class="health-pill health-fail">Fail {failed}</span>
            <span class="health-pill health-stale">Stale {stale}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_data_table_card(title: str, rows, kicker: str = "", caption: str = ""):
    kicker_html = f"<div class='table-kicker'>{clean_text(kicker)}</div>" if kicker else ""
    caption_html = f"<div class='table-caption'>{clean_text(caption)}</div>" if caption else ""
    rows_html = "".join(
        f"""
        <tr>
            <td>{clean_text(label)}</td>
            <td>{display_value(value)}</td>
        </tr>
        """
        for label, value in rows
    )
    st.markdown(
        f"""
        <div class="data-card">
            {kicker_html}
            <div class="table-title">{clean_text(title)}</div>
            {caption_html}
            <table class="terminal-table">
                <thead>
                    <tr>
                        <th>Metrik</th>
                        <th>Deger</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

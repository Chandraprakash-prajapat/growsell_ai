"""Shared look: styles, cards, simple charts (pure HTML/CSS) and small helpers.

The colours work in both the light and the dark Streamlit theme.
"""
import base64
from html import escape

import streamlit as st

CSS = """
<style>
:root { --gs-card: rgba(127,127,127,0.07); --gs-line: rgba(127,127,127,0.28); --gs-track: rgba(127,127,127,0.18); }
.block-container { padding-top: 2rem; max-width: 1180px; }
h1 { font-weight: 700; letter-spacing: -0.02em; }
footer { visibility: hidden; }
[data-testid="stAppDeployButton"] { display: none; }
[data-testid="stSidebar"] { border-right: 1px solid var(--gs-line); }

.badge { display: inline-block; background: rgba(99,102,241,0.15); color: #6366F1; font-size: 0.78rem;
         font-weight: 600; padding: 3px 11px; border-radius: 999px; margin-bottom: 6px; }

.hero { position: relative; overflow: hidden; background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 55%, #C026D3 100%);
        border-radius: 22px; padding: 46px 42px; color: #FFFFFF; margin-bottom: 26px; }
.hero::before { content: ""; position: absolute; right: -60px; top: -80px; width: 320px; height: 320px;
                border-radius: 50%; background: rgba(255,255,255,0.10); }
.hero::after { content: ""; position: absolute; right: 120px; bottom: -120px; width: 260px; height: 260px;
               border-radius: 50%; background: rgba(255,255,255,0.08); }
.hero .tag { font-size: 0.82rem; font-weight: 600; opacity: 0.9; letter-spacing: 0.06em; text-transform: uppercase; }
.hero h1 { color: #FFFFFF; font-size: 2.7rem; line-height: 1.15; margin: 10px 0 14px 0; padding: 0; position: relative; }
.hero p { font-size: 1.06rem; line-height: 1.6; max-width: 620px; opacity: 0.94; margin: 0; position: relative; }

.gs-card { background: var(--gs-card); border: 1px solid var(--gs-line); border-radius: 16px; padding: 20px 22px;
           box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-bottom: 8px; }
.gs-card.tall { min-height: 180px; }
.gs-title { font-weight: 650; font-size: 1.05rem; }
.gs-sub { opacity: 0.65; font-size: 0.85rem; margin: 2px 0 16px 0; }
.gs-card p { opacity: 0.8; font-size: 0.93rem; line-height: 1.55; margin: 6px 0 0 0; }

.ico { width: 44px; height: 44px; border-radius: 12px; padding: 10px; flex: none; box-sizing: border-box; }
.tone-indigo { background: linear-gradient(135deg, #6366F1, #8B5CF6); }
.tone-green  { background: linear-gradient(135deg, #10B981, #34D399); }
.tone-red    { background: linear-gradient(135deg, #EF4444, #F87171); }
.tone-amber  { background: linear-gradient(135deg, #F59E0B, #FBBF24); }
.tone-blue   { background: linear-gradient(135deg, #0EA5E9, #38BDF8); }

.kpi { display: flex; gap: 14px; align-items: center; background: var(--gs-card); border: 1px solid var(--gs-line);
       border-radius: 16px; padding: 16px 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); margin-bottom: 8px; min-height: 104px; box-sizing: border-box; }
.kpi-label { opacity: 0.7; font-size: 0.85rem; font-weight: 500; }
.kpi-value { font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em; line-height: 1.2; }
.kpi-note { opacity: 0.6; font-size: 0.78rem; margin-top: 2px; }
.chip { display: inline-block; font-size: 0.74rem; font-weight: 650; padding: 2px 9px; border-radius: 999px;
        background: rgba(16,185,129,0.16); color: #10B981; margin-top: 4px; }

.callout { border-left: 4px solid #6366F1; background: rgba(99,102,241,0.10); border-radius: 12px;
           padding: 14px 18px; margin: 6px 0 14px 0; line-height: 1.55; }
.callout.amber { border-left-color: #F59E0B; background: rgba(245,158,11,0.12); }

.rows { display: flex; flex-direction: column; gap: 14px; }
.row { display: grid; grid-template-columns: 150px 1fr 84px; gap: 12px; align-items: center; }
.row-lab { font-size: 0.88rem; font-weight: 550; line-height: 1.25; }
.row-sub { display: block; font-size: 0.74rem; font-weight: 400; opacity: 0.6; }
.row-track { background: var(--gs-track); border-radius: 8px; height: 14px; display: flex; overflow: hidden; }
.row-bar { height: 100%; border-radius: 8px; }
.seg { height: 100%; }
.row-val { text-align: right; font-weight: 650; font-size: 0.9rem; }
.legend { display: flex; flex-wrap: wrap; gap: 14px; margin-bottom: 14px; font-size: 0.8rem; opacity: 0.85; }
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 6px; }

.wf { display: flex; gap: 12px; align-items: flex-start; }
.wf-col { flex: 1; text-align: center; min-width: 0; }
.wf-val { font-weight: 650; font-size: 0.88rem; margin-bottom: 8px; height: 1.2em; }
.wf-track { position: relative; border-bottom: 1px solid var(--gs-line); }
.wf-bar { position: absolute; left: 14%; right: 14%; border-radius: 7px 7px 3px 3px; }
.wf-lab { font-size: 0.76rem; opacity: 0.7; margin-top: 8px; line-height: 1.25; min-height: 2.5em; }

.donut-box { position: relative; width: 168px; height: 168px; margin: 4px auto 18px auto; }
.donut { width: 100%; height: 100%; border-radius: 50%;
         -webkit-mask: radial-gradient(farthest-side, transparent 63%, #000 64%);
         mask: radial-gradient(farthest-side, transparent 63%, #000 64%); }
.donut-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.donut-center b { font-size: 1.35rem; }
.donut-center span { font-size: 0.75rem; opacity: 0.65; }
.lg { display: grid; grid-template-columns: 1fr auto 44px; gap: 8px; align-items: center; font-size: 0.86rem; margin-bottom: 8px; }
.lg-pct { opacity: 0.6; text-align: right; font-size: 0.8rem; }

.timeline { display: flex; flex-direction: column; gap: 10px; }
.tl { display: flex; gap: 12px; align-items: center; font-size: 0.92rem; }
.tl-num { flex: none; width: 26px; height: 26px; border-radius: 50%; background: rgba(99,102,241,0.18); color: #6366F1;
          font-weight: 700; font-size: 0.78rem; display: flex; align-items: center; justify-content: center; }

.tbl-wrap { overflow-x: auto; background: var(--gs-card); border: 1px solid var(--gs-line); border-radius: 14px; }
.tbl { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.tbl th { text-align: left; font-weight: 600; font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.04em;
          opacity: 0.65; padding: 12px 14px; border-bottom: 1px solid var(--gs-line); white-space: nowrap; }
.tbl td { padding: 11px 14px; border-bottom: 1px solid var(--gs-line); white-space: nowrap; }
.tbl tr:last-child td { border-bottom: none; }
.tbl .num { text-align: right; font-variant-numeric: tabular-nums; }
.tbl th.num { text-align: right; }
.mini { display: inline-block; width: 54px; height: 6px; border-radius: 4px; background: var(--gs-track);
        margin-left: 8px; vertical-align: middle; overflow: hidden; }
.mini i { display: block; height: 100%; background: #6366F1; border-radius: 4px; }

div[class*="st-key-tile-"] { background: var(--gs-card); border: 1px solid var(--gs-line); border-radius: 20px;
                             padding: 18px 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); }
div[class*="st-key-tile-feature"] { min-height: 235px; }
.tone-glass { background: rgba(255,255,255,0.22); }
.kpi.accent { background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%) !important; border-color: rgba(255,255,255,0.3) !important; color: #FFFFFF !important; }
.kpi.accent .kpi-label, .kpi.accent .kpi-note { color: #FFFFFF !important; opacity: 0.85; }
.kpi.accent .kpi-value { color: #FFFFFF !important; font-size: 2.15rem; }
.kpi.accent .chip { background: rgba(255,255,255,0.22); color: #FFFFFF; }
.stat-big { font-size: 2.6rem; font-weight: 750; letter-spacing: -0.03em; line-height: 1.1; color: #6366F1; }
.stat-big.amber { color: #F59E0B; }
.stat-text { opacity: 0.8; line-height: 1.5; margin-top: 4px; }
.report p { margin: 0.2rem 0 0.7rem 0; line-height: 1.6; }
.report ol, .report ul { margin: 0.2rem 0 0.8rem 1.2rem; padding: 0; line-height: 1.6; }
.act-title { font-weight: 650; }
.act-title.done { opacity: 0.55; text-decoration: line-through; }
.step { display: flex; gap: 14px; align-items: flex-start; margin-bottom: 14px; }
.step .num { flex: none; width: 32px; height: 32px; border-radius: 50%; background: linear-gradient(135deg, #6366F1, #8B5CF6);
             color: #FFFFFF; font-weight: 700; display: flex; align-items: center; justify-content: center; }
.step p { margin: 4px 0 0 0; opacity: 0.85; }
</style>
"""

# Extra styles used only when the seller switches Dark mode on (the base Streamlit theme is light).
DARK_CSS = """
<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stMain"] { background: #0E1117 !important; color: #FAFAFA !important; }
[data-testid="stSidebar"], [data-testid="stSidebar"] > div { background: #161B22 !important; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp li, .stApp label,
[data-testid="stMarkdownContainer"], [data-testid="stCaptionContainer"], [data-testid="stWidgetLabel"] { color: #FAFAFA !important; }
[data-testid="stSidebar"] a, [data-testid="stSidebar"] a span, [data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #E6EDF3 !important; }
[data-testid="stSidebar"] a[aria-current="page"] { background: rgba(99,102,241,0.25) !important; }
[data-testid="stSidebarHeader"] button, [data-testid="stSidebarCollapseButton"] button, [data-testid="stSidebarCollapseButton"] span { color: #E6EDF3 !important; }
.stButton > button, [data-testid="stFormSubmitButton"] > button, [data-testid^="stBaseButton-secondary"] {
    background: #21262D !important; color: #FAFAFA !important; border: 1px solid #3B434E !important; }
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"] {
    background: #6366F1 !important; border-color: #6366F1 !important; color: #FFFFFF !important; }
[data-baseweb="input"], [data-baseweb="input"] > div, [data-baseweb="input"] input { background: #161B22 !important; color: #FAFAFA !important; }
[data-testid="stExpander"] details { background: transparent !important; border-color: rgba(250,250,250,0.18) !important; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color: #FAFAFA !important; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color: rgba(250,250,250,0.18) !important; }
[data-testid="stForm"] { border-color: rgba(250,250,250,0.18) !important; }
[data-testid="stAlert"] * { color: #FAFAFA !important; }
[data-testid="stVegaLiteChart"], [data-testid="stArrowVegaLiteChart"], [data-testid="stDataFrame"] { filter: invert(0.92) hue-rotate(180deg) brightness(1.1); }
[data-testid="stDownloadButton"] button { background: #21262D !important; color: #FAFAFA !important; border: 1px solid #3B434E !important; }
div[role="dialog"] { background: #161B22 !important; }
</style>
"""


# "Spatial" look (like visionOS): aurora background, frosted glass panels, floating sidebar, soft depth.
SPATIAL_CSS = """
<style>
:root { --gs-card: rgba(255,255,255,0.58); --gs-line: rgba(70,80,140,0.14); --gs-track: rgba(70,80,140,0.12);
        --gs-glass-border: rgba(255,255,255,0.80); --gs-shadow: 0 12px 40px rgba(60,70,160,0.14);
        --gs-highlight: inset 0 1px 0 rgba(255,255,255,0.85); }
[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"] { background: transparent !important; }
.stApp {
    background:
        radial-gradient(1000px 620px at 6% -8%, #c7d2fe 0%, rgba(199,210,254,0) 62%),
        radial-gradient(900px 600px at 98% 0%, #fbcfe8 0%, rgba(251,207,232,0) 58%),
        radial-gradient(1000px 700px at 62% 108%, #bae6fd 0%, rgba(186,230,253,0) 62%),
        #eef1fb !important;
    background-attachment: fixed !important;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI Variable Display", "Segoe UI", Inter, system-ui, sans-serif;
}
.stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp li, .stApp label, .stApp button, .stApp input { font-family: inherit !important; }

.kpi, .gs-card, .tbl-wrap, div[class*="st-key-tile-"], [data-testid="stExpander"] details, [data-testid="stForm"] {
    background: var(--gs-card) !important; border: 1px solid var(--gs-glass-border) !important; border-radius: 24px !important;
    -webkit-backdrop-filter: blur(22px) saturate(170%); backdrop-filter: blur(22px) saturate(170%);
    box-shadow: var(--gs-shadow), var(--gs-highlight) !important;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
}
.kpi:hover, .gs-card:hover, div[class*="st-key-tile-"]:hover { transform: translateY(-3px); box-shadow: 0 24px 54px rgba(60,70,160,0.22), var(--gs-highlight) !important; }
.callout { border-radius: 18px; -webkit-backdrop-filter: blur(18px); backdrop-filter: blur(18px); box-shadow: var(--gs-shadow); }

.hero { border: 1px solid rgba(255,255,255,0.35); border-radius: 30px;
        box-shadow: 0 34px 70px -26px rgba(99,102,241,0.65), inset 0 1px 0 rgba(255,255,255,0.4); }
.ico { box-shadow: 0 10px 22px rgba(60,70,160,0.30), inset 0 1px 0 rgba(255,255,255,0.45); border-radius: 15px; }
.badge { -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px); border: 1px solid var(--gs-glass-border); }
.wf-bar, .row-bar { background-image: linear-gradient(180deg, rgba(255,255,255,0.38), rgba(255,255,255,0)) !important;
                    box-shadow: 0 6px 16px rgba(99,102,241,0.28); }
.donut { filter: drop-shadow(0 10px 20px rgba(99,102,241,0.30)); }

[data-testid="stSidebar"] { background: transparent !important; border-right: none !important; }
[data-testid="stSidebar"] > div:first-child {
    margin: 12px 0 12px 12px; height: calc(100vh - 24px); border-radius: 28px;
    background: var(--gs-card) !important; border: 1px solid var(--gs-glass-border);
    -webkit-backdrop-filter: blur(26px) saturate(170%); backdrop-filter: blur(26px) saturate(170%);
    box-shadow: var(--gs-shadow), var(--gs-highlight);
}
[data-testid="stSidebarNav"] a { border-radius: 14px !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: rgba(99,102,241,0.18) !important; box-shadow: var(--gs-highlight); }

.stButton > button, [data-testid="stFormSubmitButton"] > button, [data-testid="stDownloadButton"] button {
    border-radius: 999px !important; background: var(--gs-card) !important; border: 1px solid var(--gs-glass-border) !important;
    -webkit-backdrop-filter: blur(14px); backdrop-filter: blur(14px); box-shadow: 0 6px 16px rgba(60,70,160,0.14), var(--gs-highlight);
    transition: transform 0.2s ease, box-shadow 0.2s ease; }
.stButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover { transform: translateY(-2px); }
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #6366F1, #8B5CF6) !important; color: #FFFFFF !important; border-color: rgba(255,255,255,0.4) !important;
    box-shadow: 0 10px 26px rgba(99,102,241,0.5), inset 0 1px 0 rgba(255,255,255,0.4) !important; }
[data-baseweb="input"], [data-baseweb="input"] > div { border-radius: 16px !important; }
</style>
"""

SPATIAL_DARK_CSS = """
<style>
:root { --gs-card: rgba(255,255,255,0.07); --gs-line: rgba(255,255,255,0.10); --gs-track: rgba(255,255,255,0.10);
        --gs-glass-border: rgba(255,255,255,0.16); --gs-shadow: 0 18px 50px rgba(0,0,0,0.45);
        --gs-highlight: inset 0 1px 0 rgba(255,255,255,0.14); }
.stApp {
    background:
        radial-gradient(900px 600px at 6% -6%, rgba(99,102,241,0.50) 0%, rgba(99,102,241,0) 62%),
        radial-gradient(800px 600px at 100% 4%, rgba(217,70,239,0.32) 0%, rgba(217,70,239,0) 58%),
        radial-gradient(900px 700px at 60% 108%, rgba(14,165,233,0.32) 0%, rgba(14,165,233,0) 62%),
        #090C17 !important;
    background-attachment: fixed !important;
}
.kpi:hover, .gs-card:hover, div[class*="st-key-tile-"]:hover { box-shadow: 0 26px 60px rgba(0,0,0,0.55), var(--gs-highlight) !important; }
.stButton > button, [data-testid="stFormSubmitButton"] > button { background: rgba(255,255,255,0.09) !important; border: 1px solid rgba(255,255,255,0.20) !important; color: #FAFAFA !important; }
.stButton > button[kind="primary"], button[data-testid="stBaseButton-primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, #6366F1, #8B5CF6) !important; color: #FFFFFF !important; }
[data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child { background-color: transparent !important; }
[data-testid="stSidebar"] > div:first-child { background: var(--gs-card) !important; }
[data-testid="stSidebarNav"] a[aria-current="page"] { background: rgba(99,102,241,0.30) !important; }
</style>
"""

# Icons are drawn as small SVGs (white lines) and placed on a coloured square.
ICON_PATHS = {
    "cart": '<path d="M3 4h2l2 11h11l2-8H7"/><circle cx="9" cy="19" r="1.5"/><circle cx="17" cy="19" r="1.5"/>',
    "check": '<path d="M5 13l4 4L19 7"/>',
    "refund": '<path d="M4 12a8 8 0 1 0 3-6.2"/><path d="M4 4v4h4"/>',
    "trend": '<polyline points="3 17 9 11 13 15 21 7"/><polyline points="15 7 21 7 21 13"/>',
    "box": '<path d="M21 8l-9-5-9 5v8l9 5 9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
    "alert": '<path d="M12 3l10 18H2z"/><path d="M12 10v5M12 18v.01"/>',
    "bot": '<rect x="4" y="8" width="16" height="11" rx="3"/><circle cx="9" cy="13.5" r="1"/><circle cx="15" cy="13.5" r="1"/><path d="M12 8V4M9 19v2M15 19v2"/>',
    "wallet": '<rect x="3" y="6" width="18" height="14" rx="3"/><path d="M3 10h18M16 15h2"/>',
    "list": '<path d="M8 6h12M8 12h12M8 18h12M4 6h.01M4 12h.01M4 18h.01"/>',
}


def icon(name, tone="indigo"):
    """A coloured rounded square with a white icon inside."""
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" '
           'stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + ICON_PATHS[name] + "</svg>")
    data = base64.b64encode(svg.encode()).decode()
    return f'<img class="ico tone-{tone}" src="data:image/svg+xml;base64,{data}">'


def inject_css(dark=False, spatial=False):
    """Add the shared styles. Dark mode and the spatial (glass) look are optional extras."""
    css = CSS + (DARK_CSS if dark else "") + (SPATIAL_CSS if spatial else "") + (SPATIAL_DARK_CSS if spatial and dark else "")
    st.markdown(css, unsafe_allow_html=True)


def page_header(title, subtitle):
    """Badge, title and one-line description."""
    st.markdown('<span class="badge">Sample data · demo only</span>', unsafe_allow_html=True)
    st.title(title)
    st.caption(subtitle)


def rupees(amount):
    """Format a number the Indian way: 134500 -> ₹1,34,500."""
    sign = "-" if amount < 0 else ""
    digits = str(int(abs(amount) + 0.5))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join(groups + [tail])
    return f"{sign}₹{digits}"


# ---------- Building blocks (each returns one line of HTML) ----------

def card(title, subtitle, body, tall=False):
    """A titled panel."""
    css = "gs-card tall" if tall else "gs-card"
    return (f'<div class="{css}"><div class="gs-title">{escape(title)}</div>'
            f'<div class="gs-sub">{escape(subtitle)}</div>{body}</div>')


def kpi_card(icon_name, label, value, note="", tone="indigo", chip="", accent=False):
    """A number with a label and an icon. accent=True makes it the big highlighted tile."""
    if accent:
        tone = "glass"
    note_html = f'<div class="kpi-note">{escape(note)}</div>' if note else ""
    chip_html = f'<div class="chip">{escape(chip)}</div>' if chip else ""
    css = "kpi accent" if accent else "kpi"
    return (f'<div class="{css}">{icon(icon_name, tone)}<div><div class="kpi-label">{escape(label)}</div>'
            f'<div class="kpi-value">{value}</div>{note_html}{chip_html}</div></div>')


def callout(text_html, tone="indigo"):
    """A highlighted sentence. text_html may contain <b>."""
    css = "callout amber" if tone == "amber" else "callout"
    return f'<div class="{css}">{text_html}</div>'


def bar_rows(rows, color="#6366F1"):
    """Horizontal bars. rows = [(label, value, small text under the label)]."""
    top = max((value for _, value, _ in rows), default=0) or 1
    html = []
    for label, value, sub in rows:
        sub_html = f'<span class="row-sub">{escape(sub)}</span>' if sub else ""
        width = max(value / top * 100, 0)
        html.append(f'<div class="row"><div class="row-lab">{escape(label)}{sub_html}</div>'
                    f'<div class="row-track"><div class="row-bar" style="width:{width:.1f}%;background:{color}"></div></div>'
                    f'<div class="row-val">{rupees(value)}</div></div>')
    return '<div class="rows">' + "".join(html) + "</div>"


def stacked_rows(rows, series):
    """Stacked horizontal bars. rows = [(label, [value per series], sub)], series = [(name, color)]."""
    top = max((sum(values) for _, values, _ in rows), default=0) or 1
    legend = "".join(f'<span><span class="dot" style="background:{c}"></span>{escape(n)}</span>' for n, c in series)
    html = []
    for label, values, sub in rows:
        sub_html = f'<span class="row-sub">{escape(sub)}</span>' if sub else ""
        segments = "".join(f'<div class="seg" style="width:{v / top * 100:.2f}%;background:{series[i][1]}"></div>'
                           for i, v in enumerate(values))
        html.append(f'<div class="row"><div class="row-lab">{escape(label)}{sub_html}</div>'
                    f'<div class="row-track">{segments}</div><div class="row-val">{rupees(sum(values))}</div></div>')
    return f'<div class="legend">{legend}</div><div class="rows">' + "".join(html) + "</div>"


def waterfall(steps, height=210):
    """Money flow. steps = [(label, value, kind)], kind = 'total', 'neg' or 'final'."""
    running, top, bars = 0, 0, []
    for label, value, kind in steps:
        if kind == "neg":
            low, high = running + value, running
            running += value
        else:
            low, high = 0, value
            running = value
        bars.append((label, value, kind, low, high))
        top = max(top, high)
    top = top or 1
    colors = {"total": "#6366F1", "neg": "#F87171", "final": "#10B981"}
    html = []
    for label, value, kind, low, high in bars:
        text = ("−" + rupees(abs(value))) if kind == "neg" else rupees(value)
        html.append(f'<div class="wf-col"><div class="wf-val">{text}</div>'
                    f'<div class="wf-track" style="height:{height}px"><div class="wf-bar" '
                    f'style="bottom:{low / top * 100:.2f}%;height:{max((high - low) / top * 100, 0.8):.2f}%;'
                    f'background:{colors[kind]}"></div></div><div class="wf-lab">{escape(label)}</div></div>')
    return '<div class="wf">' + "".join(html) + "</div>"


def donut(parts, center_value, center_label):
    """Ring chart. parts = [(label, value, color)]."""
    total = sum(value for _, value, _ in parts) or 1
    stops, used = [], 0.0
    for _, value, color in parts:
        share = value / total * 100
        stops.append(f"{color} {used:.2f}% {used + share:.2f}%")
        used += share
    legend = "".join(f'<div class="lg"><span><span class="dot" style="background:{color}"></span>{escape(label)}</span>'
                     f'<b>{rupees(value)}</b><span class="lg-pct">{value / total * 100:.0f}%</span></div>'
                     for label, value, color in parts)
    return (f'<div class="donut-box"><div class="donut" style="background:conic-gradient({", ".join(stops)})"></div>'
            f'<div class="donut-center"><b>{center_value}</b><span>{escape(center_label)}</span></div></div>{legend}')


def timeline(items):
    """Numbered list of what the agent did."""
    html = "".join(f'<div class="tl"><div class="tl-num">{n}</div><div>{escape(text)}</div></div>'
                   for n, text in enumerate(items, start=1))
    return f'<div class="timeline">{html}</div>'


def data_table(rows, columns, pct_max=100):
    """A table that follows the theme. columns = [(header, key, kind)], kind = text, int, money or pct."""
    head = "".join(f'<th class="{"num" if kind != "text" else ""}">{escape(header)}</th>' for header, _, kind in columns)
    body = []
    for row in rows:
        cells = []
        for _, key, kind in columns:
            value = row[key]
            if kind == "text":
                cells.append(f"<td>{escape(str(value))}</td>")
            elif kind == "money":
                cells.append(f'<td class="num">{rupees(value)}</td>')
            elif kind == "pct":
                width = min(max(value / pct_max * 100, 0), 100)
                cells.append(f'<td class="num">{value:.1f}%<span class="mini"><i style="width:{width:.0f}%"></i></span></td>')
            else:
                cells.append(f'<td class="num">{value}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f'<div class="tbl-wrap"><table class="tbl"><thead><tr>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def markdown_to_html(text):
    """Turn the agent's simple markdown (bold, lists, paragraphs) into safe HTML on one line."""
    import re
    html, open_list = [], None
    for line in text.strip().splitlines():
        line = escape(line.strip())
        line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
        line = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"<i>\1</i>", line)
        bullet = re.match(r"^[-*•] (.*)", line)
        number = re.match(r"^\d+[.)] (.*)", line)
        kind = "ul" if bullet else "ol" if number else None
        if kind != open_list:
            if open_list:
                html.append(f"</{open_list}>")
            if kind:
                html.append(f"<{kind}>")
            open_list = kind
        if kind:
            html.append(f"<li>{(bullet or number).group(1)}</li>")
        elif line:
            html.append(f"<p>{line}</p>")
    if open_list:
        html.append(f"</{open_list}>")
    return "".join(html)


def report_card(text):
    """The agent's report as a panel."""
    return card("Report", "Written by the agent from your numbers", f'<div class="report">{markdown_to_html(text)}</div>')


def action_card(title, note, done=False):
    """One action item (the Done button is placed next to it by the page)."""
    check = "✅ " if done else ""
    css = "act-title done" if done else "act-title"
    return f'<div class="gs-card"><div class="{css}">{check}{escape(title)}</div><div class="gs-sub" style="margin-bottom:0">{escape(note)}</div></div>'


def tile(name):
    """A bento tile: a glass panel that can hold any Streamlit element (chart, table, button)."""
    try:
        return st.container(key=f"tile-{name}")
    except TypeError:                       # very old Streamlit without container keys
        return st.container(border=True)


def tile_head(title, subtitle=""):
    """Title and small description at the top of a tile."""
    sub = f'<div class="gs-sub">{escape(subtitle)}</div>' if subtitle else ""
    st.markdown(f'<div class="gs-title">{escape(title)}</div>{sub}', unsafe_allow_html=True)

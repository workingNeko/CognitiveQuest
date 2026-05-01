"""
Shared theme CSS for Cognitive Quest
"""

GLOBAL_CSS = """
<style>
    /* ── Google Fonts ─────────────────────────────────────────────── */
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;1,9..40,300&display=swap');

    /* ── CSS Variables ───────────────────────────────────────────── */
    :root {
        --bg:            #0d0f1a;
        --bg-card:       #13162a;
        --bg-card2:      #181c32;
        --border:        rgba(139,92,246,0.18);
        --border-subtle: rgba(255,255,255,0.06);
        --accent:        #8b5cf6;
        --accent2:       #6366f1;
        --accent3:       #38bdf8;
        --green:         #10b981;
        --amber:         #f59e0b;
        --red:           #ef4444;
        --text:          #e2e8f0;
        --text-muted:    #64748b;
        --text-dim:      #94a3b8;
        --radius:        14px;
        --radius-sm:     8px;
        --shadow:        0 4px 32px rgba(0,0,0,0.45);
        --shadow-glow:   0 0 40px rgba(139,92,246,0.15);
    }

    /* ── Base ────────────────────────────────────────────────────── */
    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stMain"], section.main {
        background: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'DM Sans', sans-serif !important;
    }

    /* Background pattern */
    [data-testid="stAppViewContainer"]::before {
        content: '';
        position: fixed;
        inset: 0;
        background:
            radial-gradient(ellipse 800px 600px at 10% 0%, rgba(99,102,241,0.12) 0%, transparent 70%),
            radial-gradient(ellipse 600px 500px at 90% 100%, rgba(139,92,246,0.10) 0%, transparent 70%);
        pointer-events: none;
        z-index: 0;
    }

    /* ── Sidebar ─────────────────────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: var(--bg-card) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * { color: var(--text) !important; }
    [data-testid="stSidebarNav"] { display: none !important; }

    /* ── Typography ──────────────────────────────────────────────── */
    h1, h2, h3, h4 {
        font-family: 'Syne', sans-serif !important;
        color: var(--text) !important;
        letter-spacing: -0.02em;
    }
    h1 { font-size: 2rem !important; font-weight: 700 !important; }
    h2, h3 { font-weight: 600 !important; }
    p, li, span, label, div {
        font-family: 'DM Sans', sans-serif !important;
    }

    /* ── Metric Cards ────────────────────────────────────────────── */
    [data-testid="metric-container"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        padding: 1.25rem 1.5rem !important;
        box-shadow: var(--shadow) !important;
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    [data-testid="metric-container"]:hover {
        border-color: rgba(139,92,246,0.45) !important;
        box-shadow: var(--shadow), var(--shadow-glow) !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricLabel"] {
        font-size: 0.75rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: var(--text-muted) !important;
        font-weight: 500 !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-family: 'Syne', sans-serif !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        color: var(--text) !important;
    }
    [data-testid="stMetricDelta"] svg { display: none; }

    /* ── Buttons ─────────────────────────────────────────────────── */
    .stButton > button {
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
        border-radius: var(--radius-sm) !important;
        border: 1px solid var(--border) !important;
        background: var(--bg-card2) !important;
        color: var(--text-dim) !important;
        transition: all 0.18s ease !important;
        padding: 0.45rem 1.1rem !important;
        letter-spacing: 0.01em;
    }
    .stButton > button:hover {
        border-color: var(--accent) !important;
        color: var(--text) !important;
        background: rgba(139,92,246,0.12) !important;
        box-shadow: 0 0 16px rgba(139,92,246,0.2) !important;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
        border: none !important;
        color: #fff !important;
        box-shadow: 0 4px 20px rgba(139,92,246,0.35) !important;
    }
    .stButton > button[kind="primary"]:hover {
        box-shadow: 0 4px 28px rgba(139,92,246,0.55) !important;
        transform: translateY(-1px) !important;
    }

    /* ── Inputs ──────────────────────────────────────────────────── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div,
    .stNumberInput > div > div > input,
    .stTextArea > div > div > textarea {
        background: var(--bg-card2) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text) !important;
        font-family: 'DM Sans', sans-serif !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 3px rgba(139,92,246,0.15) !important;
    }

    /* ── DataFrame / Data Editor ─────────────────────────────────── */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        overflow: hidden !important;
    }
    .dvn-scroller { background: var(--bg-card) !important; }

    /* ── Expanders ───────────────────────────────────────────────── */
    details[data-testid="stExpander"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        overflow: hidden !important;
    }
    details[data-testid="stExpander"] summary {
        font-family: 'Syne', sans-serif !important;
        font-weight: 600 !important;
        color: var(--text) !important;
        padding: 1rem 1.25rem !important;
    }

    /* ── Tabs ────────────────────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        background: var(--bg-card) !important;
        border-radius: var(--radius) !important;
        padding: 4px !important;
        border: 1px solid var(--border) !important;
        gap: 2px !important;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text-muted) !important;
        font-family: 'DM Sans', sans-serif !important;
        font-weight: 500 !important;
        font-size: 0.85rem !important;
        padding: 0.5rem 1rem !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, var(--accent), var(--accent2)) !important;
        color: #fff !important;
    }
    .stTabs [data-baseweb="tab-panel"] {
        background: var(--bg-card) !important;
        border: 1px solid var(--border) !important;
        border-top: none !important;
        border-radius: 0 0 var(--radius) var(--radius) !important;
        padding: 1.5rem !important;
    }

    /* ── Divider ─────────────────────────────────────────────────── */
    hr {
        border-color: var(--border-subtle) !important;
        margin: 1.5rem 0 !important;
    }

    /* ── Alerts ──────────────────────────────────────────────────── */
    .stAlert {
        border-radius: var(--radius-sm) !important;
        border: 1px solid var(--border) !important;
    }

    /* ── Progress bar ────────────────────────────────────────────── */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--accent), var(--accent3)) !important;
        border-radius: 999px !important;
    }
    .stProgress > div > div {
        background: var(--bg-card2) !important;
        border-radius: 999px !important;
    }

    /* ── Selectbox dropdown ──────────────────────────────────────── */
    [data-baseweb="select"] > div {
        background: var(--bg-card2) !important;
        border-color: var(--border) !important;
        border-radius: var(--radius-sm) !important;
        color: var(--text) !important;
    }
    [data-baseweb="popover"] { background: var(--bg-card2) !important; }
    [role="option"] { background: var(--bg-card2) !important; color: var(--text) !important; }
    [role="option"]:hover { background: rgba(139,92,246,0.18) !important; }

    /* ── Section headers ─────────────────────────────────────────── */
    .section-label {
        font-family: 'Syne', sans-serif;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: var(--accent);
        margin-bottom: 0.35rem;
    }

    /* ── Streamlit block / container wrappers ────────────────────── */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] {
        background: transparent !important;
    }

    /* ── File uploader ───────────────────────────────────────────── */
    [data-testid="stFileUploader"] {
        background: var(--bg-card2) !important;
        border: 1px dashed var(--border) !important;
        border-radius: var(--radius) !important;
    }

    /* ── Caption / small text ────────────────────────────────────── */
    .stCaption, small { color: var(--text-muted) !important; }

    /* ── Scrollbar ───────────────────────────────────────────────── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: var(--accent); }

    /* ── Plotly chart backgrounds ────────────────────────────────── */
    .js-plotly-plot .plotly { background: transparent !important; }
    .svg-container { background: transparent !important; }
</style>
"""

PLOTLY_TEMPLATE = {
    "layout": {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": "#94a3b8", "family": "DM Sans"},
        "title": {"font": {"color": "#e2e8f0", "family": "Syne"}},
        "xaxis": {
            "gridcolor": "rgba(255,255,255,0.05)",
            "linecolor": "rgba(255,255,255,0.08)",
            "tickfont": {"color": "#64748b"},
            "zerolinecolor": "rgba(255,255,255,0.05)"
        },
        "yaxis": {
            "gridcolor": "rgba(255,255,255,0.05)",
            "linecolor": "rgba(255,255,255,0.08)",
            "tickfont": {"color": "#64748b"},
            "zerolinecolor": "rgba(255,255,255,0.05)"
        },
        "legend": {"bgcolor": "rgba(0,0,0,0)", "font": {"color": "#94a3b8"}},
        "colorway": ["#8b5cf6", "#38bdf8", "#10b981", "#f59e0b", "#ef4444", "#6366f1"],
        "margin": {"l": 10, "r": 10, "t": 30, "b": 10}
    }
}
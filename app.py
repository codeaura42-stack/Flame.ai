import streamlit as st

# Add your AI chatbot URL here later. Example: "http://192.168.29.164:8503"
AI_CHATBOT_URL = "http://192.168.29.164:8501"

st.set_page_config(
    page_title="Flame.ai | Mission Control",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------
# NASA-inspired visual styling
# --------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Inter:wght@400;500;600;700;800&display=swap');

    :root {
        --fg-bg: #050505;
        --fg-panel: #11100d;
        --fg-panel-2: #1a1510;
        --fg-border: #3a2a17;
        --fg-text: #ffffff;
        --fg-muted: #d0c8bd;
        --fg-red: #ff8a00;
        --fg-cyan: #ffd166;
    }

    .stApp {
        background:
            radial-gradient(ellipse at 50% -12%, rgba(255, 145, 0, 0.22), transparent 36%),
            radial-gradient(ellipse at 50% 0%, rgba(255, 196, 61, 0.10), transparent 52%),
            linear-gradient(180deg, #050505 0%, #090806 52%, #050505 100%);
        color: var(--fg-text);
        font-family: 'Inter', sans-serif;
    }

    [data-testid="stHeader"] {
        background: rgba(7, 17, 31, 0.88);
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1180px;
        padding-top: 2.2rem;
        padding-bottom: 2rem;
    }

    .fg-topline {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 1rem;
        color: var(--fg-muted);
        font-family: 'DM Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        border-bottom: 1px solid var(--fg-border);
        padding-bottom: 1rem;
        margin-bottom: 2.5rem;
    }

    .fg-status {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        color: #ffd166;
        letter-spacing: 0.06em;
    }

    .fg-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: #ffb52e;
        box-shadow: 0 0 12px rgba(255, 181, 46, 0.8);
        display: inline-block;
    }

    .fg-hero {
        text-align: center;
        padding: 1.1rem 0 2rem;
    }

    .fg-eyebrow {
        color: #ffd166;
        font-family: 'DM Mono', monospace;
        font-size: 0.76rem;
        letter-spacing: 0.22em;
        text-transform: uppercase;
        margin-bottom: 1.2rem;
    }

    .fg-brand {
        color: #ffffff;
        font-size: clamp(3.1rem, 8vw, 5.5rem);
        line-height: 0.98;
        font-weight: 800;
        letter-spacing: -0.075em;
        margin: 0;
    }

    .fg-brand span {
        color: #ff9f1c;
    }

    .fg-hero-copy {
        max-width: 650px;
        margin: 1.2rem auto 0;
        color: #e4ddd3;
        font-size: 1.08rem;
        line-height: 1.8;
    }

    .fg-mission-strip {
        display: flex;
        justify-content: center;
        flex-wrap: wrap;
        gap: 0.65rem;
        margin-top: 1.5rem;
    }

    .fg-chip {
        border: 1px solid #4a341b;
        border-radius: 3px;
        padding: 0.42rem 0.72rem;
        color: #ffffff;
        background: rgba(16, 36, 58, 0.7);
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.08em;
    }

    .fg-section-label {
        color: var(--fg-muted);
        font-family: 'DM Mono', monospace;
        font-size: 0.72rem;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        margin: 1.5rem 0 1rem;
    }

    .fg-card {
        height: 100%;
        min-height: 310px;
        position: relative;
        overflow: hidden;
        background:
            radial-gradient(ellipse at 50% 0%, rgba(255, 153, 0, 0.08), transparent 55%),
            linear-gradient(145deg, rgba(22, 19, 15, 0.98), rgba(9, 9, 9, 0.99));
        border: 1px solid var(--fg-border);
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 18px 45px rgba(0, 0, 0, 0.16);
    }

    .fg-card:before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        height: 3px;
        width: 100%;
        background: linear-gradient(90deg, #ff7a00, #ffd166);
    }

    .fg-card.bass:before {
        background: linear-gradient(90deg, #ff9f1c, #ffd166);
    }

    .fg-card-code {
        color: var(--fg-muted);
        font-family: 'DM Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 0.13em;
        text-transform: uppercase;
    }

    .fg-card-icon {
        font-size: 2rem;
        margin: 1.2rem 0 0.6rem;
    }

    .fg-card h2 {
        color: var(--fg-text);
        font-size: 1.65rem;
        letter-spacing: -0.04em;
        margin: 0 0 0.7rem;
    }

    .fg-card p {
        color: var(--fg-muted);
        line-height: 1.75;
        margin-bottom: 1.4rem;
    }

    .fg-card-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 1rem;
    }

    .fg-meta-pill {
        color: #fff5e5;
        border: 1px solid #574022;
        border-radius: 4px;
        padding: 0.3rem 0.5rem;
        font-size: 0.72rem;
    }

    div.stLinkButton > a {
        border: 1px solid #ff9800 !important;
        background: linear-gradient(110deg, #f57c00, #ffb300) !important;
        color: #ffffff !important;
        border-radius: 5px !important;
        font-weight: 700 !important;
        transition: transform 150ms ease, filter 150ms ease;
    }

    div.stLinkButton > a:hover {
        filter: brightness(1.1);
        transform: translateY(-1px);
    }

    .fg-card-footer {
        color: #b8a58d;
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.07em;
        margin-top: 1rem;
    }

    .fg-footer {
        border-top: 1px solid var(--fg-border);
        margin-top: 3rem;
        padding-top: 1.25rem;
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.75rem;
        color: #b8afa3;
        font-family: 'DM Mono', monospace;
        font-size: 0.68rem;
        letter-spacing: 0.05em;
    }

    @media (max-width: 700px) {
        [data-testid="stMainBlockContainer"] {
            padding-top: 1.2rem;
        }
        .fg-topline {
            margin-bottom: 1.3rem;
            font-size: 0.6rem;
        }
        .fg-hero {
            padding-bottom: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------
# Mission header
# --------------------------------------------------
st.markdown(
    """
    <div class="fg-topline">
        <span>Flame.ai / RESEARCH SYSTEMS</span>
        <span class="fg-status"><span class="fg-dot"></span> SYSTEMS READY</span>
    </div>

    <section class="fg-hero">
        <div class="fg-eyebrow">MICROGRAVITY COMBUSTION RESEARCH</div>
        <h1 class="fg-brand">FLAME.<span>AI</span></h1>
        <p class="center-text">
            Mission control for exploring combustion experiments in space.
            Search original NASA research records, inspect measurements,
            and compare experiments across two scientific datasets.
        </p>
        <div class="fg-mission-strip">
            <span class="fg-chip">DATA EXPLORATION</span>
            <span class="fg-chip">EXPERIMENT COMPARISON</span>
            <span class="fg-chip">ORIGINAL RECORDS</span>
        </div>
    </section>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="fg-section-label">01 / Select a research dataset</div>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown(
        """
        <div class="fg-card">
            <div class="fg-card-code">DATA MODULE / FLEX-01</div>
            <div class="fg-card-icon">◉</div>
            <h2>FLEX</h2>
            <p>
                Explore liquid-fuel droplet combustion experiments.
                Search records and investigate recorded measurements
                from the FLEX experiment dataset.
            </p>
            <div class="fg-card-meta">
                <span class="fg-meta-pill">LIQUID FUEL</span>
                <span class="fg-meta-pill">DROPLET COMBUSTION</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button(
        "Launch FLEX Explorer  ↗",
        "https://flameai-nve7syek9yyknbvexatffg.streamlit.app",
        use_container_width=True,
    )
    st.markdown(
        '<div class="fg-card-footer">MODULE STATUS · OPEN EXPLORER TO BEGIN</div>',
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="fg-card bass">
            <div class="fg-card-code">DATA MODULE / BASS-02</div>
            <div class="fg-card-icon">✳</div>
            <h2>BASS-II</h2>
            <p>
                Explore solid-fuel combustion experiments.
                Inspect experiment details and compare recorded gas
                measurements and other source parameters.
            </p>
            <div class="fg-card-meta">
                <span class="fg-meta-pill">SOLID FUEL</span>
                <span class="fg-meta-pill">COMBUSTION MEASUREMENTS</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.link_button(
        "Launch BASS-II Explorer  ↗",
        "https://flameai-ck9m8vksedfbicjypmmvjw.streamlit.app",
        use_container_width=True,
    )
    st.markdown(
        '<div class="fg-card-footer">MODULE STATUS · OPEN EXPLORER TO BEGIN</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    """
    <div class="fg-footer">
        <span>FLAMEGUARD · MICROGRAVITY RESEARCH INTERFACE</span>
        <span>DATA-DRIVEN EXPLORATION · NO PREDICTIVE CLASSIFICATION</span>
    </div>
    """,
    unsafe_allow_html=True,
)

with col3:
    st.markdown(
        """
        <div class="fg-card">
            <div class="fg-card-code">AI MODULE / CHAT-03</div>
            <div class="fg-card-icon">✦</div>
            <h2>AI Assistant</h2>
            <p>
                Ask questions and discuss combustion research with AI.
                Export your conversations so you can keep useful answers
                and refer to them later.
            </p>
            <div class="fg-card-meta">
                <span class="fg-meta-pill">AI CHAT</span>
                <span class="fg-meta-pill">ASK QUESTIONS</span>
                <span class="fg-meta-pill">EXPORT CHAT</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if AI_CHATBOT_URL.strip():
        st.link_button(
            "Launch AI Assistant  ↗",
            AI_CHATBOT_URL.strip(),
            use_container_width=True,
        )
        st.markdown(
            '<div class="fg-card-footer">MODULE STATUS · AI ASSISTANT READY</div>',
            unsafe_allow_html=True,
        )
    else:
        st.button(
            "Add chatbot URL to activate",
            disabled=True,
            use_container_width=True,
        )
        st.markdown(
            '<div class="fg-card-footer">MODULE STATUS · URL NOT CONFIGURED</div>',
            unsafe_allow_html=True,
        )

st.markdown(
    """
    <div class="fg-footer">
        <span>FLAMEGUARD · MICROGRAVITY RESEARCH INTERFACE</span>
        <span>DATA-DRIVEN EXPLORATION · NO PREDICTIVE CLASSIFICATION</span>
    </div>
    """,
    unsafe_allow_html=True,
)

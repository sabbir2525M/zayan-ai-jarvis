import os
import hmac
import re
import tempfile
from io import BytesIO

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

try:
    import fitz  # PyMuPDF, used for text-based PDFs
except ImportError:
    fitz = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

load_dotenv()

st.set_page_config(page_title="Zayan AI Dashboard", page_icon="🤖", layout="wide")


# --- Zayan AI website-style theme ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Hind+Siliguri:wght@400;500;600;700&display=swap');

:root {
  --zayan-bg: #0b1020;
  --zayan-panel: #121a2d;
  --zayan-panel-2: #18233a;
  --zayan-line: rgba(148,163,184,.16);
  --zayan-text: #edf3ff;
  --zayan-muted: #9aa9c2;
  --zayan-accent: #7c6cff;
  --zayan-cyan: #25c6da;
}
html, body, [class*="css"] {
  font-family: 'Inter', 'Hind Siliguri', sans-serif;
}
.stApp {
  background:
    radial-gradient(ellipse at 12% 0%, rgba(124,108,255,.18), transparent 34%),
    radial-gradient(ellipse at 88% 8%, rgba(37,198,218,.10), transparent 30%),
    var(--zayan-bg);
  color: var(--zayan-text);
}
[data-testid="stHeader"] { background: rgba(11,16,32,.72); }
[data-testid="stToolbar"] { right: 1rem; }
.block-container {
  max-width: 1440px;
  padding-top: 2rem;
  padding-bottom: 3rem;
}
#MainMenu, footer { visibility: hidden; }
h1, h2, h3, h4, p, label, span { letter-spacing: -.01em; }
h1 { font-weight: 800 !important; letter-spacing: -.045em !important; }
h2, h3 { font-weight: 700 !important; }
.zayan-hero {
  position: relative;
  overflow: hidden;
  padding: 30px 34px;
  border: 1px solid rgba(160,174,255,.22);
  border-radius: 24px;
  background: linear-gradient(120deg, rgba(35,44,83,.96), rgba(18,35,58,.92) 58%, rgba(20,68,83,.82));
  box-shadow: 0 22px 60px rgba(0,0,0,.24);
  margin-bottom: 24px;
}
.zayan-hero:after {
  content: "";
  position: absolute;
  width: 280px; height: 280px; right: -70px; top: -150px;
  border-radius: 50%;
  background: rgba(124,108,255,.25);
  filter: blur(8px);
}
.zayan-brand { font-size: 2.25rem; font-weight: 800; color: #fff; margin: 0; }
.zayan-subtitle { color: #c4cde0; margin-top: 7px; font-size: 1rem; }
.zayan-chip {
  display: inline-block; margin-top: 16px; margin-right: 8px;
  padding: 6px 11px; border-radius: 999px; font-size: .78rem;
  color: #e5e9ff; border: 1px solid rgba(255,255,255,.18);
  background: rgba(255,255,255,.08);
}
div[data-testid="stTabs"] [role="tablist"] {
  gap: 9px; border-bottom: 1px solid var(--zayan-line);
}
div[data-testid="stTabs"] button[role="tab"] {
  background: rgba(255,255,255,.045);
  border: 1px solid var(--zayan-line);
  border-radius: 12px 12px 0 0;
  padding: 12px 18px;
  color: #c7d2e7;
  font-weight: 600;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  background: linear-gradient(120deg, rgba(124,108,255,.22), rgba(37,198,218,.12));
  color: #fff; border-color: rgba(124,108,255,.5);
}
div[data-testid="stVerticalBlockBorderWrapper"] {
  border: 1px solid var(--zayan-line);
  border-radius: 18px;
  background: rgba(18,26,45,.76);
}
div[data-testid="stMetric"] {
  background: linear-gradient(145deg, rgba(26,37,62,.9), rgba(17,25,43,.9));
  border: 1px solid var(--zayan-line);
  border-radius: 16px; padding: 16px 18px;
}
div[data-testid="stMetricLabel"] { color: var(--zayan-muted); }
div[data-testid="stMetricValue"] { color: #fff; font-weight: 800; }
.stButton > button, .stDownloadButton > button {
  border: 0; border-radius: 11px; padding: .62rem 1.1rem;
  color: white; font-weight: 700;
  background: linear-gradient(105deg, #7565f5, #397fe8);
  box-shadow: 0 8px 22px rgba(87,105,230,.22);
  transition: transform .15s ease, filter .15s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  color: white; filter: brightness(1.12); transform: translateY(-1px);
}
input, textarea, [data-baseweb="select"] > div {
  border-radius: 10px !important;
}
[data-testid="stChatMessage"] {
  border: 1px solid var(--zayan-line);
  border-radius: 16px; background: rgba(21,31,52,.72);
  padding: 14px 16px;
}
[data-testid="stChatInput"] {
  border: 1px solid rgba(124,108,255,.42);
  border-radius: 15px; background: rgba(18,26,45,.95);
}
[data-testid="stFileUploader"] section {
  border: 1px dashed rgba(124,108,255,.5);
  border-radius: 14px; background: rgba(124,108,255,.045);
}
[data-testid="stDataFrame"], [data-testid="stTable"] {
  border: 1px solid var(--zayan-line); border-radius: 12px; overflow: hidden;
}
hr { border-color: var(--zayan-line); }
.zayan-footer {
  color: #8291aa; font-size: .8rem; text-align: center;
  padding: 24px 0 4px; border-top: 1px solid var(--zayan-line);
  margin-top: 35px;
}
@media (max-width: 700px) {
  .block-container { padding: 1rem .8rem 2rem; }
  .zayan-hero { padding: 22px 20px; border-radius: 18px; }
  .zayan-brand { font-size: 1.75rem; }
  div[data-testid="stTabs"] [role="tablist"] { flex-wrap: wrap; }
}

/* Reference-inspired command-center layout */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #101735 0%, #0c132b 100%);
  border-right: 1px solid rgba(90,122,220,.22);
}
[data-testid="stSidebar"] > div:first-child { padding-top: 1.2rem; }
.side-brand {
  display:flex; align-items:center; gap:12px; padding: 12px 10px 26px;
  border-bottom:1px solid rgba(133,157,235,.16); margin-bottom:24px;
}
.side-logo {
  display:flex; align-items:center; justify-content:center; width:42px; height:42px;
  border-radius:13px; color:#fff; font-size:25px;
  background:linear-gradient(140deg,#35c9e5,#7467ff);
  box-shadow:0 8px 24px rgba(65,120,240,.28);
}
.side-title { color:#f4f6ff; font-weight:800; font-size:1.22rem; letter-spacing:-.04em; }
.side-caption { color:#7889b2; font-size:.62rem; letter-spacing:.13em; margin-top:2px; }
.side-section-label {
  color:#64769f; font-size:.66rem; font-weight:800; letter-spacing:.15em;
  padding:8px 12px; margin-top:5px;
}
.side-nav-item {
  color:#9eaccd; padding:11px 13px; margin:4px 0; border-radius:10px;
  font-size:.88rem; border:1px solid transparent;
}
.side-nav-item.active {
  color:#fff; background:linear-gradient(100deg,rgba(69,112,238,.22),rgba(116,103,255,.12));
  border-color:rgba(91,132,255,.42);
  box-shadow:inset 3px 0 0 #6387ff;
}
.side-divider { height:1px; background:rgba(133,157,235,.14); margin:20px 8px; }
.top-workspace {
  color:#a9b8d9; font-size:.78rem; letter-spacing:.07em;
  font-weight:700; padding:8px 0 18px;
}
.top-workspace span { color:#56688f; padding:0 7px; }
.live-pill {
  text-align:center; margin-top:4px; color:#68e2b0; font-size:.68rem;
  letter-spacing:.08em; font-weight:800; border:1px solid rgba(68,211,158,.24);
  background:rgba(31,170,125,.09); padding:7px 9px; border-radius:999px;
}
.zayan-hero {
  padding:30px 34px; border-radius:19px;
  background:linear-gradient(112deg,#172a55 0%,#171b48 57%,#102b48 100%);
  border:1px solid rgba(76,119,236,.32);
  box-shadow:0 18px 50px rgba(0,0,0,.22);
}
.zayan-hero:after {
  width:320px; height:320px; right:-95px; top:-185px;
  background:rgba(54,117,235,.19);
}
.hero-kicker {
  color:#7ea8ff; font-size:.68rem; font-weight:800;
  letter-spacing:.17em; margin-bottom:9px;
}
.zayan-brand { font-size:2rem; }
.zayan-subtitle { max-width:780px; line-height:1.65; }
.section-heading {
  color:#eef2ff; font-size:1.15rem; font-weight:750;
  margin:25px 0 13px; letter-spacing:-.025em;
}
.section-heading span {
  color:#7182a8; font-size:.75rem; font-weight:400;
  margin-left:10px; letter-spacing:0;
}
.feature-card {
  min-height:158px; position:relative; padding:17px 17px 16px;
  border-radius:15px; border:1px solid rgba(84,119,220,.27);
  background:linear-gradient(145deg,rgba(24,35,75,.98),rgba(15,24,53,.98));
  box-shadow:0 10px 28px rgba(0,0,0,.13);
}
.feature-icon {
  display:flex; align-items:center; justify-content:center; width:36px; height:36px;
  border-radius:11px; color:#c7d5ff; font-size:19px;
  background:rgba(72,113,240,.18); border:1px solid rgba(111,145,255,.23);
}
.feature-tag {
  position:absolute; right:14px; top:20px; color:#7189c5;
  font-size:.57rem; font-weight:800; letter-spacing:.12em;
}
.feature-title { color:#f1f4ff; font-weight:700; margin-top:15px; font-size:.95rem; }
.feature-desc { color:#91a1c4; font-size:.75rem; line-height:1.5; margin-top:5px; }

.tools-heading { margin-top:30px; }

/* Original cinematic holographic command-center home */
.command-shell {
  position:relative; overflow:hidden; padding:28px; margin:4px 0 22px;
  border:1px solid rgba(63,190,255,.25); border-radius:24px;
  background:
    radial-gradient(circle at 50% 48%, rgba(0,183,255,.13), transparent 25%),
    linear-gradient(125deg, rgba(10,22,48,.98), rgba(8,15,34,.98) 60%, rgba(8,35,55,.96));
  box-shadow:0 22px 65px rgba(0,0,0,.34), inset 0 0 45px rgba(28,137,255,.05);
}
.command-shell:before {
  content:""; position:absolute; inset:0; pointer-events:none; opacity:.16;
  background-image:linear-gradient(rgba(83,164,255,.18) 1px, transparent 1px),
                   linear-gradient(90deg, rgba(83,164,255,.18) 1px, transparent 1px);
  background-size:34px 34px;
  mask-image:linear-gradient(to bottom, black, transparent 88%);
}
.command-topline {
  position:relative; display:flex; justify-content:space-between; align-items:center;
  gap:12px; color:#86b9df; font-size:.68rem; font-weight:800; letter-spacing:.19em;
}
.command-topline .online {
  color:#5df2c2; border:1px solid rgba(93,242,194,.3); background:rgba(20,180,140,.08);
  border-radius:99px; padding:7px 12px; letter-spacing:.1em;
}
.command-grid {
  position:relative; display:grid; grid-template-columns:1fr 1.05fr 1fr;
  align-items:center; gap:18px; min-height:330px; padding:20px 0 12px;
}
.command-side {
  border:1px solid rgba(72,160,235,.22); border-radius:15px; padding:17px;
  background:linear-gradient(145deg,rgba(14,35,69,.78),rgba(8,20,43,.72));
}
.command-label { color:#5fa9e9; font-size:.63rem; font-weight:800; letter-spacing:.16em; }
.command-value { color:#effaff; font-size:1.05rem; font-weight:700; margin-top:9px; }
.command-note { color:#8ca8c7; font-size:.73rem; line-height:1.55; margin-top:5px; }
.core-stage { display:flex; align-items:center; justify-content:center; min-height:285px; position:relative; }
.ai-core {
  width:210px; height:210px; border-radius:50%; position:relative; display:flex;
  align-items:center; justify-content:center; isolation:isolate;
  background:radial-gradient(circle,rgba(38,203,255,.22) 0 13%,rgba(23,103,205,.15) 31%,rgba(8,23,52,.1) 58%,transparent 70%);
  filter:drop-shadow(0 0 22px rgba(38,190,255,.32));
}
.ai-core:before,.ai-core:after {
  content:""; position:absolute; inset:8px; border-radius:50%;
  border:1px solid rgba(77,211,255,.78); box-shadow:0 0 18px rgba(40,178,255,.22), inset 0 0 20px rgba(40,178,255,.12);
  animation:core-spin 13s linear infinite;
}
.ai-core:after {
  inset:25px; border:2px dashed rgba(96,144,255,.75);
  animation:core-spin 18s linear infinite reverse;
}
.core-inner {
  width:108px; height:108px; border-radius:50%; display:flex; flex-direction:column;
  justify-content:center; align-items:center; z-index:2; color:#e8fbff;
  background:radial-gradient(circle at 35% 25%,#54e8ff,#1472c7 48%,#101f56 78%);
  border:2px solid rgba(158,238,255,.8);
  box-shadow:0 0 24px rgba(39,194,255,.8),0 0 65px rgba(30,121,255,.35),inset 0 0 20px rgba(255,255,255,.2);
  animation:core-pulse 2.8s ease-in-out infinite;
}
.core-inner b { font-size:1.55rem; letter-spacing:.08em; }
.core-inner small { font-size:.48rem; letter-spacing:.18em; margin-top:3px; }
.core-orbit {
  position:absolute; width:245px; height:85px; border:1px solid rgba(59,196,255,.55);
  border-radius:50%; transform:rotate(-28deg); box-shadow:0 0 13px rgba(36,172,255,.15);
}
.core-orbit.two { transform:rotate(62deg); width:235px; height:75px; border-color:rgba(105,130,255,.55); }
.core-caption { position:absolute; bottom:1px; color:#7bbce7; font-size:.62rem; letter-spacing:.2em; font-weight:800; }
@keyframes core-spin { to { transform:rotate(360deg); } }
@keyframes core-pulse { 0%,100% { transform:scale(.96); } 50% { transform:scale(1.045); } }
.hud-section-title { color:#edf7ff; font-weight:800; font-size:1rem; margin:22px 0 12px; }
.hud-card {
  min-height:135px; padding:17px; border-radius:16px; position:relative; overflow:hidden;
  border:1px solid rgba(65,157,230,.25);
  background:linear-gradient(145deg,rgba(17,37,72,.9),rgba(10,22,47,.94));
}
.hud-card:after {
  content:""; position:absolute; width:110px; height:110px; right:-55px; bottom:-65px;
  border-radius:50%; background:rgba(37,179,255,.13); filter:blur(4px);
}
.hud-card .icon { color:#66dfff; font-size:1.35rem; }
.hud-card .name { color:#f1f7ff; font-weight:750; margin-top:10px; }
.hud-card .desc { color:#8da8c8; font-size:.72rem; line-height:1.5; margin-top:4px; }
.signal-row {
  display:flex; align-items:center; justify-content:space-between; gap:12px;
  border-bottom:1px solid rgba(100,160,220,.12); padding:9px 0;
  color:#a9c0dc; font-size:.77rem;
}
.signal-row:last-child { border-bottom:0; }
.signal-dot { display:inline-block; width:7px; height:7px; border-radius:50%; background:#42e5b5; margin-right:8px; box-shadow:0 0 9px #42e5b5; }
.hud-footer { text-align:center; color:#526f94; font-size:.65rem; letter-spacing:.13em; padding:18px 0 2px; }
@media (max-width: 850px) {
  .command-grid { grid-template-columns:1fr; }
  .core-stage { min-height:250px; order:-1; }
  .command-shell { padding:18px; }
}

div[data-testid="stTabs"] button[role="tab"] {
  background:rgba(18,29,65,.8); border-radius:10px 10px 0 0;
  border-color:rgba(83,116,212,.2); color:#9eafd4;
}
div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
  background:linear-gradient(110deg,rgba(56,105,232,.27),rgba(105,91,232,.18));
  border-color:rgba(91,132,255,.5); color:#fff;
}
/* Real clickable sidebar radio navigation */
[data-testid="stSidebar"] [data-testid="stRadio"] > label { display:none; }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] { gap:7px; }
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label {
  padding:10px 12px; border-radius:10px; border:1px solid transparent;
  color:#9eaccd; background:transparent; transition:all .15s ease;
}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:hover {
  background:rgba(69,112,238,.12); border-color:rgba(91,132,255,.25); color:#fff;
}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
  background:linear-gradient(100deg,rgba(69,112,238,.22),rgba(116,103,255,.12));
  border-color:rgba(91,132,255,.42); color:#fff;
}
[data-testid="stSidebar"] [data-testid="stRadio"] div[role="radiogroup"] label > div:first-child {
  display:none;
}
@media (max-width: 900px) {
  .feature-card { min-height:175px; }
  .section-heading span { display:block; margin:4px 0 0; }
}

</style>
""", unsafe_allow_html=True)


# Deny access until an app password is configured and verified.
app_password = st.secrets.get("APP_PASSWORD", "")
if not app_password:
    st.error("App login is not configured. Set APP_PASSWORD in Streamlit Secrets.")
    st.stop()

if not st.session_state.get("authenticated", False):
    st.markdown("""
    <div class="zayan-hero">
      <div class="zayan-brand">🤖 Zayan AI</div>
      <div class="zayan-subtitle">Your private workspace for AI assistance and affiliate business reporting.</div>
      <span class="zayan-chip">SECURE LOGIN</span><span class="zayan-chip">BUSINESS ASSISTANT</span>
    </div>
    """, unsafe_allow_html=True)
    st.subheader("🔐 Welcome back")
    st.caption("Enter your dashboard password to continue.")
    entered_password = st.text_input("Password", type="password")
    if st.button("Log in"):
        if hmac.compare_digest(entered_password, str(app_password)):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Incorrect password")
    st.stop()

def navigate_to(page):
    # Callbacks run before widgets are instantiated on the next rerun,
    # so updating the radio key here is safe in Streamlit.
    st.session_state.active_page = page
    st.session_state.sidebar_navigation = page


def submit_home_prompt():
    prompt = st.session_state.get("home_quick_prompt", "").strip()
    if prompt:
        st.session_state.pending_prompt = prompt
        navigate_to("AI Assistant")


# Functional sidebar navigation.
with st.sidebar:
    st.markdown("""
    <div class="side-brand">
      <div class="side-logo">✦</div>
      <div><div class="side-title">Zayan AI</div><div class="side-caption">BUSINESS WORKSPACE</div></div>
    </div>
    <div class="side-section-label">WORKSPACE NAVIGATION</div>
    """, unsafe_allow_html=True)
    nav_options = ["Overview", "AI Assistant", "Voice Assistant", "Business Reports", "Payments", "Settings"]
    current_page = st.session_state.get("active_page", "Overview")
    if current_page not in nav_options:
        current_page = "Overview"
    active_page = st.radio(
        "Navigate",
        nav_options,
        index=nav_options.index(current_page),
        label_visibility="collapsed",
        key="sidebar_navigation",
        format_func=lambda item: {
            "Overview": "▦  Overview",
            "AI Assistant": "✧  AI Assistant",
            "Voice Assistant": "◉  Voice Assistant",
            "Business Reports": "▤  Business Reports",
            "Payments": "▣  Payments",
            "Settings": "⚙  Settings",
        }[item],
    )
    st.session_state.active_page = active_page
    st.markdown('<div class="side-divider"></div>', unsafe_allow_html=True)
    st.caption("Private workspace · Secure session")
active_page = st.session_state.get("active_page", "Overview")

if active_page == "Overview":
    st.markdown("""
    <div class="command-shell">
      <div class="command-topline">
        <span>ZAYAN AI &nbsp; / &nbsp; PERSONAL COMMAND CENTER</span>
        <span class="online">● SYSTEM ONLINE</span>
      </div>
      <div class="command-grid">
        <div class="command-side">
          <div class="command-label">IDENTITY</div>
          <div class="command-value">ZAYAN AI</div>
          <div class="command-note">Your personal business intelligence assistant. Ready to help with planning, reporting and decisions.</div>
          <div style="height:17px"></div>
          <div class="command-label">INTERFACE MODE</div>
          <div class="command-value">Holographic Workspace</div>
          <div class="command-note">Bengali + English interaction</div>
        </div>
        <div class="core-stage">
          <div class="core-orbit"></div><div class="core-orbit two"></div>
          <div class="ai-core"><div class="core-inner"><b>ZA</b><small>AI CORE</small></div></div>
          <div class="core-caption">VOICE • THINK • ASSIST</div>
        </div>
        <div class="command-side">
          <div class="command-label">SYSTEM STATUS</div>
          <div class="signal-row"><span><i class="signal-dot"></i>Workspace</span><b>Active</b></div>
          <div class="signal-row"><span><i class="signal-dot"></i>Navigation</span><b>Ready</b></div>
          <div class="signal-row"><span><i class="signal-dot"></i>Reports module</span><b>Available</b></div>
          <div class="signal-row"><span><i class="signal-dot"></i>Voice module</span><b>Available</b></div>
          <div class="command-note" style="margin-top:12px">AI responses and voice features require a valid API connection.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="hud-section-title">COMMAND DECK &nbsp; <span style="color:#6f8db4;font-size:.72rem;font-weight:400">Select a module to launch</span></div>', unsafe_allow_html=True)
    launch_cols = st.columns(4, gap="medium")
    launch_items = [
        ("✦", "AI Assistant", "Ask questions, plan campaigns and get business support.", "OPEN CHAT"),
        ("◉", "Voice Assistant", "Talk naturally in Bengali or English.", "VOICE LINK"),
        ("▤", "Business Reports", "Analyze affiliate reports, leads and Sub IDs.", "ANALYTICS"),
        ("▣", "Payments", "Review payment sheets and compare reports.", "FINANCE"),
    ]
    for col, (symbol, title, desc, tag) in zip(launch_cols, launch_items):
        with col:
            st.markdown(f"""
            <div class="hud-card">
              <div class="feature-tag">{tag}</div>
              <div class="icon">{symbol}</div>
              <div class="name">{title}</div>
              <div class="desc">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            st.button(
                f"Launch {title}",
                key=f"launch_{title}",
                use_container_width=True,
                on_click=navigate_to,
                args=(title,),
            )

    st.markdown('<div class="hud-section-title">QUICK COMMAND &nbsp; <span style="color:#6f8db4;font-size:.72rem;font-weight:400">Send a request directly to Zayan AI</span></div>', unsafe_allow_html=True)
    st.chat_input(
        "E.g. Analyze my affiliate performance this week...",
        key="home_quick_prompt",
        on_submit=submit_home_prompt,
    )

    st.markdown("""
    <div class="command-side" style="margin-top:20px">
      <div class="command-label">MISSION CONTROL</div>
      <div class="command-value">One workspace. Your business in focus.</div>
      <div class="command-note">Use the command deck or left navigation to open each tool. Your existing chat, reporting and payment modules remain available.</div>
    </div>
    <div class="hud-footer">ZAYAN AI &nbsp; • &nbsp; PERSONAL BUSINESS WORKSPACE &nbsp; • &nbsp; SECURE SESSION</div>
    """, unsafe_allow_html=True)

# Keep a compact top strip on all internal pages except the cinematic home.
else:
    top_left, top_right = st.columns([5, 1])
    with top_left:
        st.markdown('<div class="top-workspace">ZAYAN AI <span> / </span> Personal Business Workspace</div>', unsafe_allow_html=True)
    with top_right:
        st.markdown('<div class="live-pill">● &nbsp; WORKSPACE</div>', unsafe_allow_html=True)

# Read the API key from Streamlit Cloud Secrets first, then local environment.
try:
    openai_api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))
except Exception:
    openai_api_key = os.getenv("OPENAI_API_KEY", "")

client = OpenAI(api_key=openai_api_key) if OpenAI and openai_api_key else None

if "messages" not in st.session_state:
    st.session_state.messages = []
if "processed_audio" not in st.session_state:
    st.session_state.processed_audio = None
if "team_report_text" not in st.session_state:
    st.session_state.team_report_text = ""
if "team_report_rows" not in st.session_state:
    st.session_state.team_report_rows = None


def normalized_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value).lower())


def clean_subid(value):
    if pd.isna(value):
        return ""
    return str(value).strip().strip("'\"").strip().casefold()


def clean_number_value(value):
    text = str(value).strip().replace(",", "").replace("$", "").replace("USD", "")
    if text.startswith("(") and text.endswith(")"):
        text = "-" + text[1:-1]
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(match.group(0)) if match else 0.0


def clean_number(series):
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("$", "", regex=False)
        .str.replace("%", "", regex=False)
        .str.replace(r"^\((.*)\)$", r"-\1", regex=True),
        errors="coerce",
    ).fillna(0)


def find_col(columns, aliases):
    for column in columns:
        if normalized_name(column) in aliases:
            return column
    return None


def read_report(upload):
    upload.seek(0)
    if upload.name.lower().endswith(".csv"):
        try:
            frame = pd.read_csv(upload, dtype=str, encoding="utf-8-sig")
        except UnicodeDecodeError:
            upload.seek(0)
            frame = pd.read_csv(upload, dtype=str, encoding="cp1252")
    else:
        frame = pd.read_excel(upload, dtype=str)
    frame.columns = frame.columns.astype(str).str.strip()
    return frame


METRICS = {
    "Clicks": {"click", "clicks"},
    "Leads": {"lead", "leads", "conversion", "conversions"},
    "Sales": {"sale", "sales", "order", "orders"},
    "Earnings": {"earning", "earnings", "revenue", "commission", "commissions", "payout", "dollar", "dollars"},
}


def ask_zayan(prompt):
    st.session_state.messages.append({"role": "user", "content": prompt})
    try:
        if client is None:
            raise ValueError("OPENAI_API_KEY not found in .env or OpenAI package is not installed.")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Zayan AI, a professional personal and affiliate marketing business assistant. "
                        "Understand Bengali and English. Reply in the user's language."
                    ),
                }
            ] + st.session_state.messages,
        )
        answer = response.choices[0].message.content or "No response."
    except Exception as exc:
        answer = f"AI error: {exc}"
    st.session_state.messages.append({"role": "assistant", "content": answer})


def extract_upload_text(upload):
    name = upload.name.lower()
    data = upload.getvalue()
    if name.endswith(".txt"):
        return data.decode("utf-8", errors="replace")
    if name.endswith(".pdf"):
        if fitz is None:
            raise RuntimeError("PDF support is missing. In PowerShell run: python -m pip install pymupdf")
        doc = fitz.open(stream=data, filetype="pdf")
        text = "\n".join(page.get_text("text") for page in doc).strip()
        if text:
            return text
        # Scanned/image-only PDF: OCR through OpenAI vision is needed.
        if client is None:
            raise RuntimeError("This PDF appears to be scanned. Add OPENAI_API_KEY to .env to extract text from scanned PDFs, or upload a screenshot.")
        return extract_image_with_openai(data, "application/pdf")
    if name.endswith((".png", ".jpg", ".jpeg", ".webp")):
        if client is None:
            raise RuntimeError("Screenshot OCR needs OPENAI_API_KEY in .env.")
        mime = "image/png" if name.endswith(".png") else ("image/webp" if name.endswith(".webp") else "image/jpeg")
        return extract_image_with_openai(data, mime)
    return data.decode("utf-8", errors="replace")


def extract_image_with_openai(data, mime):
    import base64
    encoded = base64.b64encode(data).decode("ascii")
    if mime == "application/pdf":
        raise RuntimeError("This PDF is image-only. Please upload a screenshot of the report page, or use a text-based PDF.")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "Read the report image exactly. Return plain text rows only, preserving each Sub ID, lead count, "
                    "and dollar amount. Do not invent unreadable values; mark them [UNCLEAR]."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the report rows and totals from this screenshot."},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{encoded}"}},
                ],
            },
        ],
    )
    return response.choices[0].message.content or ""


def parse_team_text(text):
    rows = []
    errors = []
    # Expected examples: SubID = 2 = 90; SubID 2 90; SubID | 2 | $90
    for line_no, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or set(line) <= {"=", "-", "_", " "}:
            continue
        if re.search(r"\b(all\s*dollar|total|grand total)\b", line, re.I):
            continue
        # Split on equals, pipe, tabs, or 2+ spaces; also support "SubID, 2, 90"
        parts = [p.strip().strip("'\"") for p in re.split(r"\s*=\s*|\s*\|\s*|\t+|,\s*", line) if p.strip()]
        if len(parts) < 3:
            parts = re.split(r"\s{2,}", line)
        if len(parts) >= 3:
            subid = parts[0].strip().strip("'\"")
            lead_candidates = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", parts[1])
            dollar_candidates = re.findall(r"-?\$?\s*\d[\d,]*(?:\.\d+)?", " ".join(parts[2:]))
            if subid and lead_candidates and dollar_candidates:
                rows.append({
                    "Sub ID": subid,
                    "Team Leads": clean_number_value(lead_candidates[0]),
                    "Team Earnings": clean_number_value(dollar_candidates[-1]),
                    "Source Line": line_no,
                })
                continue
        # Avoid flagging headings, totals, and common labels as malformed rows.
        if re.search(r"\d", line) and not re.search(r"\b(total|dollar|lead|sub\s*id|report)\b", line, re.I):
            errors.append(f"Line {line_no}: {line}")
    return pd.DataFrame(rows), errors


def find_subid_column(columns):
    exact = {"subid", "subid1", "subid2", "subid3", "subid4", "subid5", "subid6", "subid7", "subid8", "subid9", "subid10"}
    for col in columns:
        n = normalized_name(col)
        if n in exact or n.startswith("subid") or n in {"affiliateid", "trackingid", "partnerid"}:
            return col
    return None


def normalize_maxbounty(upload):
    df = read_report(upload)
    sub_col = find_subid_column(df.columns)
    if sub_col is None:
        raise ValueError("Could not find a Sub ID column in this CSV. Please check the CSV header.")
    out = pd.DataFrame()
    out["Sub ID"] = df[sub_col].apply(clean_subid)
    out = out[out["Sub ID"] != ""].copy()
    for label, aliases in METRICS.items():
        col = find_col(df.columns, aliases)
        out[label] = clean_number(df[col]) if col is not None else 0.0
    # Combine repeated rows for the same Sub ID.
    agg = {metric: "sum" for metric in METRICS}
    return out.groupby("Sub ID", as_index=False).agg(agg)



def read_business_pdf(upload):
    """Parse text PDF tables; image-only pages use vision if API key is configured."""
    import io
    if fitz is None:
        raise RuntimeError("Install PDF support: python -m pip install pymupdf")
    doc = fitz.open(stream=upload.getvalue(), filetype="pdf")
    rows = []
    for page in doc:
        lines = page.get_text("text", sort=True).splitlines()
        # PDF exports sometimes split every cell onto a separate line.
        text = "\n".join(lines)
        if len(text.strip()) < 80:
            if client is None:
                raise RuntimeError("Scanned PDF: add OPENAI_API_KEY to .env for image-based reports.")
            import base64
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            b64 = base64.b64encode(pix.tobytes("png")).decode()
            response = client.chat.completions.create(
                model="gpt-4o-mini", temperature=0,
                messages=[{"role":"user","content":[
                    {"type":"text","text":"Transcribe ONLY report table data rows as TSV: Sub ID<TAB>Clicks<TAB>Leads/Conversions<TAB>Earnings. Use blank for absent fields. No headers, totals, prose or markdown."},
                    {"type":"image_url","image_url":{"url":"data:image/png;base64,"+b64}}
                ]}])
            text = response.choices[0].message.content or ""
            lines = text.splitlines()
        # First try table layout from PDF (including CheckPeopleOnline)
        for line in lines:
            line=line.strip()
            if not line or re.search(r'^(sub\s*id|total|offer:|date:|exported|page\s)',line,re.I):
                continue
            parts=re.split(r'\t+|\s{2,}',line)
            if len(parts)<3:
                # TransUnion: SD_TU_santo20 8 360$ ; MaxBounty: IQ_748 16 2 12.50 0.00 86.00 5.38
                parts=line.split()
            if len(parts)<3: continue
            sid=parts[0].strip()
            if not re.search(r'[A-Za-z]',sid) or sid.lower() in ('sub','totals','total'): continue
            nums=[x for x in parts[1:] if re.fullmatch(r'\$?-?[\d,]+(?:\.\d+)?\$?',x)]
            if len(nums)<2: continue
            def n(x): return float(x.strip('$').replace(',',''))
            if len(nums)>=6: # MaxBounty columns: clicks, leads, CR, sales, earnings, EPC
                clicks,leads,earnings=n(nums[0]),n(nums[1]),n(nums[4])
            elif len(nums)>=3 and any('converted' in x.lower() for x in parts):
                clicks,leads,earnings=n(nums[0]),n(nums[1]),n(nums[2])
            elif len(nums)==3: # image OCR: clicks, leads, earnings
                clicks,leads,earnings=map(n,nums)
            else: # TransUnion: leads, earnings
                clicks,leads,earnings=None,n(nums[0]),n(nums[-1])
            rows.append({"Sub ID":sid,"Clicks":clicks,"Leads":leads,"Sales":None,"Earnings":earnings})
    if not rows:
        raise ValueError("No report rows recognized. Please use a clearer PDF or CSV export.")
    return pd.DataFrame(rows)

active_page = st.session_state.get("active_page", "Overview")

if active_page == "Overview":
    pass

elif active_page == "AI Assistant":
    st.subheader("Chat with Zayan AI")
    st.caption("Type your message or use the microphone to speak in Bengali or English.")

    pending_prompt = st.session_state.pop("pending_prompt", None)
    if pending_prompt:
        ask_zayan(pending_prompt)
        st.rerun()

    # Voice input directly inside the main AI chat page.
    mic_col, send_col = st.columns([4, 1], vertical_alignment="bottom")
    with mic_col:
        chat_audio = st.audio_input("🎙️ Speak to Zayan AI", key="chat_voice_input")
    with send_col:
        send_voice = st.button("Send voice", type="primary", use_container_width=True, key="send_chat_voice")

    if send_voice:
        if chat_audio is None:
            st.warning("Please record a voice message first.")
        elif client is None:
            st.error("OPENAI_API_KEY is missing. Add it to Streamlit Secrets.")
        else:
            temp_path = None
            try:
                audio_bytes = chat_audio.getvalue()
                if audio_bytes == st.session_state.get("chat_voice_processed_audio"):
                    st.info("This voice message was already sent.")
                else:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                        temp_file.write(audio_bytes)
                        temp_path = temp_file.name
                    with open(temp_path, "rb") as audio_file:
                        transcription = client.audio.transcriptions.create(
                            model="whisper-1",
                            file=audio_file,
                        )
                    spoken_text = (transcription.text or "").strip()
                    if not spoken_text:
                        st.warning("I couldn't hear clear speech. Please try recording again.")
                    else:
                        st.session_state.chat_voice_processed_audio = audio_bytes
                        st.markdown("**You said:** " + spoken_text)
                        ask_zayan(spoken_text)
                        st.rerun()
            except Exception as exc:
                st.error(f"Voice input error: {exc}")
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

    prompt = st.chat_input("Or type a message to Zayan AI...")
    if prompt:
        ask_zayan(prompt)
        st.rerun()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

elif active_page == "Voice Assistant":
    st.subheader("🎤 Talk to Zayan AI")
    st.caption("Voice transcription requires OPENAI_API_KEY in your .env file.")
    audio = st.audio_input("Speak in Bengali or English")
    if audio is not None and st.button("Send Voice Message"):
        if client is None:
            st.error("OPENAI_API_KEY not found in .env or OpenAI package is not installed.")
        else:
            temp_path = None
            try:
                audio_bytes = audio.getvalue()
                if audio_bytes != st.session_state.processed_audio:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                        temp_file.write(audio_bytes)
                        temp_path = temp_file.name
                    with open(temp_path, "rb") as audio_file:
                        transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
                    st.session_state.processed_audio = audio_bytes
                    st.write("You said:", transcription.text)
                    ask_zayan(transcription.text)
            except Exception as exc:
                st.error(f"Voice error: {exc}")
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        st.success(st.session_state.messages[-1]["content"])

elif active_page == "Business Reports":
    st.subheader("📊 Affiliate Business Analytics")
    upload_col, search_col = st.columns(2, gap="large")
    with upload_col:
        uploaded_file = st.file_uploader("Upload CSV, Excel or PDF report", type=["csv","xlsx","pdf"], key="business_csv")
    with search_col:
        search_text = st.text_area("🔎 Search Sub IDs (one per line or comma-separated)", height=145,
                                   placeholder="SD_TU_santo\\nonline\\nIQ_748")
        st.caption("Match Sub IDs — automatically matches the entered text anywhere in a Sub ID (case-insensitive).")
        search_clicked = st.button("🔍 Search & Calculate", type="primary")
    if uploaded_file is None:
        st.info("Upload a CSV, Excel or PDF report.")
    else:
        try:
            is_pdf = uploaded_file.name.lower().endswith(".pdf")
            df = read_business_pdf(uploaded_file) if is_pdf else read_report(uploaded_file)
            subid_col = find_subid_column(df.columns)
            if subid_col is None:
                st.error("Sub ID column not found.")
            else:
                report_df = df.copy()
                report_df["_sid"] = report_df[subid_col].apply(clean_subid)
                report_df = report_df[~report_df["_sid"].isin(["total","totals",""])].copy()
                for label, aliases in METRICS.items():
                    source = find_col(report_df.columns, aliases)
                    report_df[label] = clean_number(report_df[source]) if source is not None else float("nan")
                st.success(f"Report loaded: {len(report_df)} rows")
                if is_pdf:
                    st.caption("PDF extraction is best-effort. Check the extracted rows against the original before using totals for payments.")
                    with st.expander("Review extracted PDF rows"):
                        st.dataframe(report_df.drop(columns=["_sid"]),use_container_width=True)
                if search_clicked:
                    requested = list(dict.fromkeys(clean_subid(x) for x in re.split(r"[,;\n]+", search_text) if x.strip()))
                    if not requested: st.warning("Enter at least one Sub ID.")
                    else:
                        def matched(sid):
                            return any(q in sid for q in requested)
                        selected=report_df[report_df["_sid"].apply(matched)].copy()
                        # Only report Sub IDs with positive conversions/leads.
                        # Do not use Sales dollar amounts as conversion counts.
                        selected=selected[pd.to_numeric(selected["Leads"], errors="coerce").fillna(0) > 0].copy()
                        if selected.empty: st.warning("No matching Sub IDs with positive conversions/leads found.")
                        else:
                            selected["Sub ID"]=selected["_sid"]
                            selected=selected.groupby("Sub ID",as_index=False)[list(METRICS)].sum(min_count=1)
                            selected=selected[selected["Leads"] > 0].copy()
                            # In this report Leads are conversions; Sales is a separate, zero-valued field.
                            selected=selected.rename(columns={"Leads": "Conversions"})
                            display_columns=["Sub ID","Clicks","Conversions","Earnings"]
                            selected=selected[display_columns]
                            st.markdown("### 🔎 Selected Sub ID Results")
                            st.dataframe(selected,use_container_width=True,hide_index=True)
                            st.markdown("### Combined Totals")
                            cols=st.columns(3)
                            for col,label in zip(cols,["Clicks","Conversions","Earnings"]):
                                value=selected[label].sum(min_count=1)
                                col.metric(label, "Not in report" if pd.isna(value) else
                                           f"${value:,.2f}" if label=="Earnings" else f"{value:,.0f}")
                            st.download_button("Download selected report CSV",selected.to_csv(index=False).encode("utf-8-sig"),
                                               "zayan_subid_results.csv","text/csv")
                            # Excel is optional: a missing openpyxl package must not break search or CSV download.
                            try:
                                import openpyxl
                                excel_buffer = BytesIO()
                                selected.to_excel(excel_buffer, index=False, engine="openpyxl")
                                st.download_button("Download selected report Excel", excel_buffer.getvalue(),
                                                   "zayan_subid_results.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                            except ImportError:
                                st.info("Excel download requires openpyxl. Install it with: pip install openpyxl. CSV download works without it.")
        except Exception as exc:
            st.error(f"Could not read report: {exc}")

elif active_page == "Payments":
    st.subheader("💰 Payments Verification")
    st.write("Compare a team report (text, screenshot, or PDF) with a MaxBounty CSV. The report period must match the CSV period.")
    mode = st.radio("Team report input method", ["Copy & Paste Text", "Screenshot Upload", "PDF Upload"], horizontal=True, key="payment_mode")

    team_text = ""
    if mode == "Copy & Paste Text":
        team_text = st.text_area(
            "Paste the team's WhatsApp report",
            height=220,
            placeholder="Example:\n=ARY=BR_01 = 2 = 90\n=ARY=Jacks1 = 2 = 48.75\nAll dollar : 138.75",
            key="team_text_input",
        )
    elif mode == "Screenshot Upload":
        screenshot = st.file_uploader("Upload screenshot (PNG/JPG/WEBP)", type=["png", "jpg", "jpeg", "webp"], key="team_screenshot")
        if screenshot is not None and st.button("Extract Report Text", key="extract_image"):
            try:
                team_text = extract_upload_text(screenshot)
                st.session_state.team_report_text = team_text
                st.success("Report text extracted. Review it below before verifying.")
            except Exception as exc:
                st.error(f"Could not extract screenshot text: {exc}")
    else:
        pdf = st.file_uploader("Upload team report PDF", type=["pdf"], key="team_pdf")
        if pdf is not None and st.button("Extract Report Text", key="extract_pdf"):
            try:
                team_text = extract_upload_text(pdf)
                st.session_state.team_report_text = team_text
                st.success("Report text extracted. Review it below before verifying.")
            except Exception as exc:
                st.error(f"Could not extract PDF text: {exc}")

    if mode == "Copy & Paste Text":
        st.session_state.team_report_text = team_text

    if st.session_state.team_report_text:
        st.markdown("#### Extracted / pasted team report")
        edited_text = st.text_area("Review or correct report text before verification", value=st.session_state.team_report_text, height=220, key="team_report_review")
        st.session_state.team_report_text = edited_text
        rows, parse_errors = parse_team_text(edited_text)
        if parse_errors:
            st.warning("Some report lines could not be parsed. Correct these lines before verifying:")
            st.code("\n".join(parse_errors))
        if not rows.empty:
            st.caption(f"Recognized {len(rows)} Sub ID rows.")
            st.dataframe(rows[["Sub ID", "Team Leads", "Team Earnings"]], use_container_width=True, hide_index=True)
        st.session_state.team_report_rows = rows

    max_csv = st.file_uploader("Upload MaxBounty CSV", type=["csv", "xlsx"], key="payments_maxbounty_csv")
    if st.button("Verify Payments", type="primary"):
        if not st.session_state.team_report_text.strip():
            st.error("Provide the team report first: paste text or upload a screenshot/PDF and extract its text.")
        elif max_csv is None:
            st.error("Upload the MaxBounty CSV first.")
        else:
            try:
                team_rows, parse_errors = parse_team_text(st.session_state.team_report_text)
                if parse_errors:
                    st.error("Some report lines could not be parsed. Correct the lines shown above before verifying.")
                elif team_rows.empty:
                    st.error("No Sub ID rows were recognized. Check the report text format.")
                else:
                    max_rows = normalize_maxbounty(max_csv)
                    combined = team_rows.copy()
                    combined["Sub ID key"] = combined["Sub ID"].apply(clean_subid)
                    max_rows["Sub ID key"] = max_rows["Sub ID"].apply(clean_subid)
                    merged = combined.merge(max_rows, on="Sub ID key", how="outer", suffixes=("_Team", "_MaxBounty"), indicator=True)
                    merged["Sub ID"] = merged["Sub ID_Team"].fillna(merged["Sub ID_MaxBounty"])
                    merged["Team Leads"] = merged["Team Leads"].fillna(0)
                    merged["Team Earnings"] = merged["Team Earnings"].fillna(0)
                    merged["Leads"] = merged["Leads"].fillna(0)
                    merged["Earnings"] = merged["Earnings"].fillna(0)
                    merged["Lead Difference (Team - MaxBounty)"] = merged["Team Leads"] - merged["Leads"]
                    merged["Dollar Difference (Team - MaxBounty)"] = merged["Team Earnings"] - merged["Earnings"]
                    merged["Status"] = merged.apply(
                        lambda r: "Matched" if r["_merge"] == "both" and abs(r["Lead Difference (Team - MaxBounty)"]) < 1e-9 and abs(r["Dollar Difference (Team - MaxBounty)"]) < 0.011 else "Mismatch",
                        axis=1,
                    )
                    st.markdown("### Verification Results")
                    counts = st.columns(3)
                    counts[0].metric("Matched Sub IDs", int((merged["Status"] == "Matched").sum()))
                    counts[1].metric("Mismatched Sub IDs", int((merged["Status"] == "Mismatch").sum()))
                    counts[2].metric("Team Report Total", f"${team_rows['Team Earnings'].sum():,.2f}")
                    show_cols = [
                        "Sub ID", "Team Leads", "Leads", "Lead Difference (Team - MaxBounty)",
                        "Team Earnings", "Earnings", "Dollar Difference (Team - MaxBounty)", "Status"
                    ]
                    st.dataframe(merged[show_cols].sort_values(["Status", "Sub ID"]), use_container_width=True, hide_index=True)
                    st.markdown("### Combined Totals")
                    total_cols = st.columns(4)
                    total_cols[0].metric("Team Leads", f"{team_rows['Team Leads'].sum():,.0f}")
                    total_cols[1].metric("MaxBounty Leads", f"{max_rows['Leads'].sum():,.0f}")
                    total_cols[2].metric("Team Dollars", f"${team_rows['Team Earnings'].sum():,.2f}")
                    total_cols[3].metric("MaxBounty Earnings", f"${max_rows['Earnings'].sum():,.2f}")
                    st.caption("A mismatch may mean the reports cover different dates, a Sub ID is missing on one side, or the CSV uses a different column format.")
            except Exception as exc:
                st.error(f"Verification failed: {exc}")


    st.markdown("""
    <div class="zayan-footer">
      Zayan AI · Private Business Workspace · Built for smarter decisions
    </div>
    """, unsafe_allow_html=True)

elif active_page == "Settings":
    st.subheader("⚙️ Workspace Settings")
    st.write("Manage your Zayan AI workspace session.")
    if st.button("Log out", type="secondary"):
        st.session_state.authenticated = False
        st.session_state.active_page = "Overview"
        st.rerun()


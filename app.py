import os
import re
import hmac
import hashlib
import sqlite3
import tempfile
from datetime import datetime, date
from io import BytesIO

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    import fitz
except Exception:
    fitz = None

load_dotenv()

APP_TITLE = "ELINA AI — JARVIS Business OS"
DB_PATH = os.getenv("ZAYAN_DB_PATH", "zayan_ai_data.db")

st.set_page_config(page_title=APP_TITLE, page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

# ----------------------------- Theme -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Hind+Siliguri:wght@400;500;600;700&display=swap');
:root{--bg:#080e1d;--panel:#101b32;--panel2:#142443;--line:rgba(96,145,235,.22);--muted:#8fa4c7;--cyan:#47d7f2;--violet:#7768ff}
html,body,[class*="css"]{font-family:Inter,'Hind Siliguri',sans-serif}
.stApp{background:radial-gradient(ellipse at 12% 0%,rgba(103,88,255,.17),transparent 32%),radial-gradient(ellipse at 92% 12%,rgba(36,195,225,.12),transparent 28%),var(--bg);color:#edf4ff}
[data-testid="stHeader"]{background:rgba(8,14,29,.72)}
.block-container{max-width:1500px;padding-top:1.2rem;padding-bottom:3rem}
#MainMenu,footer{visibility:hidden}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#101936,#0b1328);border-right:1px solid var(--line)}
[data-testid="stSidebar"] .block-container{padding-top:1rem}
.brand{display:flex;align-items:center;gap:12px;padding:12px 8px 24px;border-bottom:1px solid var(--line);margin-bottom:20px}
.brand-icon{width:44px;height:44px;border-radius:14px;background:linear-gradient(135deg,#36c9e8,#7667ff);display:grid;place-items:center;font-size:24px;box-shadow:0 0 24px #387ce755}
.brand-name{font-weight:800;font-size:1.2rem;color:#fff}.brand-sub{font-size:.62rem;letter-spacing:.17em;color:#7992c3;margin-top:3px}
.eyebrow{font-size:.66rem;letter-spacing:.18em;color:#72a9ff;font-weight:800}
.hero{position:relative;overflow:hidden;padding:28px 32px;border:1px solid rgba(76,148,255,.32);border-radius:22px;background:linear-gradient(115deg,rgba(21,39,81,.97),rgba(12,29,53,.95) 60%,rgba(8,55,68,.88));box-shadow:0 18px 55px #0005;margin-bottom:22px}
.hero:after{content:"";position:absolute;right:-75px;top:-160px;width:310px;height:310px;border-radius:50%;background:#3b80ff33;filter:blur(8px)}
.hero h1{font-size:2rem;letter-spacing:-.04em;color:white;margin:.45rem 0}
.hero p{color:#c0d2ed;margin:0;max-width:800px}
.status{display:inline-block;border:1px solid #37dca755;background:#1a9b7020;color:#62e7b7;padding:6px 12px;border-radius:99px;font-size:.68rem;font-weight:800;letter-spacing:.12em}
.core{display:flex;justify-content:center;align-items:center;min-height:220px}
.core-ball{width:150px;height:150px;border-radius:50%;display:grid;place-items:center;text-align:center;background:radial-gradient(circle at 35% 25%,#78f0ff,#1678c8 48%,#111d53 78%);border:2px solid #a4f2ff;box-shadow:0 0 25px #27cfff,0 0 70px #1678c877;animation:pulse 3s ease-in-out infinite;color:white}
.core-ball b{font-size:2rem;letter-spacing:.1em}.core-ball small{display:block;font-size:.55rem;letter-spacing:.18em}
@keyframes pulse{50%{transform:scale(1.05);filter:brightness(1.15)}}
.panel{padding:17px 18px;border:1px solid var(--line);border-radius:16px;background:linear-gradient(145deg,rgba(20,36,68,.9),rgba(12,22,43,.95));height:100%}
.panel-title{font-weight:750;color:#f2f6ff;margin-bottom:6px}.muted{color:var(--muted);font-size:.82rem}
div[data-testid="stMetric"]{background:linear-gradient(145deg,#172849,#101a31);border:1px solid var(--line);border-radius:15px;padding:14px}
div[data-testid="stMetricLabel"]{color:#a7bad9}div[data-testid="stMetricValue"]{color:#fff;font-weight:800}
.stButton>button,.stDownloadButton>button{border:0;border-radius:10px;color:#fff;font-weight:700;background:linear-gradient(105deg,#7565f5,#397fe8);box-shadow:0 7px 20px #4f6ee833}
.stButton>button:hover,.stDownloadButton>button:hover{color:#fff;filter:brightness(1.12);border:0}
[data-testid="stChatMessage"]{background:#14213a;border:1px solid var(--line);border-radius:14px}
[data-testid="stChatInput"]{border:1px solid #7668ff77;border-radius:13px;background:#111c33}
[data-testid="stFileUploader"] section{border:1px dashed #7768ff88;border-radius:14px;background:#7768ff0b}
hr{border-color:var(--line)}
.smallcaps{font-size:.65rem;letter-spacing:.16em;color:#7594c7;font-weight:800}
[data-testid="stSidebar"] [data-testid="stRadio"] label{padding:8px 10px;border-radius:9px}
@media(max-width:800px){.hero{padding:22px}.hero h1{font-size:1.55rem}.core{min-height:170px}.core-ball{width:125px;height:125px}}
</style>
""", unsafe_allow_html=True)

# ----------------------------- Storage -----------------------------
def db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS memories(
            id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL,
            content TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS tasks(
            id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL,
            due_date TEXT, priority TEXT DEFAULT 'Normal',
            status TEXT DEFAULT 'Open', notes TEXT, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS team(
            id INTEGER PRIMARY KEY AUTOINCREMENT, member_name TEXT NOT NULL,
            whatsapp TEXT, group_name TEXT, active INTEGER DEFAULT 1,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT, member_name TEXT NOT NULL,
            period TEXT, amount REAL NOT NULL, currency TEXT DEFAULT 'USD',
            status TEXT DEFAULT 'Pending', reference TEXT, notes TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS chat_history(
            id INTEGER PRIMARY KEY AUTOINCREMENT, role TEXT NOT NULL,
            content TEXT NOT NULL, created_at TEXT NOT NULL
        );
        """)
init_db()

def query(sql, params=()):
    with db() as c:
        return c.execute(sql, params).fetchall()

def execute(sql, params=()):
    with db() as c:
        cur = c.execute(sql, params)
        c.commit()
        return cur.lastrowid

# ----------------------------- Configuration -----------------------------
def get_secret(name, default=""):
    try:
        return st.secrets.get(name, os.getenv(name, default))
    except Exception:
        return os.getenv(name, default)

APP_PASSWORD = str(get_secret("APP_PASSWORD", ""))
API_KEY = str(get_secret("OPENAI_API_KEY", ""))
client = OpenAI(api_key=API_KEY) if OpenAI and API_KEY else None

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "active_page" not in st.session_state:
    st.session_state.active_page = "Overview"
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "report_df" not in st.session_state:
    st.session_state.report_df = None
if "business_selected_df" not in st.session_state:
    st.session_state.business_selected_df = None
if "report_source_name" not in st.session_state:
    st.session_state.report_source_name = ""
if "report_source_hash" not in st.session_state:
    st.session_state.report_source_hash = ""
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None

# ----------------------------- Authentication -----------------------------
if not APP_PASSWORD:
    st.error("Login is not configured. Add APP_PASSWORD in Streamlit → Manage app → Settings → Secrets.")
    st.stop()

if not st.session_state.authenticated:
    st.markdown('<div class="hero"><div class="eyebrow">PRIVATE AI BUSINESS WORKSPACE</div><h1>🤖 ELINA AI — JARVIS</h1><p>Your personal command center for conversations, affiliate reporting, team operations and payments.</p></div>', unsafe_allow_html=True)
    a,b,c = st.columns([1,1.2,1])
    with b:
        with st.container(border=True):
            st.subheader("🔐 Secure Login")
            pw = st.text_input("Workspace password", type="password")
            if st.button("Unlock Workspace", use_container_width=True):
                if hmac.compare_digest(pw, APP_PASSWORD):
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
    st.stop()

# ----------------------------- Helpers -----------------------------
SYSTEM_PROMPT = """You are ELINA AI, a private personal JARVIS-style assistant and affiliate marketing business copilot.
Your owner's full name is Sabbir Alam. He is your Boss and the owner of this private workspace. Address him warmly and respectfully as Boss; use "Boss Sabbir" naturally, without forcing it into every sentence. Never confuse the owner's name with the AI's name: you are ELINA AI.
Understand Bengali and English. Reply in the language the user uses; default to natural Bangla when they use Bangla.
Be concise, practical and commercially aware. The Boss operates affiliate marketing campaigns, especially US credit-monitoring and identity-protection offers, uses Facebook Ads, manages a team, and needs help with affiliate reports, Sub IDs, payouts, payment reconciliation, tasks and professional English manager messages.
Never claim to have sent an email, transferred money, accessed an external affiliate account, or changed a live campaign unless a connected tool actually did so.
When analyzing uploaded report context, rely on the supplied data and clearly distinguish actual values from estimates.
"""

def ask_ai(prompt, speak=False):
    st.session_state.chat_messages.append({"role":"user","content":prompt})
    if client is None:
        answer = "OpenAI API সংযোগ পাওয়া যাচ্ছে না। Streamlit Secrets-এ OPENAI_API_KEY ঠিকভাবে যোগ করা আছে কি না দেখুন।"
    else:
        try:
            memory_rows = query("SELECT category,content FROM memories ORDER BY id DESC LIMIT 20")
            memory_text = "\n".join([f"- {r['category']}: {r['content']}" for r in memory_rows])
            report_context = ""
            if st.session_state.report_df is not None:
                df = st.session_state.report_df
                report_context = f"\nCurrent uploaded report summary: {len(df)} rows; columns={list(df.columns)}."
            history = [{"role":"system","content":SYSTEM_PROMPT + "\nSaved memory:\n" + memory_text + report_context}]
            history += [{"role":m["role"],"content":m["content"]} for m in st.session_state.chat_messages[-16:]]
            response = client.chat.completions.create(model="gpt-4o-mini", messages=history, temperature=0.5)
            answer = response.choices[0].message.content or "দুঃখিত, উত্তর তৈরি করা যায়নি।"
        except Exception as e:
            answer = f"AI connection error: {e}"
    st.session_state.chat_messages.append({"role":"assistant","content":answer})
    execute("INSERT INTO chat_history(role,content,created_at) VALUES(?,?,?)",("user",prompt,datetime.now().isoformat(timespec="seconds")))
    execute("INSERT INTO chat_history(role,content,created_at) VALUES(?,?,?)",("assistant",answer,datetime.now().isoformat(timespec="seconds")))
    if speak and client is not None:
        try:
            audio = client.audio.speech.create(model="gpt-4o-mini-tts", voice="alloy", input=answer)
            st.session_state.last_tts = audio.read()
        except Exception as e:
            st.session_state.tts_error = str(e)
    return answer

def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())

def clean_subid(v):
    if pd.isna(v): return ""
    return str(v).strip().strip("'\"").casefold()

def clean_num(series):
    """Parse numeric report values without changing their magnitude."""
    values = series.astype(str).str.strip()
    values = values.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
    values = values.str.replace(r"[\$,£€\s]", "", regex=True)
    values = values.str.replace(",", "", regex=False)
    values = values.str.replace("%", "", regex=False)
    values = values.replace({"": None, "nan": None, "None": None, "-": None})
    return pd.to_numeric(values, errors="coerce").fillna(0.0)


# Priority order matters when an export contains several similar columns.
METRIC_CANDIDATES = {
    "Clicks": ["clicks", "unique_clicks", "click"],
    "Leads": ["conversions", "conversion", "approved_conversions",
              "leads", "lead", "approved_leads"],
    "Sales": ["sales", "sale", "orders", "order"],
    "Earnings": ["total_earnings", "earnings", "commission",
                 "commissions", "revenue", "payout", "amount"],
}


def find_column(cols, aliases):
    by_normalized = {norm(col): col for col in cols}
    for alias in aliases:
        found = by_normalized.get(norm(alias))
        if found is not None:
            return found
    return None


def load_report(upload):
    name = upload.name.lower()
    upload.seek(0)
    if name.endswith(".csv"):
        try:
            df = pd.read_csv(upload, dtype=str, encoding="utf-8-sig")
        except UnicodeDecodeError:
            upload.seek(0)
            df = pd.read_csv(upload, dtype=str, encoding="cp1252")
    elif name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(upload, dtype=str)
    elif name.endswith(".pdf"):
        df = read_business_pdf(upload)
    else:
        raise ValueError("Use CSV, XLSX, XLS or PDF.")

    df.columns = df.columns.astype(str).str.strip()
    subcol = find_column(df.columns, ["sub_id", "subid", "tracking_sub_id"])
    if subcol is None:
        subcol = next((c for c in df.columns if norm(c).startswith("subid")), None)
    if subcol is None:
        raise ValueError("Sub ID column not found. Expected Sub ID, SubID or Sub ID 1.")

    metric_columns = {
        metric: find_column(df.columns, candidates)
        for metric, candidates in METRIC_CANDIDATES.items()
    }
    if metric_columns["Leads"] is None:
        raise ValueError(
            "Conversions/Leads column was not found. Please check that the uploaded export "
            "contains a Conversions, Conversion, Leads or Lead column."
        )
    if metric_columns["Earnings"] is None:
        raise ValueError(
            "Earnings column was not found. Please check that the uploaded export "
            "contains Earnings, Revenue, Commission or Payout."
        )

    out = pd.DataFrame()
    out["Sub ID"] = df[subcol].apply(clean_subid)
    out = out[out["Sub ID"].ne("") & ~out["Sub ID"].str.casefold().isin(["total", "totals"])].copy()

    for metric, source_col in metric_columns.items():
        if source_col is None:
            out[metric] = 0.0
        else:
            out[metric] = clean_num(df.loc[out.index, source_col])

    # Aggregate repeated rows for the same Sub ID once, after parsing each source row.
    out = out.groupby("Sub ID", as_index=False, sort=False)[
        ["Clicks", "Leads", "Sales", "Earnings"]
    ].sum()
    out.attrs["metric_columns"] = metric_columns
    return out


def read_business_pdf(upload):
    """Extract affiliate report rows from text PDFs; use vision OCR for scanned pages when available."""
    if fitz is None:
        raise ValueError("PDF support missing. Add pymupdf to requirements.")
    doc = fitz.open(stream=upload.getvalue(), filetype="pdf")
    rows = []

    def parse_line(line):
        raw = str(line).strip()
        if not raw or re.search(r"^(sub\s*id|total|grand total|offer:|date:|exported|page\s)", raw, re.I):
            return None
        parts = re.split(r"\t+|\s{2,}", raw)
        if len(parts) < 2:
            parts = raw.split()
        if len(parts) < 2:
            return None
        sid = parts[0].strip().strip("'\"")
        if not re.search(r"[A-Za-z]", sid) or norm(sid) in {"subid", "total", "totals"}:
            return None
        nums = re.findall(r"\(?-?\$?[\d,]+(?:\.\d+)?%?\)?", " ".join(parts[1:]))
        def number(value):
            value = value.strip().replace("$", "").replace(",", "").replace("%", "")
            if value.startswith("(") and value.endswith(")"):
                value = "-" + value[1:-1]
            try:
                return float(value)
            except ValueError:
                return None
        vals = [number(x) for x in nums]
        vals = [x for x in vals if x is not None]
        if len(vals) >= 6:  # MaxBounty: clicks, leads, CR, sales, earnings, EPC
            clicks, leads, earnings = vals[0], vals[1], vals[4]
        elif len(vals) == 3:  # clicks, leads, earnings
            clicks, leads, earnings = vals
        elif len(vals) == 2:  # leads, earnings (common advertiser export)
            clicks, leads, earnings = None, vals[0], vals[1]
        else:
            return None
        return {"Sub ID": sid, "Clicks": clicks, "Leads": leads, "Sales": None, "Earnings": earnings}

    for page in doc:
        page_rows = []
        for line in page.get_text("text", sort=True).splitlines():
            item = parse_line(line)
            if item:
                page_rows.append(item)
        # Rebuild table rows when PDF text extraction separates cells into coordinate-aligned words.
        if not page_rows:
            grouped = {}
            for word in page.get_text("words"):
                x0, y0, _x1, _y1, token = word[:5]
                grouped.setdefault(round(y0 / 3) * 3, []).append((x0, token))
            for y in sorted(grouped):
                item = parse_line(" ".join(token for _, token in sorted(grouped[y])))
                if item:
                    page_rows.append(item)
        # OCR scanned pages if OpenAI is configured.
        if not page_rows and client is not None:
            try:
                import base64
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                encoded = base64.b64encode(pix.tobytes("png")).decode("ascii")
                response = client.chat.completions.create(
                    model="gpt-4o-mini", temperature=0,
                    messages=[
                        {"role": "system", "content": "Extract affiliate report table rows exactly. Return TSV only with columns Sub ID, Clicks, Leads/Conversions, Earnings. Do not invent unreadable values."},
                        {"role": "user", "content": [
                            {"type": "text", "text": "Transcribe report rows from this PDF page."},
                            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + encoded}}
                        ]}
                    ]
                )
                for line in (response.choices[0].message.content or "").splitlines():
                    item = parse_line(line)
                    if item:
                        page_rows.append(item)
            except Exception:
                pass
        rows.extend(page_rows)
    if not rows:
        raise ValueError("PDF rows could not be extracted. For scanned PDFs configure OPENAI_API_KEY, or upload CSV/XLSX for the most reliable results.")
    return pd.DataFrame(rows)

def currency(v):
    return f"${v:,.2f}"

# ----------------------------- Sidebar -----------------------------
with st.sidebar:
    st.markdown('<div class="brand"><div class="brand-icon">✦</div><div><div class="brand-name">ELINA AI</div><div class="brand-sub">JARVIS BUSINESS OS</div></div></div>',unsafe_allow_html=True)
    st.markdown('<div class="smallcaps">COMMAND NAVIGATION</div>',unsafe_allow_html=True)
    pages=["Overview","AI Assistant","Voice Assistant","Business Reports","Payments","Team Management","Tasks","Memory","Email Assistant","Settings"]
    icons=["▦","✧","◉","▤","▣","♙","✓","◈","✉","⚙"]
    labels={p:f"{icons[i]}  {p}" for i,p in enumerate(pages)}
    selected=st.radio("Navigation",pages,index=pages.index(st.session_state.active_page),format_func=lambda p:labels[p],label_visibility="collapsed",key="nav_radio")
    st.session_state.active_page=selected
    st.divider()
    st.caption("PRIVATE WORKSPACE · SECURE SESSION")
    st.caption("Build: JARVIS Hybrid v1")

page=st.session_state.active_page

# ----------------------------- Overview -----------------------------
if page=="Overview":
    # Rotate the welcome line once per calendar day while always recognizing the owner.
    daily_welcomes = [
        "আজকে কী নিয়ে ভাবছেন? আমি কীভাবে সাহায্য করতে পারি?",
        "আপনার আজকের পরিকল্পনা কী, Boss? ELINA প্রস্তুত।",
        "নতুন দিন, নতুন পরিকল্পনা—বলুন Boss, কোথা থেকে শুরু করব?",
        "আপনার কাজগুলো গুছিয়ে দিতে আমি প্রস্তুত, Boss Sabbir।",
        "আজকের লক্ষ্য কী? চলুন একসাথে এগিয়ে যাই, Boss।",
        "আপনাকে আবার পেয়ে ভালো লাগছে, Boss! কী করতে পারি?",
        "আপনার পরবর্তী নির্দেশের অপেক্ষায় আছি, Boss Sabbir।",
    ]
    daily_welcome = daily_welcomes[date.today().toordinal() % len(daily_welcomes)]
    left,mid,right=st.columns([1.1,1,1.1],gap="large")
    with st.container():
        st.markdown(f'<div class="hero"><div class="eyebrow">ELINA AI / PERSONAL COMMAND CENTER</div><div style="display:flex;justify-content:space-between;align-items:center;gap:18px;flex-wrap:wrap"><div><h1>Welcome Boss Sabbir! 👋</h1><p>{daily_welcome}<br>Your personal AI assistant and business command center is ready.</p></div><span class="status">● SYSTEM ONLINE</span></div></div>',unsafe_allow_html=True)
    with left:
        st.markdown('<div class="panel"><div class="smallcaps">IDENTITY</div><div class="panel-title">ELINA AI</div><div class="muted">Personal JARVIS Business Copilot</div><br><div class="smallcaps">INTERFACE MODE</div><div class="panel-title">Hybrid Command Center</div><div class="muted">Bengali + English · Desktop + Mobile</div></div>',unsafe_allow_html=True)
    with mid:
        st.markdown('<div class="core"><div class="core-ball"><div><b>ZA</b><small>AI CORE · ONLINE</small></div></div></div>',unsafe_allow_html=True)
    with right:
        st.markdown('<div class="panel"><div class="smallcaps">SYSTEM STATUS</div><p>🟢 Workspace · Active</p><p>🟢 Navigation · Ready</p><p>🟢 Database · Connected</p><p>'+("🟢 OpenAI · Connected" if client else "🟠 OpenAI · API key missing")+'</p><p class="muted">Voice playback uses OpenAI TTS when enabled.</p></div>',unsafe_allow_html=True)
    st.subheader("Command Deck")
    cards=[("✧","AI Assistant","Ask questions and plan business activity."),("◉","Voice Assistant","Speak in Bangla or English; hear spoken replies."),("▤","Business Reports","Upload affiliate reports and search Sub IDs."),("▣","Payments","Reconcile team reports and track manual payments.")]
    cols=st.columns(4)
    for col,(ico,title,desc) in zip(cols,cards):
        with col:
            st.markdown(f'<div class="panel"><div style="font-size:1.5rem;color:#5cdff7">{ico}</div><div class="panel-title">{title}</div><div class="muted">{desc}</div></div>',unsafe_allow_html=True)
            if st.button(f"Open {title}",key="go_"+title,use_container_width=True):
                st.session_state.active_page=title; st.rerun()
    st.subheader("Quick Command")
    with st.form("quick_command"):
        quick=st.text_input("Tell ELINA what you need",placeholder="যেমন: এই সপ্তাহের affiliate performance বিশ্লেষণ করো")
        submitted=st.form_submit_button("Run command")
    if submitted and quick:
        st.session_state.quick_result=ask_ai(quick)
        st.session_state.active_page="AI Assistant"; st.rerun()
    st.caption("Note: Reports, memory, team and payment records are stored in the app database. Streamlit Cloud's local disk may reset on rebuild; connect durable external storage for long-term records.")

# ----------------------------- AI Chat -----------------------------
elif page=="AI Assistant":
    st.markdown('<div class="eyebrow">PERSONAL INTELLIGENCE</div>',unsafe_allow_html=True)
    st.title("✧ Chat with ELINA AI")
    st.caption("Bangla or English — ask about your business, campaigns, reports, planning or daily work.")
    for m in st.session_state.chat_messages:
        with st.chat_message(m["role"]): st.markdown(m["content"])
    if "quick_result" in st.session_state:
        st.success(st.session_state.pop("quick_result"))
    prompt=st.chat_input("Ask ELINA AI anything...")
    if prompt:
        with st.spinner("ELINA is thinking..."):
            ans=ask_ai(prompt)
        st.rerun()
    if st.session_state.chat_messages and st.session_state.chat_messages[-1]["role"]=="assistant":
        if st.button("🔊 Read latest answer aloud"):
            if client:
                try:
                    speech=client.audio.speech.create(model="gpt-4o-mini-tts",voice="alloy",input=st.session_state.chat_messages[-1]["content"])
                    st.audio(speech.read(),format="audio/mp3")
                except Exception as e: st.error(f"Text-to-speech error: {e}")
            else: st.warning("Add OPENAI_API_KEY to enable spoken replies.")

# ----------------------------- Voice -----------------------------
elif page=="Voice Assistant":
    st.markdown('<div class="eyebrow">VOICE INTERFACE</div>',unsafe_allow_html=True)
    st.title("◉ JARVIS Voice Assistant")
    st.caption("Record a message in Bengali or English. ELINA transcribes it, replies, and can speak the answer.")
    if not client:
        st.warning("Voice AI needs OPENAI_API_KEY in Streamlit Secrets.")
    audio=st.audio_input("🎙️ Press to record your message",key="jarvis_audio")
    speak=st.toggle("Speak ELINA's reply aloud",value=True)
    if st.button("Send voice to ELINA",type="primary",use_container_width=True):
        if audio is None: st.warning("আগে microphone দিয়ে voice record করো।")
        elif not client: st.error("OPENAI_API_KEY is missing.")
        else:
            try:
                raw=audio.getvalue()
                import hashlib
                digest=hashlib.sha256(raw).hexdigest()
                if digest==st.session_state.last_audio_hash: st.info("এই voice message ইতিমধ্যে পাঠানো হয়েছে।")
                else:
                    st.session_state.last_audio_hash=digest
                    with st.spinner("শুনছি এবং উত্তর তৈরি করছি..."):
                        with tempfile.NamedTemporaryFile(delete=False,suffix=".wav") as f:
                            f.write(raw); path=f.name
                        try:
                            with open(path,"rb") as af:
                                tr=client.audio.transcriptions.create(model="whisper-1",file=af)
                        finally: os.unlink(path)
                        spoken=(tr.text or "").strip()
                        if not spoken: st.warning("কথা পরিষ্কার শোনা যায়নি। আবার চেষ্টা করো।")
                        else:
                            st.info("তুমি বলেছ: "+spoken)
                            ans=ask_ai(spoken,speak=speak)
                            st.markdown("### ELINA AI")
                            st.markdown(ans)
                            if speak and getattr(st.session_state,"last_tts",None):
                                st.audio(st.session_state.last_tts,format="audio/mp3")
            except Exception as e: st.error(f"Voice processing error: {e}")
    st.divider()
    st.markdown("**Browser permission:** Chrome address bar-এর site settings থেকে Microphone → Allow করতে হবে।")

# ----------------------------- Reports -----------------------------
elif page=="Business Reports":
    st.markdown('<div class="eyebrow">AFFILIATE INTELLIGENCE</div>',unsafe_allow_html=True)
    st.title("📊 Affiliate Business Analytics")

    upload_col, search_col = st.columns(2, gap="large")
    with upload_col:
        uploaded_file = st.file_uploader(
            "Upload CSV, Excel or PDF report", type=["csv", "xlsx", "xls", "pdf"],
            key="business_csv", help="CSV/XLSX is preferred for exact totals. PDF extraction is best-effort."
        )
    with search_col:
        search_text = st.text_area(
            "🔎 Search Sub IDs (one per line or comma-separated)", height=105,
            placeholder="SD_TU_santo\\nonline\\nIQ_748", key="business_subid_search"
        )
        st.caption("Match Sub IDs — automatically matches the entered text anywhere in a Sub ID (case-insensitive).")
        search_clicked = st.button("🔍 Search & Calculate", type="primary", key="business_search")

    if uploaded_file is not None:
        upload_hash = hashlib.sha256(uploaded_file.getvalue()).hexdigest()
        if upload_hash != st.session_state.report_source_hash:
            try:
                loaded_df = load_report(uploaded_file)
                st.session_state.report_df = loaded_df
                st.session_state.report_source_name = uploaded_file.name
                st.session_state.report_source_hash = upload_hash
                st.session_state.business_selected_df = None
                st.success(f"Report loaded: {len(loaded_df):,} unique Sub IDs")
            except Exception as e:
                st.error(f"Could not read report: {e}")

    report_df = st.session_state.report_df
    if report_df is None:
        st.info("Upload a CSV, Excel or PDF report.")
    else:
        if st.session_state.report_source_name:
            st.caption(f"Current report: {st.session_state.report_source_name}")
        metric_map = report_df.attrs.get("metric_columns", {})
        if metric_map:
            mapped = ", ".join(
                f"{metric}: {column if column else 'not present'}"
                for metric, column in metric_map.items()
            )
            st.caption("Detected report columns — " + mapped)
        if uploaded_file is not None and uploaded_file.name.lower().endswith(".pdf"):
            st.warning("PDF extraction is best-effort. Review extracted rows before using totals for team payments.")

        if search_clicked:
            requested = list(dict.fromkeys(clean_subid(x) for x in re.split(r"[,;\n]+", search_text) if x.strip()))
            if not requested:
                st.warning("Enter at least one Sub ID to search.")
                st.session_state.business_selected_df = None
            else:
                selected = report_df[report_df["Sub ID"].apply(
                    lambda sid: any(term in clean_subid(sid) for term in requested)
                )].copy()
                if selected.empty:
                    st.warning("No matching Sub IDs found.")
                    st.session_state.business_selected_df = None
                else:
                    # load_report already aggregates duplicate rows by Sub ID.
                    # Do not filter out zero-conversion rows: their clicks/earnings may still matter.
                    selected = selected[["Sub ID", "Clicks", "Leads", "Earnings"]].copy()
                    selected = selected.rename(columns={"Leads": "Conversions"})
                    st.session_state.business_selected_df = selected

        selected = st.session_state.business_selected_df
        if selected is not None and not selected.empty:
            st.markdown("### 🔎 Selected Sub ID Results")
            st.dataframe(selected, use_container_width=True, hide_index=True)
            st.markdown("### Combined Totals")
            total_cols = st.columns(3)
            for col, label in zip(total_cols, ["Clicks", "Conversions", "Earnings"]):
                value = pd.to_numeric(selected[label], errors="coerce").sum(min_count=1)
                display = "Not in report" if pd.isna(value) else (f"${value:,.2f}" if label == "Earnings" else f"{value:,.0f}")
                col.metric(label, display)
            d1, d2 = st.columns(2)
            with d1:
                st.download_button("⬇️ Download selected report CSV", selected.to_csv(index=False).encode("utf-8-sig"),
                                   "elina_subid_results.csv", "text/csv", use_container_width=True)
            with d2:
                try:
                    excel_buffer = BytesIO()
                    selected.to_excel(excel_buffer, index=False, engine="openpyxl")
                    st.download_button("⬇️ Download selected report Excel", excel_buffer.getvalue(),
                                       "elina_subid_results.xlsx",
                                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                       use_container_width=True)
                except ImportError:
                    st.info("Excel download needs openpyxl. CSV download is available.")

        with st.expander("View complete uploaded report"):
            st.dataframe(report_df, use_container_width=True, hide_index=True)
            st.download_button("Download complete report CSV", report_df.to_csv(index=False).encode("utf-8-sig"),
                               "elina_complete_report.csv", "text/csv")


# ----------------------------- Payments -----------------------------
elif page=="Payments":
    st.markdown('<div class="eyebrow">FINANCE CONTROL</div>',unsafe_allow_html=True)
    st.title("▣ Payments & Ledger")
    st.caption("Track payment obligations and reconciliation. This module records payments; it does not transfer money.")
    p1,p2,p3=st.columns(3)
    rows=query("SELECT status,COALESCE(SUM(amount),0) total FROM payments GROUP BY status")
    totals={r["status"]:r["total"] for r in rows}
    p1.metric("Pending",currency(totals.get("Pending",0)))
    p2.metric("Paid",currency(totals.get("Paid",0)))
    p3.metric("On hold",currency(totals.get("On Hold",0)))
    with st.form("add_payment",clear_on_submit=True):
        st.subheader("Add payment record")
        c1,c2,c3=st.columns(3)
        member=c1.text_input("Team member / recipient")
        period=c2.text_input("Period",placeholder="2026-W44 / Oct 26–Nov 1")
        amount=c3.number_input("Amount (USD)",min_value=0.0,step=1.0)
        status=st.selectbox("Status",["Pending","Paid","On Hold"])
        ref=st.text_input("Reference / transaction ID")
        notes=st.text_input("Notes")
        save=st.form_submit_button("Save payment record")
    if save:
        if not member.strip() or amount<=0: st.error("Recipient and amount are required.")
        else:
            execute("INSERT INTO payments(member_name,period,amount,currency,status,reference,notes,created_at) VALUES(?,?,?,?,?,?,?,?)",
                    (member.strip(),period,amount,"USD",status,ref,notes,datetime.now().isoformat(timespec="seconds")))
            st.success("Payment record saved."); st.rerun()
    payments=query("SELECT * FROM payments ORDER BY id DESC LIMIT 500")
    if payments:
        pdf=pd.DataFrame([dict(r) for r in payments])
        st.dataframe(pdf,use_container_width=True,hide_index=True)
        st.download_button("Export payment ledger CSV",pdf.to_csv(index=False).encode("utf-8-sig"),"elina_payment_ledger.csv","text/csv")
        with st.expander("Update payment status"):
            pid=st.selectbox("Payment record ID",[r["id"] for r in payments])
            newstatus=st.selectbox("New status",["Pending","Paid","On Hold"])
            if st.button("Update status"):
                execute("UPDATE payments SET status=? WHERE id=?",(newstatus,pid)); st.success("Status updated."); st.rerun()
    else: st.info("No payment records yet.")

# ----------------------------- Team -----------------------------
elif page=="Team Management":
    st.markdown('<div class="eyebrow">PEOPLE & OPERATIONS</div>',unsafe_allow_html=True)
    st.title("♙ Team Management")
    with st.form("add_member",clear_on_submit=True):
        n=st.text_input("Member name")
        w=st.text_input("WhatsApp / contact (optional)")
        g=st.text_input("Group / offer")
        add=st.form_submit_button("Add team member")
    if add:
        if n.strip():
            execute("INSERT INTO team(member_name,whatsapp,group_name,created_at) VALUES(?,?,?,?)",(n.strip(),w.strip(),g.strip(),datetime.now().isoformat(timespec="seconds")))
            st.success("Team member added."); st.rerun()
        else: st.error("Name is required.")
    members=query("SELECT * FROM team ORDER BY member_name")
    if members:
        mdf=pd.DataFrame([dict(r) for r in members])
        st.dataframe(mdf,use_container_width=True,hide_index=True)
        with st.expander("Deactivate or remove a member"):
            mid=st.selectbox("Member ID",[r["id"] for r in members])
            if st.button("Deactivate member"):
                execute("UPDATE team SET active=0 WHERE id=?",(mid,)); st.success("Member deactivated."); st.rerun()
            if st.button("Delete member record",type="secondary"):
                execute("DELETE FROM team WHERE id=?",(mid,)); st.warning("Member deleted."); st.rerun()
    else: st.info("Team directory is empty. Add your first team member.")

# ----------------------------- Tasks -----------------------------
elif page=="Tasks":
    st.markdown('<div class="eyebrow">PERSONAL PRODUCTIVITY</div>',unsafe_allow_html=True)
    st.title("✓ Tasks & Follow-ups")
    with st.form("new_task",clear_on_submit=True):
        title=st.text_input("Task")
        c1,c2=st.columns(2)
        due=c1.date_input("Due date",value=date.today())
        priority=c2.selectbox("Priority",["Low","Normal","High","Urgent"],index=1)
        notes=st.text_area("Notes (optional)")
        add=st.form_submit_button("Add task")
    if add:
        if title.strip():
            execute("INSERT INTO tasks(title,due_date,priority,status,notes,created_at) VALUES(?,?,?,?,?,?)",(title.strip(),due.isoformat(),priority,"Open",notes,datetime.now().isoformat(timespec="seconds")))
            st.success("Task created."); st.rerun()
        else: st.error("Task title is required.")
    tasks=query("SELECT * FROM tasks ORDER BY CASE status WHEN 'Open' THEN 0 ELSE 1 END, due_date, id DESC")
    if tasks:
        for t in tasks:
            with st.container(border=True):
                c1,c2,c3=st.columns([4,1,1])
                c1.markdown(f"**{t['title']}**  \n<span class='muted'>Due: {t['due_date'] or '—'} · Priority: {t['priority']} · {t['notes'] or ''}</span>",unsafe_allow_html=True)
                c2.write(t["status"])
                if t["status"]!="Done" and c3.button("Complete",key=f"done_{t['id']}"):
                    execute("UPDATE tasks SET status='Done' WHERE id=?",(t["id"],)); st.rerun()
                elif t["status"]=="Done" and c3.button("Reopen",key=f"open_{t['id']}"):
                    execute("UPDATE tasks SET status='Open' WHERE id=?",(t["id"],)); st.rerun()
    else: st.info("No tasks. Add a follow-up to get started.")

# ----------------------------- Memory -----------------------------
elif page=="Memory":
    st.markdown('<div class="eyebrow">PERSONAL CONTEXT</div>',unsafe_allow_html=True)
    st.title("◈ ELINA Memory")
    st.caption("Save useful business preferences and working instructions. These are added to the AI context.")
    with st.form("save_memory",clear_on_submit=True):
        cat=st.selectbox("Category",["Business","Offers & Payouts","Team","Writing Preferences","Personal Workflow","Other"])
        content=st.text_area("Memory / instruction")
        save=st.form_submit_button("Save memory")
    if save:
        if content.strip():
            execute("INSERT INTO memories(category,content,created_at) VALUES(?,?,?)",(cat,content.strip(),datetime.now().isoformat(timespec="seconds")))
            st.success("Memory saved."); st.rerun()
        else: st.error("Write a memory first.")
    mem=query("SELECT * FROM memories ORDER BY id DESC")
    if mem:
        for m in mem:
            with st.container(border=True):
                st.markdown(f"**{m['category']}** · {m['created_at']}")
                st.write(m["content"])
                if st.button("Delete",key=f"delmem_{m['id']}"):
                    execute("DELETE FROM memories WHERE id=?",(m["id"],)); st.rerun()
    else: st.info("No saved memories yet.")

# ----------------------------- Email assistant -----------------------------
elif page=="Email Assistant":
    st.markdown('<div class="eyebrow">COMMUNICATION COPILOT</div>',unsafe_allow_html=True)
    st.title("✉ Email & Message Assistant")
    st.caption("Generate professional English drafts for affiliate managers. Review and send them yourself.")
    recipient=st.text_input("Manager / recipient name (optional)")
    topic=st.text_input("What is the message about?",placeholder="Request weekly payment and payout increase")
    details=st.text_area("Key points to include",placeholder="I have improved traffic quality. I can scale to 50 leads per day...")
    tone=st.selectbox("Tone",["Professional and polite","Confident and firm","Short and direct","Friendly"])
    if st.button("Generate English draft",type="primary"):
        if not topic.strip() or not details.strip(): st.warning("Add the topic and key points first.")
        elif not client: st.error("OpenAI API key is required.")
        else:
            with st.spinner("Drafting..."):
                try:
                    req=f"Write a concise natural English affiliate-manager email/message. Tone: {tone}. Recipient name: {recipient or 'Manager'}. Topic: {topic}. Include these points accurately: {details}. Do not invent facts, rates, volumes or promises. Provide only the draft."
                    out=client.chat.completions.create(model="gpt-4o-mini",messages=[{"role":"system","content":SYSTEM_PROMPT},{"role":"user","content":req}])
                    st.session_state.email_draft=out.choices[0].message.content
                except Exception as e: st.error(str(e))
    if st.session_state.get("email_draft"):
        st.text_area("Your draft",st.session_state.email_draft,height=260)
        st.download_button("Download draft TXT",st.session_state.email_draft.encode("utf-8"),"elina_email_draft.txt","text/plain")

# ----------------------------- Settings -----------------------------
elif page=="Settings":
    st.markdown('<div class="eyebrow">SYSTEM CONFIGURATION</div>',unsafe_allow_html=True)
    st.title("⚙ Settings & Diagnostics")
    st.subheader("Connection status")
    s1,s2,s3=st.columns(3)
    s1.metric("OpenAI API","Connected" if client else "Not connected")
    s2.metric("Database","SQLite ready")
    s3.metric("Voice input","Available" if client else "Needs API key")
    st.subheader("Model and voice")
    st.write("Chat model: `gpt-4o-mini`")
    st.write("Transcription: `whisper-1`")
    st.write("Speech output: `gpt-4o-mini-tts` · voice `alloy`")
    st.info("To change API credentials, use Streamlit → Manage app → Settings → Secrets. Do not paste API keys into chat or GitHub.")
    st.subheader("Data and backups")
    st.warning("Streamlit Community Cloud local files are not guaranteed to persist across rebuilds. Download regular backups or connect a managed database before relying on this as your only business ledger.")
    with st.expander("Export workspace database backup"):
        if st.button("Prepare database backup"):
            with open(DB_PATH,"rb") as f: st.session_state.db_backup=f.read()
        if st.session_state.get("db_backup"):
            st.download_button("Download SQLite backup",st.session_state.db_backup,"elina_ai_backup.db","application/octet-stream")
    st.subheader("Session")
    if st.button("Log out"):
        st.session_state.authenticated=False
        st.session_state.chat_messages=[]
        st.rerun()

st.divider()
st.markdown('<div style="text-align:center;color:#657b9f;font-size:.72rem;letter-spacing:.12em">ELINA AI · JARVIS HYBRID BUSINESS OS · PRIVATE WORKSPACE</div>',unsafe_allow_html=True)

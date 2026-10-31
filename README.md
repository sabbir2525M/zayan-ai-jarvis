Zayan AI — JARVIS Hybrid Business OS
A private Streamlit workspace with a JARVIS-inspired hybrid command-center interface.
Included modules
Secure password login
Bengali/English AI chat using OpenAI
Voice recording, transcription, and spoken AI replies (OpenAI)
Affiliate report upload (CSV/XLSX/PDF text extraction), Sub ID search, offer grouping
Team report vs network report reconciliation
Manual payment ledger and status tracking (does not transfer money)
Team directory
Tasks and follow-ups
Persistent-in-database personal memory
English affiliate-manager email/message draft assistant
Settings, diagnostics, and SQLite backup download
GitHub root files
Upload these files to the root of `sabbir2525M/zayan-ai-jarvis`:
`app.py`
`requirements.txt`
`README.md`
Streamlit Cloud
Repository: `sabbir2525M/zayan-ai-jarvis`
Branch: `main`
Main file: `app.py`
Python: 3.12 recommended
In Streamlit → Manage app → Settings → Secrets, add:
```toml
APP_PASSWORD = "choose-a-strong-private-password"
OPENAI_API_KEY = "your-openai-api-key"
```
Never commit real keys, passwords, `.env`, `secrets.toml`, or database files to GitHub.
Run locally (Windows PowerShell)
```powershell
py -m pip install -r requirements.txt
mkdir .streamlit
notepad .streamlit/secrets.toml
py -m streamlit run app.py
```
Put the two TOML secrets above into `.streamlit/secrets.toml`.
Important limitations
Email Assistant creates drafts only; it does not send email.
Payments records and reconciliation do not initiate bank transfers.
Reports are parsed from uploaded files; this does not connect to MaxBounty or advertiser accounts automatically.
Voice input and spoken replies require a valid OpenAI API key and microphone permission in the browser.
The app uses SQLite by default. Streamlit Community Cloud local storage is not guaranteed durable across rebuilds. Before relying on it as the only source of business records, connect a managed persistent database and keep backups.
AI and speech API usage may incur OpenAI charges.

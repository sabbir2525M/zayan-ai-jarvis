ELINA AI — JARVIS Hybrid Business OS
Private Streamlit workspace for affiliate operations, reporting, team records, payment tracking, and AI assistance.
Included modules
Secure password login
Bengali/English AI chat using OpenAI
Press-to-talk voice transcription and spoken replies
Affiliate report upload: CSV, XLSX, XLS, and text-based PDF
Sub ID search and aggregated report downloads
Team report vs. network report reconciliation
Manual payment ledger and status tracking (does not transfer money)
Team directory, tasks, and follow-ups
Database-backed personal memory
English affiliate-manager email/message drafting
Settings, diagnostics, and SQLite backup download
Affiliate report calculation rules
If both `Payout` and `Earnings` exist, the app uses the source `Payout` column first.
The app does not subtract advertising spend, team costs, or an assumed payout rate from gross payout.
PDF rows are parsed using the table's Sub ID, Clicks, Conversions, Status, Payout, and Converted At fields.
If a PDF includes footer totals, extracted clicks, conversions, and payout are compared with those totals.
If PDF totals do not match, the app warns against using the extracted figures for payment.
Duplicate Sub IDs are aggregated after each source row is parsed.
PDF extraction is best-effort. Review extracted rows and prefer the original CSV/XLSX export when available.
GitHub deployment
Repository: `sabbir2525M/zayan-ai-jarvis`  
Branch: `main`  
Main file: `app.py`  
Python: 3.12 recommended
Upload these files to the repository root:
`app.py`
`requirements.txt`
`README.md`
In Streamlit → Manage app → Settings → Secrets, add:
```toml
APP_PASSWORD = "choose-a-strong-private-password"
OPENAI_API_KEY = "your-openai-api-key"
```
Never commit real API keys, passwords, `.env`, `secrets.toml`, or database files to GitHub.
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
Payment records and reconciliation do not initiate bank transfers.
Reports are parsed from uploaded files; the app does not connect to MaxBounty or advertiser accounts automatically.
Voice input and spoken replies require a valid OpenAI API key and browser microphone permission.
SQLite is used by default. Streamlit Community Cloud local storage is not guaranteed to persist across rebuilds. Connect a managed persistent database and keep backups before relying on this as the only source of business records.
AI and speech API usage may incur OpenAI charges.

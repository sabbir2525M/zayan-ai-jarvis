# Zayan AI — JARVIS Business Workspace

A Streamlit-based personal AI assistant and affiliate business reporting workspace. The interface uses a dark JARVIS-inspired command-center design and includes Overview, AI Assistant, Voice Assistant, Business Reports, Payments, and Settings sections.

## Files

- `app.py` — Streamlit application.
- `requirements.txt` — Python dependencies for Streamlit Cloud.
- `README.md` — project documentation.

## Deploy on Streamlit Community Cloud

1. Create a GitHub repository and upload these three files to the repository root.
2. In Streamlit Community Cloud, choose **Create app** and select this repository.
3. Set the branch to `main` and the main file path to `app.py`.
4. In **Advanced settings → Secrets**, add the following TOML secrets:

```toml
APP_PASSWORD = "choose-a-strong-private-password"
OPENAI_API_KEY = "your-openai-api-key"
```

5. Deploy the app. Keep the repository private if you do not want the source code to be public.

## Security notes

- Never commit API keys, passwords, `.env` files, or Streamlit secrets to GitHub.
- Configure `APP_PASSWORD` in Streamlit Cloud Secrets before opening the app. The app intentionally blocks access if it is not configured.
- Configure `OPENAI_API_KEY` to enable AI and voice features that use the OpenAI API. API usage may incur charges.

## Local run

```bash
pip install -r requirements.txt
streamlit run app.py
```

For local use, create a `.streamlit/secrets.toml` file with the same secret keys. Do not upload that file to GitHub.

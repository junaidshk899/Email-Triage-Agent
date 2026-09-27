# 📬 Email Triage Agent

An AI-powered email assistant that automatically reads, classifies, and drafts replies to your emails in real time — built with Google Gemini, Gmail API, Slack, Notion, and Streamlit.

---

## 🚀 Features

- 📥 **Gmail Integration** — Connects to your inbox and fetches unread emails
- 🤖 **AI Classification** — Uses Google Gemini to classify each email by priority (🔴 Urgent / 🟡 Normal / 🟢 Low)
- ✍️ **Draft Replies** — Auto-generates professional draft replies for each email
- 🏷️ **Auto-Labeling** — Applies Gmail labels (Triage/Urgent, Triage/Normal, Triage/Low) automatically
- 🔔 **Slack Alerts** — Sends real-time notifications to Slack when an urgent email arrives
- 📓 **Notion Reports** — Saves full triage reports as formatted Notion pages
- 🖥️ **Streamlit UI** — Review and edit AI-generated drafts in a clean browser interface
- ⚡ **Real-Time Webhooks** — Uses Gmail Push Notifications via Google Cloud Pub/Sub for instant triaging

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| Google Gemini API | Email classification and draft generation |
| Gmail API | Fetch emails, apply labels |
| Google Cloud Pub/Sub | Gmail push notifications |
| Slack Webhooks | Urgent email alerts |
| Notion API | Save triage reports |
| FastAPI | Webhook server for real-time triaging |
| Streamlit | Browser-based review UI |
| ngrok | Expose local server for webhooks |

---

## 📁 Project Structure

```
email-triage-agent/
├── main.py                  # Core triage pipeline (CLI)
├── app.py                   # Streamlit UI
├── gmail_client.py          # Gmail API connection and helpers
├── triage_agent.py          # Gemini AI classification and drafting
├── webhook_server.py        # FastAPI webhook server
├── setup_watch.py           # Register Gmail push notifications
├── notion_client_helper.py  # Notion API integration
├── credentials.json         # Google OAuth credentials (not committed)
├── token.json               # Gmail auth token (auto-generated)
├── .env                     # Environment variables (not committed)
└── requirements.txt         # Python dependencies
```

---

## ⚙️ Setup Guide

### 1. Clone the repository

```bash
git clone https://github.com/your-username/email-triage-agent.git
cd email-triage-agent
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Mac/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the root directory:

```env
GEMINI_API_KEY=your-gemini-api-key
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url
NOTION_TOKEN=secret_your-notion-token
NOTION_PAGE_ID=your-notion-page-id
PUBSUB_TOPIC=projects/your-project-id/topics/gmail-triage
```

### 5. Set up Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project and enable the **Gmail API**
3. Create **OAuth 2.0 credentials** (Desktop App)
4. Download `credentials.json` and place it in the project root

### 6. Set up Slack

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → Create New App
2. Enable **Incoming Webhooks**
3. Add webhook to your workspace channel
4. Copy the webhook URL to `.env`

### 7. Set up Notion

1. Go to [notion.so/my-integrations](https://www.notion.so/my-integrations) → New Integration
2. Copy the **Internal Integration Token** to `.env`
3. Create a Notion page called `Email Triage Reports`
4. Connect the integration to that page (⋯ → Connect to)
5. Copy the page ID from the URL to `.env`

### 8. Set up Google Cloud Pub/Sub (for real-time webhooks)

1. Go to [Google Cloud Console](https://console.cloud.google.com) → Pub/Sub
2. Create a topic named `gmail-triage`
3. Grant publish permission to `gmail-api-push@system.gserviceaccount.com`
4. Create a Push subscription pointing to your ngrok URL + `/webhook`

---

## ▶️ Running the Project

### Option A — Manual triage (CLI)

```bash
python main.py
```

### Option B — Streamlit UI

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### Option C — Real-time webhook mode

Open 3 terminals and run one command in each:

```bash
# Terminal 1 — Webhook server
uvicorn webhook_server:app --reload --port 8000

# Terminal 2 — ngrok tunnel
ngrok http 8000

# Terminal 3 — Register Gmail watch (run once)
python setup_watch.py
```

> ⚠️ The Gmail watch expires every 7 days. Re-run `python setup_watch.py` weekly to keep real-time triaging active.

---

## 🔒 Security Notes

- Never commit `.env`, `credentials.json`, or `token.json` to GitHub
- All three are listed in `.gitignore`
- Rotate your API keys if accidentally exposed

---

## 📄 Requirements

Create a `requirements.txt` with:

```
anthropic
google-auth
google-auth-oauthlib
google-api-python-client
google-genai
notion-client
fastapi
uvicorn
streamlit
requests
python-dotenv
ngrok
```

---

## 🗺️ Roadmap

- [ ] Auto-send approved replies via Gmail API
- [ ] Daily digest email summary
- [ ] Multi-account Gmail support
- [ ] Mobile app notifications
- [ ] Fine-tuned classification model

---

## 🤝 Connect

Built by **Muhammad Junaid**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-blue)](https://www.linkedin.com/in/your-profile)
[![GitHub](https://img.shields.io/badge/GitHub-Follow-black)](https://github.com/your-username)

---

## 📜 License

MIT License — feel free to use, modify, and share.

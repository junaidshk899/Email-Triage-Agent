from fastapi import FastAPI, Request, BackgroundTasks
from gmail_client import get_gmail_service, fetch_single_email, get_or_create_label, apply_label
from triage_agent import classify_and_draft
from main import send_slack_alert
from notion_client_helper import save_report_to_notion
from datetime import datetime
import base64
import json
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

PROCESSED_IDS = set()  # prevent duplicate processing

@app.get("/")
def root():
    return {"status": "Email Triage Webhook running"}

@app.post("/webhook")
async def gmail_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        body = await request.json()
        # Decode the Pub/Sub message
        pubsub_message = body.get("message", {})
        data = pubsub_message.get("data", "")
        decoded = json.loads(base64.b64decode(data).decode("utf-8"))

        email_address = decoded.get("emailAddress")
        history_id = decoded.get("historyId")

        print(f"📬 New email notification for {email_address} (historyId: {history_id})")

        # Process in background so webhook returns fast
        background_tasks.add_task(process_new_emails, history_id)
        return {"status": "ok"}
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "message": str(e)}

async def process_new_emails(history_id: str):
    try:
        service = get_gmail_service()

        # Get new emails since last historyId
        history = service.users().history().list(
            userId='me',
            startHistoryId=history_id,
            historyTypes=['messageAdded']
        ).execute()

        messages = []
        for record in history.get('history', []):
            for msg in record.get('messagesAdded', []):
                msg_id = msg['message']['id']
                if msg_id not in PROCESSED_IDS:
                    messages.append(msg_id)
                    PROCESSED_IDS.add(msg_id)

        if not messages:
            print("No new messages to process.")
            return

        # Create labels
        labels = {
            'urgent': get_or_create_label(service, 'Triage/Urgent'),
            'normal': get_or_create_label(service, 'Triage/Normal'),
            'low':    get_or_create_label(service, 'Triage/Low')
        }

        results = []
        for msg_id in messages:
            email = fetch_single_email(service, msg_id)
            if not email:
                continue
            print(f"Processing: {email['subject'][:50]}...")
            result = classify_and_draft(email)

            # Apply label
            label_id = labels.get(result['priority'])
            if label_id:
                apply_label(service, result['id'], label_id)

            # Slack alert
            if result['priority'] == 'urgent':
                send_slack_alert(result)
                print(f"  ⚡ Slack alert sent!")

            results.append(result)
            print(f"  ✅ Done: {result['priority'].upper()}")

        # Save to Notion
        if results:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            notion_url = save_report_to_notion(results, timestamp)
            print(f"  📓 Notion page saved: {notion_url}")

    except Exception as e:
        print(f"Processing error: {e}")
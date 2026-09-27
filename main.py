from notion_client_helper import save_report_to_notion
from gmail_client import get_gmail_service, fetch_unread_emails, get_or_create_label, apply_label
from triage_agent import classify_and_draft
from datetime import datetime
import requests
import os
from dotenv import load_dotenv

load_dotenv()

PRIORITY_EMOJI = {'urgent': '🔴', 'normal': '🟡', 'low': '🟢'}
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

def send_slack_alert(email_result):
    if not SLACK_WEBHOOK_URL:
        return
    message = (
        f"🚨 *Urgent Email Alert*\n"
        f"*Subject:* {email_result['subject']}\n"
        f"*From:* {email_result['from']}\n"
        f"*Category:* {email_result['category']}\n"
        f"*Summary:* {email_result['summary']}"
    )
    requests.post(SLACK_WEBHOOK_URL, json={"text": message})

def run_triage():
    print("Connecting to Gmail...")
    service = get_gmail_service()
    emails = fetch_unread_emails(service, max_results=10)
    print(f"Found {len(emails)} unread emails. Triaging...\n")

    # Create labels once
    labels = {
        'urgent': get_or_create_label(service, 'Triage/Urgent'),
        'normal': get_or_create_label(service, 'Triage/Normal'),
        'low':    get_or_create_label(service, 'Triage/Low')
    }

    results = []
    for email in emails:
        print(f"Processing: {email['subject'][:50]}...")
        result = classify_and_draft(email)
        results.append(result)

        # Apply Gmail label
        label_id = labels.get(result['priority'])
        if label_id:
            apply_label(service, result['id'], label_id)
            print(f"  🏷️ Labeled as: {result['priority']}")

        # Send Slack alert for urgent
        if result['priority'] == 'urgent':
            send_slack_alert(result)
            print(f"  ⚡ Slack alert sent!")

    # Sort by priority
    priority_order = {'urgent': 0, 'normal': 1, 'low': 2}
    results.sort(key=lambda x: priority_order.get(x['priority'], 1))

    # Save output
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
    output_file = f'triage_{timestamp}.md'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Email Triage Report — {timestamp}\n\n")
        for r in results:
            emoji = PRIORITY_EMOJI.get(r['priority'], '⚪')
            f.write(f"## {emoji} {r['subject']}\n")
            f.write(f"**From:** {r['from']}  \n")
            f.write(f"**Priority:** {r['priority']} | **Category:** {r['category']}  \n")
            f.write(f"**Summary:** {r['summary']}\n\n")
            f.write(f"**Draft Reply:**\n\n{r['draft_reply'] if r['draft_reply'] else 'No reply needed.'}\n\n")
            f.write("---\n\n")

    print(f"\nDone! Report saved to: {output_file}")
    print(f"Urgent emails: {sum(1 for r in results if r['priority'] == 'urgent')}")
    print(f"Normal emails: {sum(1 for r in results if r['priority'] == 'normal')}")
    print(f"Low priority:  {sum(1 for r in results if r['priority'] == 'low')}")

    # Save to Notion
    print("\nSaving report to Notion...")
    notion_url = save_report_to_notion(results, timestamp)
    print(f"Notion page created: {notion_url}")
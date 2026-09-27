from google import genai
import os
import time
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def classify_and_draft(email: dict) -> dict:
    prompt = f"""You are an email triage assistant. Analyze this email and respond in this exact format:

PRIORITY: [urgent / normal / low]
CATEGORY: [action-required / information / newsletter / spam / meeting / question]
SUMMARY: [one sentence summary]
DRAFT_REPLY:
[Write a professional draft reply if a reply is needed, otherwise write "No reply needed."]

---EMAIL---
From: {email['from']}
Subject: {email['subject']}
Body:
{email['body']}
"""
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            time.sleep(15)
            return parse_response(response.text, email)
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            print(f"  Waiting 60 seconds before retry...")
            time.sleep(60)
    return {
        'id': email['id'],
        'subject': email['subject'],
        'from': email['from'],
        'priority': 'unknown',
        'category': 'unknown',
        'summary': 'Failed to process after 3 attempts.',
        'draft_reply': ''
    }

def parse_response(raw: str, email: dict) -> dict:
    lines = raw.strip().split('\n')
    data = {
        'id': email['id'],
        'subject': email['subject'],
        'from': email['from'],
        'priority': 'normal',
        'category': 'information',
        'summary': '',
        'draft_reply': ''
    }
    in_draft = False
    draft_lines = []
    for line in lines:
        if line.startswith('PRIORITY:'):
            data['priority'] = line.replace('PRIORITY:', '').strip().lower()
        elif line.startswith('CATEGORY:'):
            data['category'] = line.replace('CATEGORY:', '').strip().lower()
        elif line.startswith('SUMMARY:'):
            data['summary'] = line.replace('SUMMARY:', '').strip()
        elif line.startswith('DRAFT_REPLY:'):
            in_draft = True
        elif in_draft:
            draft_lines.append(line)
    data['draft_reply'] = '\n'.join(draft_lines).strip()
    return data
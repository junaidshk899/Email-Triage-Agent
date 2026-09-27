import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('gmail', 'v1', credentials=creds)

def get_or_create_label(service, label_name):
    existing = service.users().labels().list(userId='me').execute()
    for label in existing.get('labels', []):
        if label['name'] == label_name:
            return label['id']
    created = service.users().labels().create(
        userId='me',
        body={'name': label_name, 'labelListVisibility': 'labelShow', 'messageListVisibility': 'show'}
    ).execute()
    return created['id']

def apply_label(service, email_id, label_id):
    service.users().messages().modify(
        userId='me',
        id=email_id,
        body={'addLabelIds': [label_id]}
    ).execute()

def fetch_single_email(service, msg_id: str):
    try:
        msg_data = service.users().messages().get(
            userId='me', id=msg_id, format='full'
        ).execute()
        headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
        body = ''
        if 'parts' in msg_data['payload']:
            for part in msg_data['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        elif 'body' in msg_data['payload'] and 'data' in msg_data['payload']['body']:
            body = base64.urlsafe_b64decode(msg_data['payload']['body']['data']).decode('utf-8')
        return {
            'id': msg_id,
            'from': headers.get('From', ''),
            'subject': headers.get('Subject', ''),
            'body': body[:2000]
        }
    except Exception as e:
        print(f"Error fetching email {msg_id}: {e}")
        return None
    
def fetch_unread_emails(service, max_results=10):
    results = service.users().messages().list(
        userId='me', labelIds=['INBOX'], q='is:unread', maxResults=max_results
    ).execute()
    messages = results.get('messages', [])
    emails = []
    for msg in messages:
        msg_data = service.users().messages().get(
            userId='me', id=msg['id'], format='full'
        ).execute()
        headers = {h['name']: h['value'] for h in msg_data['payload']['headers']}
        body = ''
        if 'parts' in msg_data['payload']:
            for part in msg_data['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                    break
        elif 'body' in msg_data['payload'] and 'data' in msg_data['payload']['body']:
            body = base64.urlsafe_b64decode(msg_data['payload']['body']['data']).decode('utf-8')
        emails.append({
            'id': msg['id'],
            'from': headers.get('From', ''),
            'subject': headers.get('Subject', ''),
            'body': body[:2000]  # truncate long emails
        })
    return emails
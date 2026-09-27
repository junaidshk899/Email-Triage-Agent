from gmail_client import get_gmail_service
import os
from dotenv import load_dotenv

load_dotenv()

TOPIC_NAME = os.getenv("PUBSUB_TOPIC")

def setup_gmail_watch():
    service = get_gmail_service()
    request = {
        'labelIds': ['INBOX'],
        'topicName': TOPIC_NAME
    }
    result = service.users().watch(userId='me', body=request).execute()
    print(f"✅ Gmail watch set up successfully!")
    print(f"   History ID: {result['historyId']}")
    print(f"   Expiration: {result['expiration']}")
    print(f"   (Watch expires in 7 days — re-run this script weekly)")

if __name__ == '__main__':
    setup_gmail_watch()
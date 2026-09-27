from notion_client import Client
import os
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.getenv("NOTION_TOKEN"))
PARENT_PAGE_ID = os.getenv("NOTION_PAGE_ID")

PRIORITY_EMOJI = {'urgent': '🔴', 'normal': '🟡', 'low': '🟢'}

def save_report_to_notion(results: list, timestamp: str):
    # Create a new child page under the parent
    new_page = notion.pages.create(
        parent={"page_id": PARENT_PAGE_ID},
        properties={
            "title": [
                {
                    "type": "text",
                    "text": {"content": f"Email Triage Report — {timestamp}"}
                }
            ]
        },
        children=build_page_blocks(results, timestamp)
    )
    return new_page['url']

def build_page_blocks(results: list, timestamp: str):
    blocks = []

    # Header
    blocks.append({
        "object": "block",
        "type": "heading_1",
        "heading_1": {
            "rich_text": [{"type": "text", "text": {"content": f"📬 Email Triage Report — {timestamp}"}}]
        }
    })

    # Summary callout
    urgent = sum(1 for r in results if r['priority'] == 'urgent')
    normal = sum(1 for r in results if r['priority'] == 'normal')
    low    = sum(1 for r in results if r['priority'] == 'low')

    blocks.append({
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {
                "content": f"🔴 Urgent: {urgent}   🟡 Normal: {normal}   🟢 Low: {low}   |   Total: {len(results)}"
            }}],
            "icon": {"emoji": "📊"}
        }
    })

    blocks.append({"object": "block", "type": "divider", "divider": {}})

    # Email blocks
    for r in results:
        emoji = PRIORITY_EMOJI.get(r['priority'], '⚪')

        # Email heading
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": f"{emoji} {r['subject']}"}}]
            }
        })

        # Metadata
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "From: "}, "annotations": {"bold": True}},
                    {"type": "text", "text": {"content": r['from']}},
                    {"type": "text", "text": {"content": "   Priority: "}, "annotations": {"bold": True}},
                    {"type": "text", "text": {"content": r['priority'].upper()}, "annotations": {"code": True}},
                    {"type": "text", "text": {"content": "   Category: "}, "annotations": {"bold": True}},
                    {"type": "text", "text": {"content": r['category']}, "annotations": {"code": True}},
                ]
            }
        })

        # Summary
        blocks.append({
            "object": "block",
            "type": "quote",
            "quote": {
                "rich_text": [{"type": "text", "text": {"content": r['summary']}}]
            }
        })

        # Draft reply
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {"type": "text", "text": {"content": "Draft Reply: "}, "annotations": {"bold": True}},
                ]
            }
        })
        blocks.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {
                    "content": r['draft_reply'] if r['draft_reply'] else "No reply needed."
                }}]
            }
        })

        blocks.append({"object": "block", "type": "divider", "divider": {}})

    return blocks
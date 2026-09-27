from notion_client_helper import save_report_to_notion
import streamlit as st
import os
from gmail_client import get_gmail_service, fetch_unread_emails, get_or_create_label, apply_label
from triage_agent import classify_and_draft
from main import send_slack_alert
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

PRIORITY_EMOJI = {'urgent': '🔴', 'normal': '🟡', 'low': '🟢'}
PRIORITY_COLOR = {'urgent': '#ff4b4b', 'normal': '#ffa500', 'low': '#21c354'}

st.set_page_config(page_title="Email Triage Agent", page_icon="📬", layout="wide")
st.title("📬 Email Triage Agent")
st.caption("Review AI-generated drafts before sending")

# --- Sidebar controls ---
with st.sidebar:
    st.header("⚙️ Settings")
    max_emails = st.slider("Max emails to fetch", 1, 20, 10)
    run_btn = st.button("🔄 Fetch & Triage Emails", use_container_width=True)
    st.divider()
    st.markdown("**Priority Legend**")
    st.markdown("🔴 Urgent — 🟡 Normal — 🟢 Low")

# --- Session state ---
if 'results' not in st.session_state:
    st.session_state.results = []
if 'service' not in st.session_state:
    st.session_state.service = None

# --- Fetch and triage ---
if run_btn:
    with st.spinner("Connecting to Gmail and triaging emails..."):
        try:
            service = get_gmail_service()
            st.session_state.service = service
            emails = fetch_unread_emails(service, max_results=max_emails)

            labels = {
                'urgent': get_or_create_label(service, 'Triage/Urgent'),
                'normal': get_or_create_label(service, 'Triage/Normal'),
                'low':    get_or_create_label(service, 'Triage/Low')
            }

            results = []
            progress = st.progress(0, text="Starting...")
            for i, email in enumerate(emails):
                progress.progress((i + 1) / len(emails), text=f"Processing: {email['subject'][:40]}...")
                result = None
                for attempt in range(3):
                    try:
                        result = classify_and_draft(email)
                        break
                    except Exception as e:
                        if attempt < 2:
                            import time
                            time.sleep(10)
                        else:
                            result = {
                                'id': email['id'],
                                'subject': email['subject'],
                                'from': email['from'],
                                'priority': 'unknown',
                                'category': 'unknown',
                                'summary': f'Failed to process: {str(e)[:80]}',
                                'draft_reply': ''
                            }
                label_id = labels.get(result['priority'])
                if label_id:
                    apply_label(service, result['id'], label_id)
                if result['priority'] == 'urgent':
                    send_slack_alert(result)
                results.append(result)

            priority_order = {'urgent': 0, 'normal': 1, 'low': 2}
            results.sort(key=lambda x: priority_order.get(x['priority'], 1))
            st.session_state.results = results
            progress.empty()
            st.success(f"✅ Triaged {len(results)} emails!")
        except Exception as e:
            st.error(f"Error: {e}")

# --- Display results ---
if st.session_state.results:
    results = st.session_state.results

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", len(results))
    col2.metric("🔴 Urgent", sum(1 for r in results if r['priority'] == 'urgent'))
    col3.metric("🟡 Normal", sum(1 for r in results if r['priority'] == 'normal'))
    col4.metric("🟢 Low", sum(1 for r in results if r['priority'] == 'low'))

    st.divider()

    # Email cards
    for i, r in enumerate(results):
        emoji = PRIORITY_EMOJI.get(r['priority'], '⚪')
        color = PRIORITY_COLOR.get(r['priority'], '#888')

        with st.expander(f"{emoji} {r['subject']} — {r['from']}", expanded=(r['priority'] == 'urgent')):
            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(f"**Priority**")
                st.markdown(f"<span style='color:{color};font-weight:bold'>{r['priority'].upper()}</span>", unsafe_allow_html=True)
                st.markdown(f"**Category**")
                st.markdown(f"`{r['category']}`")
                st.markdown(f"**From**")
                st.markdown(r['from'])
            with col2:
                st.markdown(f"**Summary**")
                st.info(r['summary'])
                st.markdown(f"**Draft Reply**")
                edited = st.text_area(
                    "Edit before sending:",
                    value=r['draft_reply'] if r['draft_reply'] else 'No reply needed.',
                    height=150,
                    key=f"draft_{i}"
                )
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("✅ Approve Draft", key=f"approve_{i}"):
                        st.success("Draft approved! (Connect Gmail send API to auto-send)")
                with col_b:
                    if st.button("🗑️ Discard", key=f"discard_{i}"):
                        st.warning("Draft discarded.")

    # Save report buttons
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save Report to File"):
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
            st.success(f"Report saved to {output_file}")
    with col2:
        if st.button("📓 Save Report to Notion"):
            with st.spinner("Saving to Notion..."):
                try:
                    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
                    url = save_report_to_notion(results, timestamp)
                    st.success(f"Notion page created!")
                    st.markdown(f"[Open in Notion]({url})")
                except Exception as e:
                    st.error(f"Notion error: {e}")

else:
    st.info("Click **Fetch & Triage Emails** in the sidebar to get started.")
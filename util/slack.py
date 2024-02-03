import json
import os
import re
import urllib.request


# Generic function to send a request to Slack API
def send_slack_request(url, data):
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    data = urllib.parse.urlencode(data).encode("ascii")
    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("Authorization", f"Bearer {bot_token}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(request) as response:
        return response.read()


# Function to update a Slack message
def update_slack_message(channel_id, timestamp, new_text, thread_ts=None):
    slack_update_url = "https://slack.com/api/chat.update"
    data = {
        "channel": channel_id,
        "ts": timestamp,
        "text": new_text
    }
    # If thread_ts is provided, add it to the data
    if thread_ts:
        data["thread_ts"] = thread_ts

    response = send_slack_request(slack_update_url, data)
    # log_to_aws(LogLevel.INFO, f'Response from Slack on updating message: {response}')
    return response


# Function to send a text response to Slack
def send_text_response(event, response_text, thread_ts=None):
    SLACK_URL = "https://slack.com/api/chat.postMessage"
    channel_id = event["event"]["channel"]
    data = {
        "token": os.environ.get("SLACK_BOT_TOKEN"),
        "channel": channel_id,
        "text": response_text,
        "link_names": True
    }
    # If thread_ts is provided, add it to the data to make the message a reply in a thread
    if thread_ts:
        data["thread_ts"] = thread_ts

    return send_slack_request(SLACK_URL, data)


# Function to fetch thread messages from Slack
def get_thread_messages(channel_id, thread_ts):
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    url = f"https://slack.com/api/conversations.replies?channel={channel_id}&ts={thread_ts}"

    request = urllib.request.Request(url, method="GET")
    request.add_header("Authorization", f"Bearer {bot_token}")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(request) as response:
        data = json.loads(response.read().decode())
        if data['ok']:
            return data['messages']
        else:
            raise Exception(f"Error fetching thread messages: {data['error']}")


def markdown_to_slack(md_text):
    # Temporary replacement for code blocks and inline code
    code_blocks = []
    inline_codes = []

    def replace_code_block(match):
        code_blocks.append(match.group(0))
        return f"CODE_BLOCK_{len(code_blocks) - 1}"

    def replace_inline_code(match):
        inline_codes.append(match.group(0))
        return f"INLINE_CODE_{len(inline_codes) - 1}"

    md_text = re.sub(r"(```.*?```)", replace_code_block, md_text, flags=re.DOTALL)
    md_text = re.sub(r"(`.+?`)", replace_inline_code, md_text)

    # Convert bold
    md_text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", md_text)
    md_text = re.sub(r"__(.+?)__", r"*\1*", md_text)

    # Convert italic
    md_text = re.sub(r"\*(.+?)\*", r"_\1_", md_text)
    md_text = re.sub(r"_(.+?)_", r"_\1_", md_text)

    # Convert strikethrough
    md_text = re.sub(r"~~(.+?)~~", r"~\1~", md_text)

    # Convert links
    md_text = re.sub(r"\[(.+?)\]\((.+?)\)", r"<\2|\1>", md_text)

    # Convert headings to bold
    md_text = re.sub(r"^#{1,6}\s*(.+)$", r"*\1*", md_text, flags=re.MULTILINE)

    # Convert ordered lists
    md_text = re.sub(r"\n(\d+)\.\s*(.+)$", r"\n\1. \2", md_text, flags=re.MULTILINE)

    # Convert bullet lists
    md_text = re.sub(r"\n\*(.+)$", r"\n- \1", md_text, flags=re.MULTILINE)
    md_text = re.sub(r"\n\+(.+)$", r"\n- \1", md_text, flags=re.MULTILINE)

    # Convert blockquotes
    md_text = re.sub(r"^>\s*(.+)$", r"_>\1_", md_text, flags=re.MULTILINE)

    # Restore code blocks and inline code
    for i, code in enumerate(code_blocks):
        md_text = md_text.replace(f"CODE_BLOCK_{i}", code)
    for i, code in enumerate(inline_codes):
        md_text = md_text.replace(f"INLINE_CODE_{i}", code)

    return md_text

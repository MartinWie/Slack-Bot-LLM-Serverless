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
def update_slack_message(channel_id, timestamp, new_text):
    SLACK_UPDATE_URL = "https://slack.com/api/chat.update"
    data = {
        "channel": channel_id,
        "ts": timestamp,
        "text": new_text
    }
    response = send_slack_request(SLACK_UPDATE_URL, data)
    # log_to_aws(LogLevel.INFO, f'Response from Slack on updating message: {response}')
    return response


# Function to send a text response to Slack
def send_text_response(event, response_text):
    SLACK_URL = "https://slack.com/api/chat.postMessage"
    channel_id = event["event"]["channel"]
    data = {
        "token": os.environ.get("SLACK_BOT_TOKEN"),
        "channel": channel_id,
        "text": response_text,
        "link_names": True
    }
    return send_slack_request(SLACK_URL, data)


def markdown_to_slack(md_text):
    # Convert bold
    md_text = re.sub(r"\*\*(.+?)\*\*", r"*\1*", md_text)
    md_text = re.sub(r"__(.+?)__", r"*\1*", md_text)

    # Convert italic
    md_text = re.sub(r"\*(.+?)\*", r"_\1_", md_text)
    md_text = re.sub(r"_(.+?)_", r"_\1_", md_text)

    # Convert inline code
    md_text = re.sub(r"`(.+?)`", r"`\1`", md_text)

    # Convert code blocks
    md_text = re.sub(r"```(.+?)```", r"```\1```", md_text)
    md_text = re.sub(r"~~~(.+?)~~~", r"```\1```", md_text)

    # Convert blockquotes
    md_text = re.sub(r"^>\s*(.+?)$", r">\1", md_text, flags=re.MULTILINE)

    # Convert links
    md_text = re.sub(r"\[(.+?)\]\((.+?)\)", r"<\2|\1>", md_text)

    # Convert headers (Markdown headers are not supported in Slack. Convert them to bold)
    md_text = re.sub(r"^#{1,6}\s*(.+)$", r"*\1*", md_text, flags=re.MULTILINE)

    return md_text

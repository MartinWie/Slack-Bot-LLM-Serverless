import json
import os

from six.moves import urllib

from util.logger import log_to_aws, LogLevel


# Function to send a text response to Slack
def send_text_response(event, response_text):
    SLACK_URL = "https://slack.com/api/chat.postMessage"
    channel_id = event["event"]["channel"]
    user = event["event"]["user"]
    bot_token = os.environ.get("SLACK_BOT_TOKEN")
    data = urllib.parse.urlencode({
        "token": bot_token,
        "channel": channel_id,
        "text": response_text,
        "user": user,
        "link_names": True
    })
    data = data.encode("ascii")
    request = urllib.request.Request(SLACK_URL, data=data, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")
    res = urllib.request.urlopen(request).read()
    log_to_aws(LogLevel.INFO, f'Response from Slack: {res}')


def lambda_handler(event, context):
    log_to_aws(LogLevel.INFO, "Lambda function invoked!")
    log_to_aws(LogLevel.INFO, f"Received event: {event}")

    # Check if 'body' exists in the event
    if 'body' in event:
        # Parse the event body from JSON
        body = json.loads(event['body'])

        if 'type' in body and body['type'] == 'url_verification':
            log_to_aws(LogLevel.INFO, "URL verification event received.")
            if 'challenge' in body:
                challenge = body['challenge']
                log_to_aws(LogLevel.INFO, f"Responding with challenge: {challenge}")
                return {
                    "statusCode": 200,
                    "headers": {
                        "Content-Type": "text/plain"
                    },
                    "body": challenge
                }

        elif 'type' in body and body['type'] == 'event_callback':
            if 'event' in body and 'type' in body['event'] and body['event']['type'] == 'message':
                message_text = body['event'].get('text', '')
                if '<@U06GBCG8E9F>' in message_text or 'Leela' in message_text:
                    send_text_response(body, "ok")
                    return {
                        "statusCode": 200,
                        "body": "Response sent"
                    }

    return {
        "statusCode": 200,
        "body": "Event type not supported"
    }

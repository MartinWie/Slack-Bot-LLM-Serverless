import os

from six.moves import urllib

from util.ai_util import openai_request, print_and_return_streamed_response
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
    log_to_aws(LogLevel.INFO, "Async Processor Lambda function invoked!")
    log_to_aws(LogLevel.INFO, f"Event: {event}")

    # Check if 'event' exists and process it
    if 'event' in event:
        # Your existing Slack processing logic here
        message_text = event['event'].get('text', '')
        if '<@U06GBCG8E9F>' in message_text or 'Leela' in message_text:
            response = openai_request(message_text)
            answer = print_and_return_streamed_response(response)
            send_text_response(event, answer)

    return {
        "statusCode": 200,
        "body": "Async processing completed"
    }
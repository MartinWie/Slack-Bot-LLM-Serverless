import json
import os
import urllib.request

from util.ai_util import openai_request
from util.logger import log_to_aws, LogLevel


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
    log_to_aws(LogLevel.INFO, f'Response from Slack on updating message: {response}')
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


def lambda_handler(event, context):
    try:
        log_to_aws(LogLevel.INFO, "Async Processor Lambda function invoked!")
        log_to_aws(LogLevel.INFO, f"Event: {event}")

        # Parse the incoming event body (assuming it's JSON)
        event_body = json.loads(event.get('body', '{}'))

        # Check if 'event' exists in the parsed body and process it
        if 'event' in event_body:
            # Check if the event is from a bot
            if 'bot_id' in event_body['event']:
                log_to_aws(LogLevel.INFO, "Event from a bot, skipping processing")
                return {
                    "statusCode": 200,
                    "body": "Event from bot, no action taken"
                }

            message_text = event_body['event'].get('text', '')
            channel_id = event_body['event']['channel']
            # Check if the message mentions the bot (assumed bot ID: 'U06GBCG8E9F' or name 'Leela')
            if '<@U06GBCG8E9F>' in message_text or 'Leela' in message_text:
                # Send "Thinking..." message and process the message
                thinking_message_response = send_text_response(event_body, "Thinking...")
                thinking_message_ts = json.loads(thinking_message_response)['ts']

                response = openai_request(message_text)
                answer = print_and_return_streamed_response(response, channel_id, thinking_message_ts)

                # Final update to replace "Thinking..." with the actual response
                update_slack_message(channel_id, thinking_message_ts, answer)

        return {
            "statusCode": 200,
            "body": "Async processing completed"
        }

    except Exception as e:
        log_to_aws(LogLevel.ERROR, f"Error occurred: {e}")
        send_text_response(event, "Leela müde, Leela schlafen")
        return {
            "statusCode": 500,
            "body": "Error occurred in processing"
        }


def print_and_return_streamed_response(response, channel_id, message_ts):
    final_output = ""
    for event in response:
        if event['choices'][0]['delta'].get('content') is not None:
            event_text = event['choices'][0]['delta']['content']
            final_output += event_text
            update_slack_message(channel_id, message_ts, final_output)

    return final_output

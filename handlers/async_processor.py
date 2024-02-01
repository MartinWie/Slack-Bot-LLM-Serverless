import json

from util.ai_util import openai_request, prepend_conversation_history, CURRENT_GLOBAL_TOKEN_LIMIT
from util.logger import log_to_aws, LogLevel
from util.slack import send_text_response, update_slack_message, markdown_to_slack, get_thread_messages


def lambda_handler(event, context):
    try:
        log_to_aws(LogLevel.INFO, "Async Processor Lambda function invoked!")
        # log_to_aws(LogLevel.INFO, f"Event: {event}")

        # Parse the incoming event body (assuming it's JSON)
        event_body = json.loads(event.get('body', '{}'))

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
            thread_ts = event_body['event'].get('thread_ts', None) or event_body['event'].get('ts', None)

            # Check if the message mentions the bot
            if '<@U06GBCG8E9F>' in message_text or 'Leela' in message_text or 'leela' in message_text:
                # Initialize the list to store conversation strings
                conversation_history = []

                # Fetch all messages in the thread
                thread_messages = get_thread_messages(channel_id, thread_ts)
                for message in thread_messages:
                    # Add each message and its sender to the conversation history
                    sender = "Bot" if 'bot_id' in message else "Human"
                    conversation_history.append(f"{sender} input: {message.get('text', '')}")

                # Use the helper function to prepend conversation history
                prepended_input = prepend_conversation_history(
                    conversation_history,
                    message_text,
                    CURRENT_GLOBAL_TOKEN_LIMIT / 4
                )

                # Send "Thinking..." message and process the message
                thinking_message_response = send_text_response(event_body, "Thinking...", thread_ts=thread_ts)
                thinking_message_ts = json.loads(thinking_message_response)['ts']

                response = openai_request(prepended_input)
                answer = update_slack_message_and_return_streamed_response(
                    response,
                    channel_id,
                    thinking_message_ts,
                    thread_ts
                )

                # Final update to replace "Thinking..." with the actual response
                update_slack_message(channel_id, thinking_message_ts, markdown_to_slack(answer), thread_ts)

        return {
            "statusCode": 200,
            "body": "Async processing completed"
        }

    except Exception as e:
        log_to_aws(LogLevel.ERROR, f"Error occurred: {e}")
        send_text_response(event, "Leela müde, Leela schlafen", thread_ts=thread_ts)
        return {
            "statusCode": 500,
            "body": "Error occurred in processing"
        }


def update_slack_message_and_return_streamed_response(response, channel_id, message_ts, thread_ts=None):
    final_output = ""

    for event in response:
        if event['choices'][0]['delta'].get('content') is not None:
            event_text = event['choices'][0]['delta']['content']

            for char in event_text:
                final_output += char

                # Check for sentence-ending punctuation or new lines
                if char in ['.', '!', '?', ','] or char == '\n':
                    update_slack_message(channel_id, message_ts, markdown_to_slack(final_output.strip()), thread_ts)

    update_slack_message(channel_id, message_ts, markdown_to_slack(final_output.strip()), thread_ts)

    return final_output

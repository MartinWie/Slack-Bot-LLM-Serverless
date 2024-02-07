import json
import re

from util.ai_util import openai_request, prepend_conversation_history, CURRENT_GLOBAL_TOKEN_LIMIT, summarize_webpage, \
    get_intent, google_search
from util.logger import log_to_aws, LogLevel
from util.slack import send_text_response, update_slack_message, markdown_to_slack, get_thread_messages


def lambda_handler(event, context):
    log_to_aws(LogLevel.INFO, "Async Processor Lambda function invoked!")
    # log_to_aws(LogLevel.INFO, f"Event: {event}")

    allowed_intends = ["Websearch", "Chat"]

    # Parse the incoming event body (assuming it's JSON)
    event_body = json.loads(event.get('body', '{}'))
    try:

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

                # Check for URLs in the message text
                urls = re.findall(r'https?://\S+', message_text)
                # If URLs exist, add them to a list
                url_list = []
                if urls:
                    url_list.extend(urls)

                url_data = ""

                current_message_ts = None

                if len(url_list) > 0:
                    message_response = send_text_response(
                        event_body,
                        "Reading URL...",
                        thread_ts=thread_ts
                    )
                    current_message_ts = json.loads(message_response)['ts']
                    for url in url_list:
                        url_data += "\n" + summarize_webpage(url)

                loading_message_response = None
                loading_message_text = "Thinking..."

                if current_message_ts is not None:
                    loading_message_response = update_slack_message(
                        channel_id,
                        current_message_ts,
                        loading_message_text,
                        thread_ts
                    )
                else:
                    loading_message_response = send_text_response(
                        event_body,
                        loading_message_text,
                        thread_ts=thread_ts
                    )

                thinking_message_ts = json.loads(loading_message_response)['ts']

                # Get intet
                intent = get_intent(allowed_intends, message_text)

                if intent is not None and intent == 'Websearch':
                    update_slack_message(
                        channel_id,
                        thinking_message_ts,
                        "Searching the web...",
                        thread_ts
                    )
                    websearch_links = google_search(message_text)
                    for url in websearch_links:
                        url_data += "\n Websearch results for the user question: " + summarize_webpage(url)

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

                # Get final response
                response = openai_request(prepended_input + url_data)

                if response is None:
                    raise ValueError("The response from OpenAI was None.")

                answer = update_slack_message_and_return_streamed_response(
                    response,
                    channel_id,
                    thinking_message_ts,
                    thread_ts
                )

                update_slack_message(channel_id, thinking_message_ts, markdown_to_slack(answer), thread_ts)

        return {
            "statusCode": 200,
            "body": "Async processing completed"
        }

    except Exception as e:
        log_to_aws(LogLevel.ERROR, f"Error occurred: {e}")
        if 'event' in event_body:
            send_text_response(event_body, "Leela müde, Leela schlafen", thread_ts=thread_ts)
        return {
            "statusCode": 500,
            "body": "Error occurred in processing"
        }


def update_slack_message_and_return_streamed_response(response, channel_id, message_ts, thread_ts=None):
    final_output = ""

    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            event_text = chunk.choices[0].delta.content

            for char in event_text:
                final_output += char

                # Check for sentence-ending punctuation or new lines
                if char in ['.', '!', '?', ','] or char == '\n':
                    update_slack_message(channel_id, message_ts, markdown_to_slack(final_output.strip()), thread_ts)

    update_slack_message(channel_id, message_ts, markdown_to_slack(final_output.strip()), thread_ts)

    return final_output

import json
import string
import sys

import openai
import tiktoken

from util.logger import log_to_aws, LogLevel


def openai_request(
        prompt: str,
        model: str = "gpt-4-0125-preview",
        temperature: float = 0.3,
        token_limit: int = 120000
):
    if get_token_amount_from_string(prompt) > token_limit:
        log_to_aws(
            LogLevel.INFO,
            f"Token amount of {get_token_amount_from_string(prompt)} is to big. Stay below {token_limit}!"
        )
        exit()
    try:
        response = openai.ChatCompletion.create(
            model=model,
            temperature=temperature,
            stream=True,
            messages=[
                {"role": "system",
                 "content": "Help answer user questions, provide solutions step by step."},
                {"role": "user", "content": prompt}
            ]
        )
        return response

    except openai.error.APIError as e:
        log_to_aws(LogLevel.INFO, f"Error with the OpenAI API. Details:{e}")
        return None

    except openai.error.RateLimitError as e:
        log_to_aws(LogLevel.INFO, f"Rate limit exceeded. Please wait before making further requests. Details: {e}")
        return None

    except openai.error.APIConnectionError as e:
        log_to_aws(LogLevel.INFO, f"Connection error. Please check your internet connection. Details:{e}")
        return None

    except openai.error.InvalidRequestError as e:
        log_to_aws(LogLevel.INFO, f"Invalid request. Check your parameters. Details:{e}")
        return None

    except openai.error.AuthenticationError as e:
        log_to_aws(LogLevel.INFO, f"Authentication error. Please check your OpenAI API key. Details:{e}")
        return None

    except openai.error.ServiceUnavailableError as e:
        log_to_aws(LogLevel.INFO, f"OpenAI service is currently unavailable. Please try again later. Details:{e}")
        return None

    except Exception as e:
        log_to_aws(LogLevel.INFO, f"An unexpected error occurred:{e}")
        return None


def print_and_return_streamed_response(response):
    # create variables to collect the stream of events
    collected_events = []
    final_output = ""
    # iterate through the stream of events
    for event in response:
        collected_events.append(event)  # save the event response
        if event['choices'][0]['delta'].get('content') is not None:
            event_text = event['choices'][0]['delta']['content']  # extract the text
            sys.stdout.write(event_text)
            sys.stdout.flush()  # ensures output is displayed immediately
            final_output += event_text
    return final_output


# Function to prepend as much of the conversation history as possible to the input string
def prepend_conversation_history(conversation_history, input_string, token_limit):
    current_tokens = get_token_amount_from_string(input_string)
    prepended_history = ""

    for entry in reversed(conversation_history):
        entry_tokens = get_token_amount_from_string(entry)
        if current_tokens + entry_tokens <= token_limit:
            prepended_history = entry + prepended_history
            current_tokens += entry_tokens
        else:
            break  # Stop if we cannot add more without exceeding the token limit

    return prepended_history + input_string  # Return the combined string


def get_token_amount_from_string(text: string):
    # cl100k_base is for gpt-4 and gpt-3.5-turbo
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def prompt_to_text(prompt: string):
    return openai_request(prompt)


def prompt_to_json(prompt: string):
    return parse_openai_return_json_string(
        openai_request(
            prompt
        )
    )


def parse_openai_return_json_string(text: string):
    try:
        json_data = json.loads(text)
        return json_data
    except json.JSONDecodeError as e:
        log_to_aws(LogLevel.INFO, f"Invalid JSON data: {e}")

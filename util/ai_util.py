import json
import string

import openai
import requests
import tiktoken
from bs4 import BeautifulSoup
from openai import OpenAI

from config.config import OPENAI_API_KEY
from util.logger import log_to_aws, LogLevel

CURRENT_GLOBAL_TOKEN_LIMIT = 120000


def openai_request(
        prompt: str,
        model: str = "gpt-4-0125-preview",
        temperature: float = 0.3,
        token_limit: int = CURRENT_GLOBAL_TOKEN_LIMIT,
        stream_response: bool = True
):
    if get_token_amount_from_string(prompt) > token_limit:
        log_to_aws(
            LogLevel.INFO,
            f"Token amount of {get_token_amount_from_string(prompt)} is to big. Stay below {token_limit}!"
        )
        exit()

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        response = client.chat.completions.create(
            model=model,
            temperature=temperature,
            messages=[
                {"role": "system",
                 "content": "Help answer user questions, provide solutions step by step. Keep it short and concise."},
                {"role": "user", "content": prompt}
            ],
            stream=stream_response
        )
        return response

    except openai.APIError as e:
        log_to_aws(LogLevel.ERROR, f"Error with the OpenAI API. Details:{e}")
        return None

    except openai.RateLimitError as e:
        log_to_aws(LogLevel.ERROR, f"Rate limit exceeded. Please wait before making further requests. Details: {e}")
        return None

    except openai.AuthenticationError as e:
        log_to_aws(LogLevel.ERROR, f"Authentication error. Please check your OpenAI API key. Details:{e}")
        return None

    except Exception as e:
        log_to_aws(LogLevel.ERROR, f"An unexpected error occurred:{e}")
        return None


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


def summarize_webpage(url: str):
    # Fetch the content of the webpage
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException as e:
        log_to_aws(LogLevel.ERROR, f"Error fetching URL content: {e}")
        return "Error fetching URL content."

    # Parse the webpage content
    soup = BeautifulSoup(response.content, 'html.parser')
    # Extract text from the webpage
    text = ' '.join([p.get_text() for p in soup.find_all('p')])

    # Check if text is too long and trim if necessary
    if len(text) > CURRENT_GLOBAL_TOKEN_LIMIT:
        text = text[:CURRENT_GLOBAL_TOKEN_LIMIT - 100]

    # Create a prompt for summarization
    summary_prompt = f"Summarize the following content from a webpage: {text}"

    # Use openai_request to get the summary
    summary_response = openai_request(summary_prompt, stream_response=False)

    # Extract and return the summary
    if summary_response:
        return f"Here is the summary for {url}: " + summary_response.choices[0].message.content
    else:
        return "Failed to get a summary for website..."

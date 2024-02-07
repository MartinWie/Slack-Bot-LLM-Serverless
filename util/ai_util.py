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
                 "content": "Help answer user questions short and concise, provide solutions step by step. Keep it "
                            "short and concise."
                            "When a user asks for info about an URL dont worry about it your input automatically "
                            "includes the websites content. Dont Mention your training data date and trust that the "
                            "context contains all relevant information! Keep your answers short and concise."},
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


def get_intent(possible_intents: list, text: str):
    # Good starting intents: Websearch,InternalWiki,Chat
    concatenated_intents = ','.join(possible_intents)

    # Check if text is too long and trim if necessary
    if len(text) > CURRENT_GLOBAL_TOKEN_LIMIT:
        text = text[:CURRENT_GLOBAL_TOKEN_LIMIT - 100]

    # Create a prompt for intent gathering
    intent_prompt = f"You need to detect the intended action. Here is a list of all possible intents: {concatenated_intents}. Only respond with the intend you believe the users has. Just respond with this one word, no more and no less. Here is the text that needs to be checked: {text}"

    # Use openai_request to get the intent
    response = openai_request(intent_prompt, stream_response=False)

    # Extract and return the intet
    intent = response.choices[0].message.content

    log_to_aws(LogLevel.INFO, f"Checked intent and found:{intent}")

    if intent in possible_intents:
        return intent
    else:
        return None


def google_search(query: str):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
    }
    url = f'https://www.google.com/search?q={query}&ie=utf-8&oe=utf-8&num=10'
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        allData = soup.find_all("div", {"class": "g"})
        links = []

        for data in allData:
            link_element = data.find('a', href=True)
            if link_element:
                link = link_element['href']
                links.append(link)
                if len(links) == 1:
                    break
        log_to_aws(LogLevel.INFO, f"Checked web and found:{links}")
        return links
    else:
        return None


def duckduckgo_search(query: str):
    headers = {'User-Agent': 'Mozilla/5.0'}
    params = {'q': query}
    response = requests.get("https://duckduckgo.com/html/", params=params, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        for link in soup.find_all('a', href=True, class_='result__url'):
            redirect_url = link['href']
            if redirect_url.startswith('//'):
                redirect_url = 'https:' + redirect_url
            final_url = requests.get(redirect_url, headers=headers, allow_redirects=True).url
            links.append(final_url)
            if len(links) == 1:
                break
        log_to_aws(LogLevel.INFO, f"Checked web and found:{links}")
        return links
    else:
        return None

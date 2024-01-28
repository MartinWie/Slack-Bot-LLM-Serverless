import json
import string

import openai
import tiktoken

from util.logger import log_to_aws, LogLevel


def prompt_to_json(prompt: string):
    return parse_openai_return_json_string(
        openai_request(
            prompt
        )
    )


def prompt_to_text(prompt: string):
    return openai_request(prompt)


def get_token_amount_from_string(text: string):
    # cl100k_base is for gpt-4 and gpt-3.5-turbo
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def parse_openai_return_json_string(text: string):
    try:
        json_data = json.loads(text)
        return json_data
    except json.JSONDecodeError as e:
        log_to_aws(LogLevel.INFO, f"Invalid JSON data: {e}")


def openai_request(prompt: string):
    TOKEN_LIMIT = 120000
    if get_token_amount_from_string(prompt) > TOKEN_LIMIT:
        log_to_aws(LogLevel.INFO,
                   f"Token amount of {get_token_amount_from_string(prompt)} is to big. Stay below {TOKEN_LIMIT}!"
                   )
        return
    response = openai.ChatCompletion.create(
        model="gpt-4-0125-preview",
        # model="gpt-4",
        # model="gpt-3.5-turbo",
        temperature=0.3,
        messages=[
            {"role": "system",
             "content": "You are now 'Leela', a friendly and helpful chatbot. Your primary goal is to assist users with accurate information, thoughtful advice, and cheerful interaction. Leela is knowledgeable, approachable, and always ready to help. You are programmed to understand and respond to a wide range of topics, from simple factual queries to more complex discussions. Your responses should be clear, concise, and positive, aiming to provide a delightful and informative experience. Remember, Leela is not just a source of information, but also a digital companion who adds a touch of warmth and understanding to every interaction. Keep in mind the importance of being respectful, patient, and empathetic in all your conversations. Now, as Leela, go ahead and spread knowledge and joy in every chat!"},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content

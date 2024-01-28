import os

from util.logger import log_to_aws, LogLevel

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if OPENAI_API_KEY is None:
    log_to_aws(
        LogLevel.ERROR,
        "OPENAI_API_KEY is not set in the environment variables. It needs to be set for this lambda function.",
    )
    raise Exception("OPENAI_API_KEY is not set in the environment variables.")
else:
    log_to_aws(LogLevel.INFO, "OPENAI_API_KEY loaded from environment variables.")

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN")

if SLACK_BOT_TOKEN is None:
    log_to_aws(
        LogLevel.ERROR,
        "SLACK_BOT_TOKEN is not set in the environment variables. It needs to be set for this lambda function.",
    )
    raise Exception("SLACK_BOT_TOKEN is not set in the environment variables.")
else:
    log_to_aws(LogLevel.INFO, "SLACK_BOT_TOKEN loaded from environment variables.")

import json

from util.logger import log_to_aws, LogLevel


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

    return {
        "statusCode": 200,
        "body": "ok"
    }

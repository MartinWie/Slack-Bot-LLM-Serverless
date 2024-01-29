from util.logger import log_to_aws, LogLevel


def lambda_handler(event, context):
    log_to_aws(LogLevel.INFO, "Lambda function invoked!")

    if 'type' in event and event['type'] == 'url_verification':
        log_to_aws(LogLevel.INFO, "URL verification event received.")
        if 'challenge' in event:
            challenge = event['challenge']
            log_to_aws(LogLevel.INFO, f"Responding with challenge: {challenge}")
            return {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "text/plain"
                },
                "body": challenge
            }
        else:
            log_to_aws(LogLevel.ERROR, "No challenge in event.")
            return {
                "statusCode": 400,
                "body": "Bad Request"
            }

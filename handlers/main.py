import hashlib
import hmac
import json
import os
import time

import boto3

from util.logger import log_to_aws, LogLevel

# Lambda client for invoking another function
lambda_client = boto3.client('lambda')

SLACK_SIGNING_SECRET = os.environ.get("SLACK_SIGNING_SECRET")


def is_request_valid(slack_signature, timestamp, body):
    # Form the basestring as stated by Slack
    basestring = f"v0:{timestamp}:{body}"

    # Create a new HMAC "signature", and return a string in hex format
    my_signature = 'v0=' + hmac.new(
        str(SLACK_SIGNING_SECRET).encode('utf-8'),
        basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # Compare the signatures
    if hmac.compare_digest(my_signature, slack_signature):
        # Check if the timestamp is within 300 seconds (5 minutes) of current time
        if abs(time.time() - int(timestamp)) < 300:
            return True
    return False


def lambda_handler(event, context):
    log_to_aws(LogLevel.INFO, "Main Lambda function invoked!")

    # Extract Slack signature and timestamp from headers
    slack_signature = event['headers'].get('X-Slack-Signature')
    slack_timestamp = event['headers'].get('X-Slack-Request-Timestamp')

    # Verify request
    if not is_request_valid(slack_signature, slack_timestamp, event['body']):
        log_to_aws(LogLevel.ERROR, "Invalid Slack signature.")
        return {
            "statusCode": 403,
            "body": json.dumps("Invalid request")
        }

    service_name = os.environ.get("SERVICE_NAME")
    stage = os.environ.get("STAGE")
    async_processor_function_name = f"{service_name}-{stage}-AsyncProcessor"

    # Asynchronously invoke the async_processor Lambda function
    try:
        lambda_client.invoke(
            FunctionName=async_processor_function_name,
            InvocationType='Event',  # 'Event' for asynchronous invocation
            Payload=json.dumps(event)
        )
        log_to_aws(LogLevel.INFO, "Successfully invoked async processor.")
    except Exception as e:
        log_to_aws(LogLevel.ERROR, f"Error invoking async processor: {e}")

    # Return response immediately
    return {
        "statusCode": 200,
        "body": json.dumps("Request received, processing started")
    }

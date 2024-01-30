import json
import os

import boto3

from util.logger import log_to_aws, LogLevel

# Lambda client for invoking another function
lambda_client = boto3.client('lambda')


def lambda_handler(event, context):
    log_to_aws(LogLevel.INFO, "Main Lambda function invoked!")

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

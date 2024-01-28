from util.logger import log_to_aws, LogLevel


def lambda_handler(event, context):
    log_to_aws(LogLevel.INFO, f"Lambda function invoced!")

    log_to_aws(LogLevel.INFO, f"Lambda function finished!")
    return {"response": "ok"}

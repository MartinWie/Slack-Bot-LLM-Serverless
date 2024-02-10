from unittest.mock import MagicMock

import boto3
import pytest

from handlers.main import lambda_handler


@pytest.mark.unit
def test_lambda_handler():
    # Create a mock Lambda client
    lambda_client = boto3.client('lambda')
    lambda_client.invoke = MagicMock(return_value={'Payload': 'mock_payload'})

    event = {
        'headers': {
            'X-Slack-Signature': 'test_signature',
            'X-Slack-Request-Timestamp': 'test_timestamp'
        },
        'body': 'test_body'
    }

    context = {}

    result = lambda_handler(event, context)

    assert result["body"] is not None

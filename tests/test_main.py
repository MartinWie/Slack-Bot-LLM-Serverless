import pytest

from handlers.main import lambda_handler


@pytest.mark.unit
def test_lambda_handler():
    event = {}  # Define your test event here
    context = None  # Define your test context here

    result = lambda_handler(event, context)

    # Add your assertions to check the output of the lambda_handler function
    assert result["body"] is not None

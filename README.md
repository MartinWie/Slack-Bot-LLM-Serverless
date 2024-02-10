# Slack-Bot-LLM-Serverless

[![Open Source](https://badges.frapsoft.com/os/v1/open-source.svg?v=103)](https://opensource.org/)

![Slack-LLM-Bot](https://github.com/MartinWie/Slack-Bot-LLM-Serverless/blob/main/slack-llm-bot.png?raw=true)

A Slack bot with LLM support, using the Slack Events API, AWS Lambda, written in Python, utilizing the Serverless
framework.

## Initial Development Setup

Before you start, make sure to install all requirements!

Install serverless

```
brew install serverless

serverless plugin install -n serverless-pydeps
```

# Creating virtual environment + install dependencies

```
python -m venv venv
source venv/bin/activate  # For Unix-based systems
venv\Scripts\activate  # For Windows

pip install -r requirements.txt
pip install -r requirements-dev.txt # For local testing
```

Do not forget to also add the venv in your pycharm interpreter:
Settings -> Python Interpreter -> Add Interpreter -> Virtualenv Environment -> Existing

## Management of Python Dependencies in Lambda

This project uses the serverless-pydeps plugin to manage Python dependencies.
You can add dependencies to the requirements.txt file located in the project root directory.
During deployment, the plugin will package the dependencies with the function.

## IAM permission setup

The serverless.yaml file contains IAM role statements required for the Lambda function.
The IAM role allows the function to access AWS services such as CloudWatch Logs, and AWS Systems Manager Parameter
Store.
The relevant role with all defined permissions is created during deployment.

## Deploying the Function

```
sls deploy --verbose --config serverless.yaml --stage Dev

```

Stage needs the environment, you want to deploy to.
For example "Dev", "Test" and "Prod"

This will package and deploy your Lambda function to AWS.

## Running the lambda function locally

This can be useful for debugging!
Disclaimer: This will use your local aws cli user, make sure you have sufficient permissions!

```
sls invoke local -f main --stage Dev
```

Replace main with the name of your function if you have changed it in the serverless.yaml file.

## Monitoring and Logging

The Lambda function is configured to log messages to Amazon CloudWatch Logs.
You can view the logs in the AWS Management Console or use the AWS CLI to retrieve log events.

One amazing feature of this setup is to view the live logs of deployed functions:

```
sls logs -f main -t --stage Dev 
```

Replace "main" with the name of your function if you have changed it in the serverless.yaml file. The -t flag will
enable tailing the logs in real-time.

The utils/logger.py module contains the log_to_aws function, which you can use to log messages of various log levels (
e.g., LogLevel.INFO, LogLevel.DEBUG, etc.).
You can import and use this function in your Lambda handler to log custom messages.

## Removing the Deployed Function

1) Open the AWS web console
2) Browse to CloudFormation
3) Find your "Stack" and delete it

## Troubleshooting Common Issues

If you encounter issues during deployment or while running your Lambda function, consider the following common causes
and solutions:

1) Missing or incorrect IAM permissions: Ensure that the IAM role statements in the serverless.yaml file include all
   necessary permissions for the AWS services your function is using.
2) Dependency issues: Make sure that all required dependencies are listed in the requirements.txt file and installed in
   your virtual environment. Verify that the serverless-pydeps plugin is properly configured in the serverless.yaml
   file.
3) Invalid event sources: Double-check the event sources specified in the serverless.yaml file for your Lambda function.
   Make sure they are correctly configured and use the appropriate syntax for the Serverless Framework.
4) Errors in your Lambda function: Check the logs in Amazon CloudWatch Logs for any error messages or stack traces that
   can help you debug issues in your Lambda function. Use the log_to_aws function from the utils/logger.py module to log
   custom messages that can help you identify issues.
5) Resource limits: Monitor the usage of resources such as memory, CPU, and execution time for your Lambda function.
   Adjust the settings in the serverless.yaml file as needed to ensure your function has enough resources to run
   successfully.

## Testing

Our default for testing is the python package pytest.

### Run existing tests

To run all tests, use the following command in your project root:

```
pytest
```

To run specific tests based on their markers, use the following command:

```
pytest -m <marker_name>

# Current tests have the tags "unit" and "integration" (They are defined in our pytest.ini)

# To run only unit tests, just run:
pytest -m unit

```

### Add new tests

1) Create a test file for your respective handler in our "tests" folder. The naming convention is test_<handlername> (
   main.py -> test_main.py)
2) In this file you create a function and add the Python decorator (annotations) @pytest.mark.<marker_name>. We
   currently have two markers.

## Todos's

- Verify that request are sent form Slack (serverless function auth)
- Improve websearch by generating a more precise question for the search(include history data to come up with a search
  query)
- Add marker for web search responses "\[Web-Search]"
- Intention implementation: Confluence content
  search(https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-search/)
- Refactor / cleanup "async_processor.py"
- Intention implementation: Image generation
- Intention implementation: create ticket
- Implement special commands for prompts(move web search into this)?
- Add support for external knowledgebase(e.g. Confluence)
- full rewrite Readme.md
- Introduce env var file vs Parameterstore reading + fix Env var check in main
- Switch to Slack SDK?
- Add support for other LLMs.

## Support me :heart: :star: :money_with_wings:

If this project provided value, and you want to give something back, you can give the repo a star or support by buying
me a coffee.

<a href="https://buymeacoffee.com/MartinWie" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-blue.png" alt="Buy Me A Coffee" width="170"></a>

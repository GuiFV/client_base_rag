from aws_cdk import (
    aws_lambda as lambda_,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    Duration,
    Stack,
    CfnOutput,
)
from constructs import Construct


class ClientBaseRagStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Fetch the secrets from AWS Secrets Manager
        openai_secret = secretsmanager.Secret.from_secret_name_v2(
            self, "OpenAIKey", "openai-api-key"
        )

        session_secret_key = secretsmanager.Secret.from_secret_name_v2(
            self, "SessionSecretKey", "app-session-secret-key"
        )

        # Create a Lambda function to run a Flask app
        lambda_function = lambda_.Function(self, "FlaskLambda",
                                           runtime=lambda_.Runtime.PYTHON_3_9,
                                           handler="lambda_function.handler",
                                           code=lambda_.Code.from_asset("lambda"),  # Bundled dependencies
                                           timeout=Duration.seconds(30),
                                           environment={
                                               'OPENAI_SECRET_ARN': openai_secret.secret_arn,
                                               'SESSION_SECRET_KEY_ARN': session_secret_key.secret_arn
                                           })

        # Grant Lambda function permissions to read the secrets
        openai_secret.grant_read(lambda_function)
        session_secret_key.grant_read(lambda_function)

        # Enable function URL for the Lambda function
        function_url = lambda_function.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE,
        )

        # Output the Lambda Function URL for the Flask app
        CfnOutput(self, "LambdaFunctionURL",
                  description="URL for the Flask Lambda function",
                  value=function_url.url)

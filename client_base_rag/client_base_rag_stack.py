from aws_cdk import (
    aws_lambda as lambda_,
    Duration,
    Stack,
    CfnOutput,
)
from constructs import Construct


class ClientBaseRagStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create a Lambda function to run a Flask app
        lambda_function = lambda_.Function(self, "FlaskLambda",
                                           runtime=lambda_.Runtime.PYTHON_3_9,
                                           handler="lambda_function.handler",
                                           code=lambda_.Code.from_asset("lambda"),  # Bundled dependencies
                                           timeout=Duration.seconds(30))

        # Enable function URL for the Lambda function
        function_url = lambda_function.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE,
        )

        # Output the Lambda Function URL for the Flask app
        CfnOutput(self, "LambdaFunctionURL",
                  description="URL for the Flask Lambda function",
                  value=function_url.url)

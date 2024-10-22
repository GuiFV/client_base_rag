from aws_cdk import (
    aws_lambda as lambda_,
    aws_secretsmanager as secretsmanager,
    aws_iam as iam,
    aws_s3 as s3,
    Duration,
    Stack,
    CfnOutput,
    RemovalPolicy,
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

        # Create an S3 bucket with a lifecycle rule to delete objects after 24 hours
        s3_bucket = s3.Bucket(self,
                              "ClientBaseRagBucket",
                              lifecycle_rules=[
                                  s3.LifecycleRule(
                                      expiration=Duration.hours(24),
                                  )
                              ],
                              removal_policy=RemovalPolicy.DESTROY,  # Correct import
                              auto_delete_objects=True
                              # Ensure bucket contents are deleted when the bucket is destroyed
                              )

        # Create a Lambda function to run a Flask app
        lambda_function = lambda_.Function(self, "FlaskLambda",
                                           runtime=lambda_.Runtime.PYTHON_3_9,
                                           handler="lambda_function.handler",
                                           code=lambda_.Code.from_asset("lambda"),  # Bundled dependencies
                                           timeout=Duration.seconds(60),  # Increased timeout to 60 seconds
                                           memory_size=256,  # Optionally increased memory allocation
                                           environment={
                                               'OPENAI_SECRET_ARN': openai_secret.secret_arn,
                                               'SESSION_SECRET_KEY_ARN': session_secret_key.secret_arn,
                                               'BUCKET_NAME': s3_bucket.bucket_name
                                               # Added S3 bucket name to the environment
                                           })

        # Grant Lambda function permissions to read the secrets
        openai_secret.grant_read(lambda_function)
        session_secret_key.grant_read(lambda_function)

        # Grant Lambda function permissions to interact with the S3 bucket
        s3_bucket.grant_read_write(lambda_function)

        # Enable function URL for the Lambda function
        function_url = lambda_function.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE,
        )

        # Output the Lambda Function URL for the Flask app
        CfnOutput(self, "LambdaFunctionURL",
                  description="URL for the Flask Lambda function",
                  value=function_url.url)

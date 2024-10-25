import aws_cdk as core
import aws_cdk.assertions as assertions
from client_base_rag.client_base_rag_stack import ClientBaseRagStack


def get_template():
    """Helper function to generate the CloudFormation template from the stack."""
    app = core.App()
    stack = ClientBaseRagStack(app, "ClientBaseRagStack")
    return assertions.Template.from_stack(stack)


def test_s3_bucket_created():
    """Ensure an S3 bucket is created."""
    template = get_template()
    template.resource_count_is("AWS::S3::Bucket", 1)


def test_s3_bucket_properties():
    """Validate the properties of the S3 bucket."""
    template = get_template()
    template.has_resource_properties("AWS::S3::Bucket", {
        "LifecycleConfiguration": {
            "Rules": [{
                "ExpirationInDays": 1,
                "Status": "Enabled"
            }]
        }
    })


def test_lambda_functions_created():
    """Ensure the correct number of Lambda functions are created."""
    template = get_template()
    template.resource_count_is("AWS::Lambda::Function", 2)


def test_lambda_properties():
    """Validate the properties of the Flask Lambda function."""
    template = get_template()
    template.has_resource_properties("AWS::Lambda::Function", {
        "Handler": "lambda_function.handler",
        "Runtime": "python3.9",
        "Timeout": 60,
        "MemorySize": 256,
        "Environment": {
            "Variables": {
                "OPENAI_SECRET_ARN": {"Fn::Join": ["", ["arn:", {"Ref": "AWS::Partition"}, ":secretsmanager:",
                                                        {"Ref": "AWS::Region"}, ":", {"Ref": "AWS::AccountId"},
                                                        ":secret:openai-api-key"]]},
                "SESSION_SECRET_KEY_ARN": {"Fn::Join": ["", ["arn:", {"Ref": "AWS::Partition"}, ":secretsmanager:",
                                                             {"Ref": "AWS::Region"}, ":", {"Ref": "AWS::AccountId"},
                                                             ":secret:app-session-secret-key"]]},
                "BUCKET_NAME": {"Ref": "ClientBaseRagBucket253728B3"}
            }
        }
    })


def test_lambda_function_url_created():
    """Ensure a Lambda Function URL is created."""
    template = get_template()
    template.resource_count_is("AWS::Lambda::Url", 1)


def test_no_secrets_created():
    """Ensure no SecretsManager secrets are created."""
    template = get_template()
    template.resource_count_is("AWS::SecretsManager::Secret", 0)


def test_iam_roles_created():
    """Ensure the correct number of IAM roles are created."""
    template = get_template()
    template.resource_count_is("AWS::IAM::Role", 2)


def test_iam_policy_created():
    """Ensure the correct IAM policy is created."""
    template = get_template()
    template.resource_count_is("AWS::IAM::Policy", 1)


def test_iam_policy_properties():
    """Validate the properties of the IAM policy."""
    template = get_template()
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": [
                {
                    "Action": ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
                    "Effect": "Allow",
                    "Resource": {"Fn::Join": ["", ["arn:", {"Ref": "AWS::Partition"}, ":secretsmanager:",
                                                   {"Ref": "AWS::Region"}, ":", {"Ref": "AWS::AccountId"},
                                                   ":secret:openai-api-key-??????"]]}
                },
                {
                    "Action": ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
                    "Effect": "Allow",
                    "Resource": {"Fn::Join": ["", ["arn:", {"Ref": "AWS::Partition"}, ":secretsmanager:",
                                                   {"Ref": "AWS::Region"}, ":", {"Ref": "AWS::AccountId"},
                                                   ":secret:app-session-secret-key-??????"]]}
                },
                {
                    "Action": [
                        "s3:GetObject*",
                        "s3:GetBucket*",
                        "s3:List*",
                        "s3:DeleteObject*",
                        "s3:PutObject",
                        "s3:PutObjectLegalHold",
                        "s3:PutObjectRetention",
                        "s3:PutObjectTagging",
                        "s3:PutObjectVersionTagging",
                        "s3:Abort*",
                    ],
                    "Effect": "Allow",
                    "Resource": [
                        {"Fn::GetAtt": ["ClientBaseRagBucket253728B3", "Arn"]},
                        {"Fn::Join": ["", [{"Fn::GetAtt": ["ClientBaseRagBucket253728B3", "Arn"]}, "/*"]]}
                    ]
                }
            ],
            "Version": "2012-10-17"
        }
    })


def test_lambda_function_url_output():
    """Ensure the correct output for the Lambda Function URL."""
    template = get_template()
    template.has_output("LambdaFunctionURL", {
        "Description": "URL for the Flask Lambda function",
        "Value": {"Fn::GetAtt": ["FlaskLambdaFunctionUrl73830B7F", "FunctionUrl"]}
    })


def test_s3_bucket_lifecycle_rule():
    """Ensure the S3 bucket lifecycle rule deletes objects after 24 hours."""
    template = get_template()
    template.has_resource_properties("AWS::S3::Bucket", {
        "LifecycleConfiguration": {
            "Rules": [{
                "ExpirationInDays": 1,
                "Status": "Enabled"
            }]
        }
    })


def test_lambda_environment_variables():
    """Ensure the Lambda function has the correct environment variables."""
    template = get_template()
    properties = template.to_json().get("Resources", {}).values()
    lambda_properties = [
        p for p in properties
        if p.get("Type") == "AWS::Lambda::Function"
    ]

    matched_lambda = None
    for lambda_config in lambda_properties:
        environment_vars = lambda_config.get("Properties", {}).get("Environment", {}).get("Variables", {})
        if "OPENAI_SECRET_ARN" in environment_vars or "SESSION_SECRET_KEY_ARN" in environment_vars:
            matched_lambda = environment_vars
            break

    assert matched_lambda is not None, "No Lambda function matched with the required environment variables."

    openai_secret_arn = matched_lambda.get("OPENAI_SECRET_ARN")
    session_secret_key_arn = matched_lambda.get("SESSION_SECRET_KEY_ARN")

    assert openai_secret_arn is not None, f"OPENAI_SECRET_ARN not found in environment variables: {matched_lambda}"
    assert session_secret_key_arn is not None, f"SESSION_SECRET_KEY_ARN not found in environment variables: {matched_lambda}"

    if isinstance(openai_secret_arn, dict) and 'Fn::Join' in openai_secret_arn:
        assert openai_secret_arn == {
            "Fn::Join": [
                "", [
                    "arn:", {"Ref": "AWS::Partition"},
                    ":secretsmanager:", {"Ref": "AWS::Region"},
                    ":", {"Ref": "AWS::AccountId"},
                    ":secret:openai-api-key"
                ]
            ]
        }
    if isinstance(session_secret_key_arn, dict) and 'Fn::Join' in session_secret_key_arn:
        assert session_secret_key_arn == {
            "Fn::Join": [
                "", [
                    "arn:", {"Ref": "AWS::Partition"},
                    ":secretsmanager:", {"Ref": "AWS::Region"},
                    ":", {"Ref": "AWS::AccountId"},
                    ":secret:app-session-secret-key"
                ]
            ]
        }

    bucket_name = matched_lambda.get("BUCKET_NAME")
    assert bucket_name is not None, f"BUCKET_NAME not found in environment variables: {matched_lambda}"
    assert bucket_name.get(
        "Ref") == "ClientBaseRagBucket253728B3", f"BUCKET_NAME reference did not match: {bucket_name}"


def test_output_lambda_function_url():
    """Ensure the Lambda Function URL output is configured correctly."""
    template = get_template()
    template.has_output("LambdaFunctionURL", {
        "Description": "URL for the Flask Lambda function",
        "Value": {
            "Fn::GetAtt": ["FlaskLambdaFunctionUrl73830B7F", "FunctionUrl"]
        }
    })


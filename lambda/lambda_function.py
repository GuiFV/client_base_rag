import os
import boto3
from mangum import Mangum
from flask_asgi import asgi_app


def fetch_secret(secret_arn):
    # secret_arn = os.getenv('SECRET_ARN')
    if not secret_arn:
        raise RuntimeError("Secret ARN not set in environment variables")

    # Create a Secrets Manager client
    region_name = "us-east-1"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_arn)
    except Exception as e:
        print(f"Error fetching secret: {e}")
        return None

    secret = get_secret_value_response['SecretString']
    return secret


# Fetch the OpenAI API key
OPENAI_API_KEY = fetch_secret(os.getenv('OPENAI_SECRET_ARN'))

# Fetch the session secret key
SESSION_SECRET_KEY = fetch_secret(os.getenv('SESSION_SECRET_KEY_ARN'))

if not OPENAI_API_KEY:
    raise RuntimeError("Failed to fetch OpenAI API key")

if not SESSION_SECRET_KEY:
    raise RuntimeError("Failed to fetch session secret key")

asgi_app.secret_key = SESSION_SECRET_KEY

handler = Mangum(asgi_app, lifespan="off")

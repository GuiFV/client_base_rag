import sys
import os

# Function to check and modify sys.path if virtual environment is activated
def ensure_venv():
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        venv_site_packages = os.path.join(venv_path, 'lib', 'python3.12', 'site-packages')
        if os.path.exists(venv_site_packages):
            sys.path.insert(0, venv_site_packages)
            print(f"VENV detected, updated sys.path: {sys.path}")
        else:
            print(f"Path {venv_site_packages} does not exist")
    else:
        print("No virtual environment detected")


# Ensure virtual environment if available
ensure_venv()

# Imports
from flask import Flask, render_template, request, jsonify, session
import boto3
from openai import OpenAI
import json


app = Flask(__name__, static_url_path='/static')

def get_secret(secret_name):
    # Fetch OpenAI API key from AWS Secrets Manager
    region_name = "us-east-1"  # Replace with your AWS region

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        print(f"Error fetching secret: {e}")
        return None

    secret = get_secret_value_response['SecretString']
    return secret


OPENAI_API_KEY = get_secret("openai-api-key")

# Retrieve the session secret key
session_secret_key = get_secret("app-session-secret-key")

if not OPENAI_API_KEY:
    raise RuntimeError("Failed to fetch OpenAI API key")

if not session_secret_key:
    raise RuntimeError("Failed to fetch session secret key")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

app.secret_key = session_secret_key

@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/message', methods=['POST'])
def process_message():
    data = request.json
    user_message = data['message']


    # Initialize chat history if it doesn't exist
    if 'chat_history' not in session:
        session['chat_history'] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    # Append user message to chat history
    session['chat_history'].append({"role": "user", "content": user_message})

    # Use the OpenAI API to process the message
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=session['chat_history']
    )

    bot_response = completion.choices[0].message.content.strip()

    # Append assistant response to chat history
    session['chat_history'].append({"role": "assistant", "content": bot_response})

    # Explicitly mark the session as modified
    session.modified = True

    return jsonify({'response': bot_response})



if __name__ == "__main__":

    app.run(debug=True)

import sys
import os

# Function to check and modify sys.path if virtual environment is activated
def ensure_venv():
    """This was required to isolate the machine locally and under AWS due to pydantic library issue"""
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


# Ensure app run on virtual environment if available
ensure_venv()

# Imports
from flask import Flask, render_template, request, jsonify, session
import boto3
from openai import OpenAI
import json
import csv
import fitz  # PyMuPDF
from docx import Document  # python-docx
import re


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


def parse_file(file):
    """Parse the uploaded file based on its type and return its contents as a string."""
    filename = file.filename
    file_contents = ""

    if filename.endswith('.pdf'):
        doc = fitz.open(file.stream)
        for page in doc:
            file_contents += page.get_text()
    elif filename.endswith('.txt'):
        file_contents = file.read().decode('utf-8')
    elif filename.endswith('.csv'):
        file_contents = file.read().decode('utf-8')
    elif filename.endswith('.docx'):
        doc = Document(file)
        file_contents = '\n'.join([para.text for para in doc.paragraphs])
    else:
        raise ValueError("Unsupported file type")

    # Ensure storing correctly in session
    session['uploaded_document'] = file_contents
    return file_contents

def extract_keywords(query):
    """Extract keywords from the query by removing stop words and focusing on significant terms."""
    stop_words = {'is', 'the', 'on', 'in', 'who', 'a', 'an'}
    words = re.findall(r'\b\w+\b', query.lower())
    keywords = [word for word in words if word not in stop_words]
    return keywords


def search_document(document, query):
    """Search for relevant snippets in the document based on the query."""
    keywords = extract_keywords(query)
    lines = document.split('\n')

    snippets = [line.strip() for line in lines if any(keyword in line.lower() for keyword in keywords)]

    return snippets if snippets else ["No relevant information found in the document."]



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

    # Initializing an indication text for snippets
    snippets_text = ""

    # Augment user message with relevant snippets from the document
    if 'uploaded_document' in session:

        # Retrieve and print the document contents from the session
        document = session['uploaded_document']
        snippets = search_document(document, user_message)
        snippets_text = "\n".join(snippets)

    # Inform LLM explicitly that the document content is additional context
    augmented_message = (
        f"User's message:\n{user_message}\n\n"
        "Additional context provided from the uploaded document:\n"
        f"{snippets_text}\n"
    )

    # Append user message to chat history
    session['chat_history'].append({"role": "user", "content": augmented_message})

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

    # Format and send the augmented response with the information source
    response = f"{bot_response}\n\nInformation source:\n{snippets_text}"

    return jsonify({'response': response})


@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    try:
        file_contents = parse_file(file)
        session['uploaded_document'] = file_contents
        return jsonify({'message': 'File uploaded and parsed successfully.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":

    app.run(debug=True)

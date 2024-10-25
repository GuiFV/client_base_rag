import sys
import os

# Global flag to indicate if running locally
RUNNING_LOCALLY = False


# Function to check and modify sys.path if virtual environment is activated
def ensure_venv():
    """This was required to isolate the machine locally and under AWS due to pydantic library issue."""
    global RUNNING_LOCALLY
    venv_path = os.environ.get('VIRTUAL_ENV')
    if venv_path:
        venv_site_packages = os.path.join(venv_path, 'lib', 'python3.12', 'site-packages')
        if os.path.exists(venv_site_packages):
            sys.path.insert(0, venv_site_packages)
            RUNNING_LOCALLY = True
            print(f"VENV detected, updated sys.path: {sys.path}")
        else:
            print(f"Path {venv_site_packages} does not exist")
    else:
        print("No virtual environment detected")


# Ensure app run on virtual environment if available
ensure_venv()

# Imports
from flask import Flask, render_template, request, jsonify, session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import boto3
from openai import OpenAI
import re

# Constants
if RUNNING_LOCALLY:
    LOCAL_STORAGE_PATH = os.path.join(os.getcwd(), "local_s3")  # Local storage path at the project's root
    os.makedirs(LOCAL_STORAGE_PATH, exist_ok=True)

app = Flask(__name__, static_url_path='/static')

# Initialize Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["100 per day", "10 per hour"]
)

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


# Fetch secrets
OPENAI_API_KEY = get_secret("openai-api-key")
session_secret_key = get_secret("app-session-secret-key")

if not OPENAI_API_KEY:
    raise RuntimeError("Failed to fetch OpenAI API key")
if not session_secret_key:
    raise RuntimeError("Failed to fetch session secret key")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)
app.secret_key = session_secret_key

# S3 bucket environment variable
BUCKET_NAME = os.getenv("BUCKET_NAME")
if not RUNNING_LOCALLY and BUCKET_NAME is None:
    raise RuntimeError("S3 BUCKET_NAME environment variable is not set in non-local environment")

s3_client = boto3.client('s3') if not RUNNING_LOCALLY else None


def save_and_parse_file(file):
    """Save the uploaded file locally and parse its contents."""
    filename = file.filename
    local_path = os.path.join(LOCAL_STORAGE_PATH, filename)
    file.save(local_path)

    with open(local_path, 'r', encoding='utf-8') as f:
        file_contents = f.read()

    print(f'Saved file at: {local_path}')
    print(f'File length: {len(file_contents)}')
    print(f'File contents: {file_contents[:100]}')  # Printing only first 100 characters for brevity

    return local_path, file_contents


def extract_keywords(query):
    """Extract keywords from the query by removing stop words and focusing on significant terms."""
    stop_words = {'is', 'the', 'on', 'in', 'who', 'a', 'an'}
    words = re.findall(r'\b\w+\b', query.lower())
    keywords = [word for word in words if word not in stop_words]
    print(f"Extracted keywords: {keywords}")  # Debugging output
    return keywords


def process_s3_file(file_key, query):
    """Fetch file from S3 and process it in chunks to search for query."""
    if RUNNING_LOCALLY:
        raise RuntimeError("S3 operations are not allowed in local environment")

    response = s3_client.get_object(Bucket=BUCKET_NAME, Key=file_key)
    content = response['Body'].iter_lines()

    keywords = extract_keywords(query)
    snippets = []

    for line in content:
        decoded_line = line.decode('utf-8')
        if any(keyword in decoded_line.lower() for keyword in keywords):
            snippets.append(decoded_line.strip())

    return snippets if snippets else ["No relevant information found in the document."]


def search_document(document, query):
    """Search for relevant snippets in the document based on the query."""
    keywords = extract_keywords(query)
    lines = document.split('\n')

    snippets = [line.strip() for line in lines if any(keyword in line.lower() for keyword in keywords)]
    print(f"Document length: {len(document)}")
    print(f"Keywords: {keywords}\nSnippets: {snippets}")  # Debugging output
    return snippets if snippets else ["No relevant information found in the document."]


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/clear_session', methods=['POST'])
@limiter.limit("10 per day")
def clear_session():
    session.clear()
    return jsonify({'message': 'Session cleared successfully'}), 200


@app.route('/api/message', methods=['POST'])
@limiter.limit("30 per day")
def process_message():
    data = request.json
    user_message = data['message']

    if 'chat_history' not in session:
        session['chat_history'] = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]

    snippets_text = ""

    if not RUNNING_LOCALLY and 'uploaded_document_s3_key' in session:
        # Retrieve document from S3
        s3_key = session['uploaded_document_s3_key']
        snippets = process_s3_file(s3_key, user_message)
        snippets_text = "\n".join(snippets)
        print(f's3_key: {s3_key}')
    elif 'uploaded_document_path' in session:
        # Retrieve document from local storage
        with open(session['uploaded_document_path'], 'r', encoding='utf-8') as f:
            document = f.read()
        snippets = search_document(document, user_message)
        snippets_text = "\n".join(snippets)
        print(f'document: {document}')

    if not snippets_text:
        augmented_message = (
            f"User's message:\n{user_message}\n\n"
            "No document uploaded. To use the assistant's full capability, please upload a document."
        )

    else:
        augmented_message = (
            f"User's message:\n{user_message}\n\n"
            "Additional context provided from the uploaded document:\n"
            f"{snippets_text}\n"
        )

    session['chat_history'].append({"role": "user", "content": augmented_message})

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=session['chat_history']
    )

    bot_response = completion.choices[0].message.content.strip()

    session['chat_history'].append({"role": "assistant", "content": bot_response})

    session.modified = True

    response = f"{bot_response}\n\nInformation source:\n\n{snippets_text}"

    return jsonify({'response': response})


@app.route('/api/upload', methods=['POST'])
@limiter.limit("10 per day")
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file.mimetype not in ['text/plain', 'text/csv']:
        return jsonify({'error': 'Unsupported file type'}), 400

    if len(file.read()) > 1 * 1024 * 1024:  # Limiting file size to 1MB
        return jsonify({'error': 'File size exceeds limit (1MB)'}), 400

    file.seek(0)  # Reset file pointer to beginning after checking size

    try:
        if RUNNING_LOCALLY:
            local_path, file_contents = save_and_parse_file(file)
            session['uploaded_document_path'] = local_path
            print(f"File parsed contents stored path: {local_path}")

        else:
            s3_key = f"uploads/{file.filename}"
            s3_client.upload_fileobj(file, BUCKET_NAME, s3_key)
            session['uploaded_document_s3_key'] = s3_key

        return jsonify(
            {'message': f'File {"stored locally" if RUNNING_LOCALLY else "uploaded to S3"} and parsed successfully.'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)

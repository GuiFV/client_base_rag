document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('user-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

document.getElementById('file-upload').addEventListener('change', handleFileUpload);
document.getElementById('refresh-session-link').addEventListener('click', refreshSession);

async function sendMessage() {
    const userInput = document.getElementById('user-input');
    const message = userInput.value.trim();
    if (message) {
        appendMessage('user', message);
        userInput.value = ''; // Clear the input field

        // Send the message to the server
        try {
            const response = await fetch('/api/message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to fetch response from server.');
            }

            const data = await response.json();
            appendMessage('bot', data.response);

        } catch (error) {
            console.error('Error:', error);
            appendMessage('bot', 'An error occurred while processing your message.');
        }
    }
}

function appendMessage(type, message) {
    const output = document.getElementById('output');
    const messageDiv = document.createElement('div');
    messageDiv.classList.add(type);
    messageDiv.innerText = message;
    output.appendChild(messageDiv);
    output.scrollTop = output.scrollHeight; // Auto scroll to the bottom
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        // Check file size (1MB = 1 * 1024 * 1024 bytes)
        if (file.size > 1 * 1024 * 1024) {
            appendMessage('bot', 'File size exceeds limit (1MB).');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Failed to upload file.');
            }

            const data = await response.json();
            appendMessage('bot', data.message || 'File uploaded and parsed successfully.');

        } catch (error) {
            console.error('Error:', error);
            appendMessage('bot', `An error occurred while uploading the file: ${error.message}`);
        }
    }
}

// Function to refresh the page
function refreshPage() {
    location.reload();
}


// Functions to open and close the modal
function openModal() {
    const modal = document.getElementById('modal');
    modal.style.display = "block";

    // Add an event listener to close the modal when clicking outside of it
    window.addEventListener('click', handleOutsideClick);
}

function closeModal() {
    const modal = document.getElementById('modal');
    modal.style.display = "none";

    // Remove the event listener when the modal is closed
    window.removeEventListener('click', handleOutsideClick);
}

// Function to handle clicks outside the modal
function handleOutsideClick(event) {
    const modal = document.getElementById('modal');
    if (event.target === modal) {
        closeModal();
    }
}

// Close the modal when clicking the close button
document.querySelector('.close').addEventListener('click', closeModal);

// Function to clear session and redirect to homepage
async function refreshSession(event) {
    event.preventDefault(); // Prevent default anchor behavior

    try {
        const response = await fetch('/api/clear_session', {
            method: 'POST'
        });

        if (response.ok) {
            // Redirect to homepage
            window.location.href = "/";
        } else {
            console.error('Failed to clear session.');
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
document.getElementById('send-btn').addEventListener('click', sendMessage);
document.getElementById('user-input').addEventListener('keypress', function (e) {
    if (e.key === 'Enter') {
        sendMessage();
    }
});

document.getElementById('file-upload').addEventListener('change', handleFileUpload);

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
                throw new Error('Failed to fetch response from server.');
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
    messageDiv.innerText=message;
    output.appendChild(messageDiv);
    output.scrollTop = output.scrollHeight; // Auto scroll to the bottom
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (e) {
            const fileContents = e.target.result;
            console.log(fileContents); // Store or process the file contents as needed
            appendMessage('bot', "File uploaded and read successfully.");
        };
        reader.onerror = function () {
            console.error("Error reading file");
            appendMessage('bot', "Failed to read the file.");
        };
        reader.readAsText(file); // This works for text files, configure accordingly for other types
    }
}
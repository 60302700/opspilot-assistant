const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');
const chatContainer = document.getElementById('chat-container');
const sendButton = document.getElementById('send-button');

// Using marked.js for robust markdown rendering
function parseMarkdown(text) {
    return marked.parse(text, { breaks: true });
}

function appendMessage(sender, text, isMarkdown = false) {
    const isUser = sender === 'user';

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isUser ? 'user-message' : 'ai-message'}`;

    const avatarDiv = document.createElement('div');
    avatarDiv.className = `avatar ${isUser ? 'user-avatar' : 'ai-avatar'}`;
    avatarDiv.textContent = isUser ? 'ME' : 'OP';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = isMarkdown ? parseMarkdown(text) : `<p>${text}</p>`;

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);

    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

function appendLoading() {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ai-message loading-message';
    messageDiv.id = 'loading-message';

    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'avatar ai-avatar';
    avatarDiv.textContent = 'OP';

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.innerHTML = `
        <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;

    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);

    chatContainer.appendChild(messageDiv);
    scrollToBottom();
}

function removeLoading() {
    const loadingMessage = document.getElementById('loading-message');
    if (loadingMessage) {
        loadingMessage.remove();
    }
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const message = userInput.value.trim();
    if (!message) return;

    // Disable input and button
    userInput.value = '';
    userInput.disabled = true;
    sendButton.disabled = true;

    appendMessage('user', message);
    appendLoading();

    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await response.json();

        removeLoading();
        if (data.error) {
            appendMessage('ai', `**Error:** ${data.error}`, true);
        } else {
            appendMessage('ai', data.response, true);
        }
    } catch (error) {
        removeLoading();
        appendMessage('ai', `**Connection Error:** Could not reach the server.`, true);
    } finally {
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.focus();
    }
});

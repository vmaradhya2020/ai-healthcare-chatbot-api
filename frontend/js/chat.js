// ============================================
// Chat Page Logic
// ============================================

// Redirect to login if not authenticated
if (!isAuthenticated()) {
    window.location.href = 'index.html';
}

// DOM Elements
const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const typingIndicator = document.getElementById('typingIndicator');
const menuBtn = document.getElementById('menuBtn');
const dropdownMenu = document.getElementById('dropdownMenu');
const clearChatBtn = document.getElementById('clearChatBtn');
const logoutBtn = document.getElementById('logoutBtn');

// Chat State
let chatHistory = [];

// ============================================
// Message Rendering
// ============================================

function formatTime(date) {
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

function createMessageBubble(type, message, metadata = {}) {
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${type}`;

    const avatarSVG = type === 'bot'
        ? '<path d="M25 15v20M15 25h20" stroke="white" stroke-width="3" stroke-linecap="round"/>'
        : '<circle cx="25" cy="25" r="12" fill="white"/>';

    const avatar = `
        <div class="message-avatar">
            <svg width="40" height="40" viewBox="0 0 50 50" fill="none">
                <circle cx="25" cy="25" r="20" fill="${type === 'bot' ? '#4CAF50' : '#2196F3'}"/>
                ${avatarSVG}
            </svg>
        </div>
    `;

    const header = type === 'bot'
        ? `<div class="message-header">
                <span class="sender-name">Healthcare AI</span>
                <span class="message-time">${formatTime(new Date())}</span>
           </div>`
        : '';

    const timeFooter = type === 'user'
        ? `<div class="message-header">
                <span class="message-time">${formatTime(new Date())}</span>
           </div>`
        : '';

    const metaChips = (metadata.intent || metadata.data_source)
        ? `<div class="message-meta">
                ${metadata.intent ? `<span class="meta-chip">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <rect x="3" y="3" width="7" height="7"/>
                        <rect x="14" y="3" width="7" height="7"/>
                        <rect x="14" y="14" width="7" height="7"/>
                        <rect x="3" y="14" width="7" height="7"/>
                    </svg>
                    ${metadata.intent}
                </span>` : ''}
                ${metadata.data_source ? `<span class="meta-chip">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                        <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/>
                    </svg>
                    ${metadata.data_source}
                </span>` : ''}
           </div>`
        : '';

    bubble.innerHTML = `
        ${avatar}
        <div class="message-content">
            ${header}
            <div class="message-text">${message}</div>
            ${metaChips}
            ${timeFooter}
        </div>
    `;

    return bubble;
}

function addMessage(type, message, metadata = {}) {
    // Remove welcome message if it exists
    const welcomeMsg = chatMessages.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // Create and add message bubble
    const bubble = createMessageBubble(type, message, metadata);
    chatMessages.appendChild(bubble);

    // Scroll to bottom
    scrollToBottom();

    // Store in history
    chatHistory.push({ type, message, metadata, timestamp: new Date() });
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
    typingIndicator.style.display = 'flex';
    scrollToBottom();
}

function hideTypingIndicator() {
    typingIndicator.style.display = 'none';
}

// ============================================
// Chat Functionality
// ============================================

async function sendMessage(message) {
    try {
        // Add user message to chat
        addMessage('user', message);

        // Clear input
        messageInput.value = '';
        adjustTextareaHeight();

        // Show typing indicator
        showTypingIndicator();

        // Disable send button
        sendBtn.disabled = true;

        // Call chat API
        const response = await apiCall('/chat', {
            method: 'POST',
            body: JSON.stringify({ message })
        });

        // Hide typing indicator
        hideTypingIndicator();

        // Add bot response
        addMessage('bot', response.response, {
            intent: response.intent,
            data_source: response.data_source
        });

        // Enable send button
        sendBtn.disabled = false;

        // Focus back on input
        messageInput.focus();

    } catch (error) {
        hideTypingIndicator();
        sendBtn.disabled = false;

        addMessage('bot', '❌ Sorry, I encountered an error. Please try again or contact support if the issue persists.');
        console.error('Chat error:', error);
    }
}

// ============================================
// Form Handling
// ============================================

chatForm.addEventListener('submit', (e) => {
    e.preventDefault();

    const message = messageInput.value.trim();
    if (!message) return;

    sendMessage(message);
});

// Handle Enter key (send) and Shift+Enter (new line)
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

// Auto-resize textarea
function adjustTextareaHeight() {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 120) + 'px';
}

messageInput.addEventListener('input', adjustTextareaHeight);

// ============================================
// Menu Actions
// ============================================

// Toggle dropdown menu
menuBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    dropdownMenu.classList.toggle('active');
});

// Close dropdown when clicking outside
document.addEventListener('click', () => {
    dropdownMenu.classList.remove('active');
});

// Prevent dropdown from closing when clicking inside
dropdownMenu.addEventListener('click', (e) => {
    e.stopPropagation();
});

// Clear chat
clearChatBtn.addEventListener('click', () => {
    chatHistory = [];
    chatMessages.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">
                <svg width="60" height="60" viewBox="0 0 50 50" fill="none">
                    <circle cx="25" cy="25" r="23" fill="#4CAF50" opacity="0.2"/>
                    <path d="M25 10v30M10 25h30" stroke="#4CAF50" stroke-width="4" stroke-linecap="round"/>
                </svg>
            </div>
            <h2>Chat Cleared</h2>
            <p class="welcome-prompt">How can I assist you today?</p>
        </div>
    `;
    dropdownMenu.classList.remove('active');
});

// Logout
logoutBtn.addEventListener('click', () => {
    logout();
});

// ============================================
// Load Chat History on Page Load
// ============================================

async function loadChatHistory() {
    try {
        const response = await apiCall('/chat/history');

        if (response.items && response.items.length > 0) {
            // Remove welcome message
            const welcomeMsg = chatMessages.querySelector('.welcome-message');
            if (welcomeMsg) {
                welcomeMsg.remove();
            }

            // Add messages in reverse order (oldest first)
            response.items.reverse().forEach(item => {
                addMessage('user', item.user_message);
                if (item.ai_response) {
                    addMessage('bot', item.ai_response, {
                        intent: item.intent,
                        data_source: item.data_source
                    });
                }
            });
        }
    } catch (error) {
        console.error('Failed to load chat history:', error);
        // Don't show error to user, just log it
    }
}

// Load history when page loads
document.addEventListener('DOMContentLoaded', () => {
    loadChatHistory();
    messageInput.focus();
});

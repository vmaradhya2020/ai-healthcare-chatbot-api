"""
Gradio Interface for Healthcare AI Assistant
HuggingFace Spaces Compatible Deployment
"""

import gradio as gr
import requests
import os
from typing import List, Tuple
import json

# API endpoint - use localhost for Docker deployment
API_URL = os.getenv("API_URL", "http://localhost:8001")

# Store session token
session_token = None
session_user_email = None


def login(email: str, password: str) -> str:
    """Login and get authentication token"""
    global session_token, session_user_email

    if not email or not password:
        return "⚠️ Please enter both email and password"

    try:
        # Send JSON with email field as expected by FastAPI UserLogin schema
        response = requests.post(
            f"{API_URL}/login",
            json={"email": email, "password": password}
        )

        if response.status_code == 200:
            data = response.json()
            session_token = data.get("access_token")
            session_user_email = email
            return f"✅ Login successful! Welcome, {email}\n\nYou can now start chatting in the Chat tab."
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return f"❌ Login failed: {error_detail}"
    except Exception as e:
        return f"❌ Connection error: {str(e)}\n\nPlease ensure the backend is running."


def register(email: str, password: str, client_code: str) -> str:
    """Register a new user"""
    if not email or not password or not client_code:
        return "⚠️ Please fill in all fields"

    if len(password) < 8:
        return "⚠️ Password must be at least 8 characters long"

    try:
        response = requests.post(
            f"{API_URL}/register",
            json={
                "email": email,
                "password": password,
                "client_code": client_code
            }
        )

        if response.status_code == 200:
            return "✅ Registration successful! You can now login in the Login tab."
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return f"❌ Registration failed: {error_detail}"
    except Exception as e:
        return f"❌ Connection error: {str(e)}"


def chat(message: str, history: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], str]:
    """Send message to chatbot and return updated history"""
    global session_token

    if not message or not message.strip():
        return history, ""

    if not session_token:
        history.append((message, "⚠️ **Please login first**\n\nGo to the Login tab and enter your credentials."))
        return history, ""

    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={"message": message},
            headers={"Authorization": f"Bearer {session_token}"}
        )

        if response.status_code == 200:
            data = response.json()
            bot_response = data.get("response", "No response received")
            intent = data.get("intent", "unknown")
            data_source = data.get("data_source", "N/A")

            # Format response with metadata
            formatted_response = f"{bot_response}\n\n"
            formatted_response += f"_📊 Intent: {intent} | Source: {data_source}_"

            history.append((message, formatted_response))
        elif response.status_code == 401:
            history.append((message, "❌ **Session expired**\n\nPlease login again."))
            session_token = None
        else:
            error_detail = response.json().get("detail", "Unknown error")
            history.append((message, f"❌ Error: {error_detail}"))

    except Exception as e:
        history.append((message, f"❌ Connection error: {str(e)}"))

    return history, ""  # Return empty string to clear input


def get_chat_history() -> str:
    """Fetch chat history from backend"""
    global session_token

    if not session_token:
        return "⚠️ Please login first"

    try:
        response = requests.get(
            f"{API_URL}/chat/history",
            headers={"Authorization": f"Bearer {session_token}"}
        )

        if response.status_code == 200:
            data = response.json()
            conversations = data.get("conversations", [])

            if not conversations:
                return "No chat history found"

            # Format history
            history_text = "## Chat History\n\n"
            for idx, conv in enumerate(conversations[:10], 1):  # Show last 10
                history_text += f"**{idx}. {conv.get('timestamp', 'N/A')}**\n"
                history_text += f"👤 You: {conv.get('message', 'N/A')}\n"
                history_text += f"🤖 Bot: {conv.get('response', 'N/A')}\n\n"
                history_text += "---\n\n"

            return history_text
        else:
            return "❌ Failed to fetch history"
    except Exception as e:
        return f"❌ Error: {str(e)}"


def logout() -> str:
    """Logout user"""
    global session_token, session_user_email

    session_token = None
    session_user_email = None
    return "✅ Logged out successfully"


# Custom CSS for better styling
custom_css = """
.gradio-container {
    max-width: 900px !important;
}
.chat-message {
    font-size: 16px !important;
}
"""

# Create Gradio interface
with gr.Blocks(
    title="Healthcare AI Assistant",
    theme=gr.themes.Soft(primary_hue="green"),
    css=custom_css
) as demo:

    gr.Markdown(
        """
        # 🏥 Healthcare AI Assistant
        ### AI-powered chatbot for medical equipment management and support
        """
    )

    with gr.Tab("💬 Chat"):
        gr.Markdown("Ask questions about orders, invoices, warranties, appointments, and more!")

        chatbot = gr.Chatbot(
            label="Healthcare Assistant",
            height=500,
            bubble_full_width=False,
            avatar_images=(None, "🤖"),
            show_label=True,
            elem_classes="chat-message"
        )

        with gr.Row():
            msg = gr.Textbox(
                label="Your message",
                placeholder="E.g., 'What is the status of my order?' or 'Show me pending invoices'",
                lines=2,
                scale=4
            )
            send_btn = gr.Button("Send", variant="primary", scale=1)

        with gr.Row():
            clear_btn = gr.Button("Clear Chat", variant="secondary")

        # Chat examples
        gr.Examples(
            examples=[
                "What is the status of order TRK-2023-1000?",
                "Show me all pending invoices",
                "When does the warranty expire for equipment USM-2023-001?",
                "I need to schedule an appointment for equipment maintenance",
                "Create a support ticket for equipment malfunction",
                "What AMC contracts are expiring soon?",
            ],
            inputs=msg,
            label="Example Questions"
        )

        # Event handlers
        msg.submit(chat, [msg, chatbot], [chatbot, msg])
        send_btn.click(chat, [msg, chatbot], [chatbot, msg])
        clear_btn.click(lambda: [], None, chatbot, queue=False)

    with gr.Tab("🔐 Login"):
        gr.Markdown("### Login to Your Account")

        with gr.Row():
            with gr.Column():
                email_input = gr.Textbox(
                    label="Email Address",
                    placeholder="admin@cityhospital.com",
                    type="text"
                )
                password_input = gr.Textbox(
                    label="Password",
                    placeholder="Enter your password",
                    type="password"
                )
                login_btn = gr.Button("Login", variant="primary", size="lg")
                logout_btn = gr.Button("Logout", variant="secondary")

            with gr.Column():
                login_output = gr.Textbox(
                    label="Status",
                    interactive=False,
                    lines=4
                )

        gr.Markdown("**Test Credentials:** `admin@cityhospital.com` / `password123`")

        # Event handlers
        login_btn.click(login, [email_input, password_input], login_output)
        logout_btn.click(logout, None, login_output)

    with gr.Tab("📝 Register"):
        gr.Markdown("### Create a New Account")

        with gr.Row():
            with gr.Column():
                reg_email = gr.Textbox(label="Email Address", placeholder="you@example.com")
                reg_password = gr.Textbox(
                    label="Password",
                    placeholder="Minimum 8 characters",
                    type="password"
                )
                reg_client_code = gr.Textbox(
                    label="Client Code",
                    placeholder="Provided by your organization"
                )
                register_btn = gr.Button("Register", variant="primary", size="lg")

            with gr.Column():
                register_output = gr.Textbox(
                    label="Registration Status",
                    interactive=False,
                    lines=4
                )

        gr.Markdown("**Available Client Codes:** `CITY001`, `MARY002`, `COMM003`, `DIAG004`")

        # Event handler
        register_btn.click(
            register,
            [reg_email, reg_password, reg_client_code],
            register_output
        )

    with gr.Tab("📜 History"):
        gr.Markdown("### Your Chat History")

        history_output = gr.Markdown(label="Chat History")
        refresh_btn = gr.Button("Refresh History", variant="primary")

        refresh_btn.click(get_chat_history, None, history_output)

    with gr.Tab("ℹ️ About"):
        gr.Markdown(
            """
            ## Features

            This Healthcare AI Assistant provides comprehensive support for medical equipment management:

            ### 📦 Order Management
            - Track order status and delivery information
            - View order history and details
            - Real-time tracking number lookup

            ### 💰 Financial Management
            - Invoice tracking and payment status
            - Payment history and receipts
            - Pending invoice notifications

            ### 🛡️ Warranty & AMC
            - Warranty status and expiration dates
            - AMC contract details and renewal
            - Coverage information

            ### 📅 Appointment Scheduling
            - Schedule equipment maintenance
            - Book service appointments
            - Technician availability

            ### 🎫 Support Tickets
            - Create and track support tickets
            - Equipment issue reporting
            - Priority-based ticket handling

            ### 🤖 AI-Powered Intelligence
            - Natural language understanding
            - Context-aware responses
            - Intent classification
            - Data retrieval from multiple sources

            ---

            ## Technology Stack

            - **Backend:** FastAPI + Python 3.11
            - **Frontend:** Gradio 4.0
            - **Database:** MySQL / SQLite
            - **AI Model:** OpenAI GPT-4
            - **Authentication:** JWT tokens
            - **Deployment:** Docker + HuggingFace Spaces

            ---

            ## Getting Started

            1. **Register** (if new user) or **Login** with existing credentials
            2. Navigate to the **Chat** tab
            3. Ask questions in natural language
            4. View your **History** to review past conversations

            ---

            ## Sample Healthcare Organizations

            - **City General Hospital** (CITY001)
            - **St. Mary's Medical Center** (MARY002)
            - **Community Health Clinic** (COMM003)
            - **Advanced Diagnostics Center** (DIAG004)

            ---

            ## Support

            For technical support or feature requests, please contact your system administrator.

            **Version:** 1.0.0 | **Last Updated:** 2026-01-11
            """
        )


# Launch configuration
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True
    )

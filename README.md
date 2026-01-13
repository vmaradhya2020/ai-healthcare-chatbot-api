---
title: Healthcare AI Assistant
emoji: 🏥
colorFrom: blue
colorTo: green
sdk: docker
sdk_version: "3.9"
app_port: 7860
pinned: false
---

# 🏥 Healthcare AI Assistant

An AI-powered healthcare chatbot for managing medical equipment orders, warranties, invoices, and support tickets.

## 🌟 Features

- **Order Management** - Track order status and delivery information
- **Financial Tracking** - Invoice and payment management
- **Warranty & AMC** - Contract status and expiration tracking
- **Appointment Scheduling** - Schedule equipment maintenance
- **Support Tickets** - Create and track support requests
- **AI-Powered** - Natural language understanding with OpenAI GPT-4

## 🚀 Quick Start

### Using the Application

1. **Login** with test credentials:
   - Email: `admin@cityhospital.com`
   - Password: `password123`

2. **Or Register** a new account:
   - Use one of these client codes: `CITY001`, `MARY002`, `COMM003`, `DIAG004`

3. **Start Chatting**:
   - "What is the status of my order?"
   - "Show me pending invoices"
   - "When does the warranty expire for equipment USM-2023-001?"
   - "I need to schedule an appointment"

## 💬 Example Questions

- **Orders**: "What is the status of order TRK-2023-1000?"
- **Invoices**: "Show me all pending invoices"
- **Warranties**: "Which warranties are expiring soon?"
- **Equipment**: "List all ultrasound machines"
- **Support**: "Create a support ticket for equipment malfunction"
- **Scheduling**: "I need to schedule maintenance"

## 🏢 Demo Organizations

- **City General Hospital** (CITY001)
- **St. Mary's Medical Center** (MARY002)
- **Community Health Clinic** (COMM003)
- **Advanced Diagnostics Center** (DIAG004)

## 🛠️ Technology Stack

- **Backend**: FastAPI + Python 3.11
- **Frontend**: Gradio 4.0
- **Database**: SQLite (demo) / MySQL (production)
- **AI**: OpenAI GPT-4
- **Authentication**: JWT tokens
- **Deployment**: Docker

## 📊 Architecture

The application uses a dual-interface architecture:
- **Gradio UI** (Port 7860) - User-facing chat interface
- **FastAPI Backend** (Port 8001) - RESTful API with business logic
- **SQLite/MySQL** - Persistent data storage

## 🔒 Security Features

- JWT-based authentication
- Password hashing with bcrypt
- Rate limiting (configurable)
- HIPAA compliance logging
- CORS protection

## 📝 API Documentation

When running locally, access:
- **Interactive Docs**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## 🐳 Local Development

### Prerequisites
- Python 3.11+
- Docker (optional)

### Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the application:
   ```bash
   # Start backend
   uvicorn app.main:app --host 0.0.0.0 --port 8001

   # Start Gradio frontend
   python app_gradio.py
   ```

### Docker

```bash
# Build
docker build -f Dockerfile -t healthcare-chatbot .

# Run
docker run -p 7860:7860 --env-file .env healthcare-chatbot
```

## 📚 Documentation

- **Deployment Guide**: See `HUGGINGFACE_DEPLOYMENT.md`
- **Quick Start**: See `START_HERE.md`
- **API Reference**: See `/docs` endpoint

## 🤝 Contributing

This is a capstone project demonstrating AI-powered healthcare support systems.

## 📄 License

Educational/Demo Project

## 🙏 Acknowledgments

- Built with FastAPI and Gradio
- Powered by OpenAI GPT-4
- Healthcare equipment management domain

---

**Note**: This is a demonstration application. For production use, ensure proper security reviews, compliance checks, and data protection measures are in place.

**Version**: 1.0.0 | **Last Updated**: 2026-01-12

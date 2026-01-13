# Quick Start Guide

Get the Healthcare Chatbot API up and running in 10 minutes!

## Prerequisites

- Python 3.11+
- MySQL 8.0+ installed and running on your local machine
- Git

## Step 1: Clone and Setup (2 minutes)

```bash
# Navigate to project directory
cd C:\capstone_ic_ik\ai-healthcare-chatbot-api-main

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```
<!-- PS C:\capstone_ic_ik\ai-healthcare-chatbot-api-main> python -m venv ichealthchatbot
PS C:\capstone_ic_ik\ai-healthcare-chatbot-api-main> .\ichealthchatbot\Scripts\Activate.ps1
(ichealthchatbot) PS C:\capstone_ic_ik\ai-healthcare-chatbot-api-main> -->

## Step 2: Setup MySQL Database (3 minutes)

```bash
# Login to MySQL
mysql -u root -p

# Run the setup script (from MySQL prompt)
source C:\capstone_ic_ik\ai-healthcare-chatbot-api-main\scripts\setup_mysql.sql

# Or run directly from command line:
mysql -u root -p < scripts\setup_mysql.sql

# Exit MySQL
exit
```

**Important:** The script creates a user `healthcareapp` with password `Change_This_Password_123!`

## Step 3: Configure Environment (2 minutes)

```bash
# Copy the example environment file
copy .env.example .env

# Edit .env file and set these REQUIRED values:
```

Open `.env` in your text editor and update:

```env
# REQUIRED: Generate a secure secret key
SECRET_KEY=your-secret-key-here

# REQUIRED: MySQL connection (use password from Step 2)
DATABASE_URL=mysql+pymysql://healthcareapp:Change_This_Password_123!@localhost:3306/healthcaresense

# OPTIONAL: For advanced features
OPENAI_API_KEY=sk-your-openai-key-here

# Set to development for local testing
ENVIRONMENT=development
```

**Generate SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 4: Initialize Database (2 minutes)

```bash
# Create database tables using Alembic
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head

# Seed with sample data (optional but recommended)
python seed_data.py
```

## Step 5: Run the Application (1 minute)

```bash
# Start the server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

You should see:
```
================================================================================
Starting Healthcare Chatbot API - Environment: development
================================================================================
✓ Database connection successful
Development mode: Initializing database tables
CORS Origins: ['http://localhost:4200']
Rate Limiting: Enabled
...
```

## Step 6: Test the API

### Open API Documentation

Visit: http://127.0.0.1:8001/docs

### Test Health Endpoint

```bash
curl http://127.0.0.1:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "development",
  "version": "v1"
}
```

### Register a User

```bash
curl -X POST "http://127.0.0.1:8001/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"password\":\"Password123!\",\"client_code\":\"CLIENT001\"}"
```

### Login

```bash
curl -X POST "http://127.0.0.1:8001/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"test@example.com\",\"password\":\"Password123!\"}"
```

Save the `access_token` from the response!

### Send a Chat Message

```bash
curl -X POST "http://127.0.0.1:8001/chat" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"What is my order status?\"}"
```

## Using Docker (Alternative Quick Start)

If you have Docker installed:

```bash
# Start everything (MySQL + API + Redis)
docker-compose up -d

# Wait for services to start (30 seconds)
# Check logs
docker-compose logs -f api

# Run migrations
docker-compose exec api alembic upgrade head

# Seed database
docker-compose exec api python seed_data.py

# Access at http://localhost:8001
```

## Default Test Data

After running `seed_data.py`, you can login with:

- **Email:** `admin@client001.com`
- **Password:** `Admin123!`
- **Client Code:** `CLIENT001`

## Common Issues & Solutions

### ❌ "Can't connect to MySQL server"

**Solution:** Make sure MySQL service is running
```bash
# Windows: Check Services app and start MySQL80
# Or from command line:
net start MySQL80
```

### ❌ "Access denied for user 'healthcareapp'"

**Solution:** Check your DATABASE_URL in `.env` matches the password you set in MySQL

### ❌ "Secret key validation error"

**Solution:** Make sure you generated and set a SECRET_KEY in `.env`

### ❌ "ModuleNotFoundError"

**Solution:** Make sure virtual environment is activated and dependencies installed
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

### ❌ "OPENAI_API_KEY not found"

**Note:** OpenAI is optional. The system will use keyword-based fallback if not configured.
For full features, get an API key from https://platform.openai.com/api-keys

## Next Steps

### Development
- Read [API Documentation](http://127.0.0.1:8001/docs)
- Explore the codebase structure
- Run tests: `pytest`
- Check code quality: `ruff check app/`

### Production Deployment
- Follow [DEPLOYMENT.md](DEPLOYMENT.md)
- Set up proper SSL/TLS
- Configure production database
- Enable monitoring

## Project Structure

```
ai-healthcare-chatbot-api-main/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── models.py            # Database models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # Authentication
│   ├── intent.py            # Intent classification
│   ├── handlers.py          # Request handlers
│   ├── rag.py               # RAG system
│   └── services/            # Business logic
├── alembic/                 # Database migrations
├── scripts/                 # Utility scripts
├── docs/                    # Documentation
├── .env.example             # Environment template
├── requirements.txt         # Python dependencies
└── docker-compose.yml       # Docker configuration
```

## Available Endpoints

| Endpoint | Method | Description | Auth Required |
|----------|--------|-------------|---------------|
| `/health` | GET | Health check | No |
| `/health/ready` | GET | Readiness check | No |
| `/register` | POST | Register user | No |
| `/login` | POST | Login | No |
| `/me` | GET | Get user info | Yes |
| `/chat` | POST | Send message | Yes |
| `/chat/history` | GET | Get chat history | Yes |
| `/docs` | GET | API documentation | No (dev only) |

## Sample Chat Queries

Try these queries to test different intents:

```bash
# Order Status
"What is the status of my order ORD-12345?"
"Show me my recent orders"

# Invoices
"Show me my pending invoices"
"What invoices are due?"

# Warranties
"Check warranty status for equipment EQ-001"
"What AMC contracts do I have?"

# Maintenance
"Show upcoming maintenance schedules"

# General queries (uses RAG)
"What are the specifications for the MRI machine?"
"How do I request a technician visit?"
```

## Getting Help

- **API Issues:** Check logs in console or `/logs` directory
- **Database Issues:** See [MySQL Setup Guide](docs/MYSQL_SETUP.md)
- **Deployment:** See [DEPLOYMENT.md](DEPLOYMENT.md)
- **GitHub Issues:** https://github.com/venkateswari2754/ai-healthcare-chatbot-api/issues

## Development Tips

### Enable Debug Mode
```env
LOG_LEVEL=DEBUG
```

### Disable Rate Limiting (for testing)
```env
RATE_LIMIT_ENABLED=false
```

### View SQL Queries
```env
LOG_LEVEL=DEBUG
# Database queries will be logged to console
```

### Reset Database
```bash
# Drop all tables
alembic downgrade base

# Recreate
alembic upgrade head

# Reseed
python seed_data.py
```

---

**You're all set!** 🎉

The API is now running and ready for development. Check out the [full documentation](README.md) for more details.

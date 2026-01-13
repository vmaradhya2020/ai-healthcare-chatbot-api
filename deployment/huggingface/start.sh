#!/bin/bash

# Healthcare AI Assistant Startup Script
# Starts both FastAPI backend and Gradio frontend

set -e

echo "============================================"
echo "Healthcare AI Assistant - Starting Services"
echo "============================================"

# Create database tables if they don't exist
echo "📊 Initializing database..."
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)" || echo "⚠️  Database initialization skipped"

# Seed data if database is empty (optional)
if [ "$SEED_DATA" = "true" ]; then
    echo "🌱 Seeding database with test data..."
    python seed_comprehensive_data.py || echo "⚠️  Data seeding skipped"
fi

# Start FastAPI backend in background
echo "🚀 Starting FastAPI backend on port 8001..."
uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8001 \
    --log-level info &

BACKEND_PID=$!
echo "✅ Backend started (PID: $BACKEND_PID)"

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://localhost:8001/health > /dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Backend failed to start in time"
        exit 1
    fi
    sleep 2
done

# Start Gradio frontend
echo "🎨 Starting Gradio frontend on port 7860..."
python app_gradio.py

# If Gradio exits, kill backend
kill $BACKEND_PID 2>/dev/null || true

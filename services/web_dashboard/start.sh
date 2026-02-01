#!/bin/bash
# Startup script that initializes database and starts the Flask app

echo "🚀 Starting Hospital Web Dashboard..."

# Initialize database if it doesn't exist or is empty
if [ ! -f "/app/healthcare.db" ] || [ ! -s "/app/healthcare.db" ]; then
    echo "🏥 Initializing database..."
    python simple_db_init.py
    echo "✅ Database initialized!"
else
    echo "ℹ️  Database already exists"
fi

# Start the Flask application
echo "🌐 Starting Flask application..."
python app.py
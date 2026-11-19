#!/bin/bash
# start.sh — Launch the Smart City platform

set -e

echo "🏙️  Smart City Neo-Sousse 2030 — Startup"
echo "==========================================="

# Check for .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Created .env from template — please fill in your values"
fi

# Load env
export $(cat .env | grep -v '^#' | xargs)

# Create DB and seed
echo ""
echo "📦 Setting up database..."
psql -U "$DB_USER" -h "$DB_HOST" -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "   DB already exists"
psql -U "$DB_USER" -h "$DB_HOST" -d "$DB_NAME" -f database/schema.sql
python database/seed_data.py

echo ""
echo "✅ Database ready!"
echo ""
echo "🚀 Starting Streamlit dashboard..."
echo "   → Open http://localhost:8501"
echo ""

streamlit run frontend/app.py --server.port 8501

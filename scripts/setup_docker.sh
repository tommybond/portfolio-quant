#!/bin/bash

# Setup script for Docker infrastructure

echo "🚀 Setting up Portfolio Quant Docker Infrastructure..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5432/portfolio_quant
TIMESCALEDB_URL=postgresql://portfolio_quant:portfolio_quant_password@localhost:5432/portfolio_quant

# Redis Configuration
REDIS_URL=redis://localhost:6379

# API Keys (set these)
POLYGON_API_KEY=
ALPACA_API_KEY=
ALPACA_SECRET_KEY=
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Security
JWT_SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Application
ENVIRONMENT=development
EOF
    echo "✅ .env file created. Please update with your API keys."
fi

# Start Docker containers
echo "🐳 Starting Docker containers..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check TimescaleDB
if docker exec portfolio_quant_timescaledb pg_isready -U portfolio_quant &> /dev/null; then
    echo "✅ TimescaleDB is ready"
else
    echo "⚠️  TimescaleDB is not ready yet"
fi

# Check PostgreSQL
if docker exec portfolio_quant_postgres pg_isready -U portfolio_quant &> /dev/null; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL is not ready yet"
fi

# Check Redis
if docker exec portfolio_quant_redis redis-cli ping &> /dev/null; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis is not ready yet"
fi

# Initialize TimescaleDB extension
echo "🔧 Initializing TimescaleDB extension..."
docker exec -i portfolio_quant_timescaledb psql -U portfolio_quant -d portfolio_quant << EOF
CREATE EXTENSION IF NOT EXISTS timescaledb;
SELECT timescaledb_post_restore();
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "📊 Services available at:"
echo "  - TimescaleDB: localhost:5432"
echo "  - PostgreSQL: localhost:5433"
echo "  - Redis: localhost:6379"
echo "  - InfluxDB: localhost:8086"
echo "  - Prometheus: localhost:9090"
echo "  - Grafana: localhost:3000 (admin/admin)"
echo ""
echo "📝 Next steps:"
echo "  1. Update .env file with your API keys"
echo "  2. Run: python scripts/init_database.py"
echo "  3. Start the application: streamlit run app.py"
echo ""

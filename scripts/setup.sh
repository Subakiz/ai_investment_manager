#!/bin/bash

# AlphaGen Investment Platform Setup Script
# This script sets up the environment for the AlphaGen platform

set -e

echo "🚀 Setting up AlphaGen Personal Investment Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Python 3.11+ is installed
print_status "Checking Python version..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.11"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
    print_error "Python ${PYTHON_VERSION} is installed, but Python ${REQUIRED_VERSION}+ is required."
    exit 1
fi

print_status "Python ${PYTHON_VERSION} is installed ✓"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
print_status "Upgrading pip..."
pip install --upgrade pip

# Install requirements
print_status "Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p logs data

# Copy environment template if .env doesn't exist
if [ ! -f ".env" ]; then
    print_status "Creating environment configuration file..."
    cp .env.template .env
    print_warning "Please edit .env file with your actual configuration values before running the application."
fi

# Check if PostgreSQL is running (optional)
print_status "Checking PostgreSQL connection..."
if command -v psql &> /dev/null; then
    if psql -h localhost -p 5432 -U alphauser -d alphagen -c '\q' 2>/dev/null; then
        print_status "PostgreSQL connection successful ✓"
    else
        print_warning "Could not connect to PostgreSQL. Make sure PostgreSQL is running and configured correctly."
        print_warning "You can use Docker Compose to start PostgreSQL: docker-compose up -d db"
    fi
else
    print_warning "PostgreSQL client (psql) not found. Database connection will be checked at runtime."
fi

# Make scripts executable
print_status "Making scripts executable..."
chmod +x scripts/*.sh

print_status "Setup completed successfully! 🎉"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your configuration"
echo "2. Start PostgreSQL database: docker-compose up -d db"
echo "3. Run database migration: python migrations/001_initial_schema.py"
echo "4. Initialize data pipeline: python -m src.data_pipeline.pipeline init"
echo "5. Start the API server: python -m src.api.main"
echo ""
echo "For automated data collection:"
echo "- Run: python -m src.data_pipeline.pipeline schedule"
echo ""
echo "For manual data collection:"
echo "- Run: python -m src.data_pipeline.pipeline collect --type all"
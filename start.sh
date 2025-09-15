#!/bin/bash

# AlphaGen Investment Platform - Master Startup Script
# This script starts all components of the application

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGS_DIR="$PROJECT_DIR/logs"
PID_DIR="$PROJECT_DIR/.pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create necessary directories
mkdir -p "$LOGS_DIR" "$PID_DIR"

echo -e "${BLUE}🚀 Starting AlphaGen Investment Platform...${NC}"
echo "Project Directory: $PROJECT_DIR"
echo "Logs Directory: $LOGS_DIR"
echo ""

# Function to check if a service is running
check_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "${YELLOW}⚠️  $service_name is already running (PID: $pid)${NC}"
            return 0
        else
            rm -f "$pid_file"
        fi
    fi
    return 1
}

# Function to start a service
start_service() {
    local service_name=$1
    local command=$2
    local log_file="$LOGS_DIR/${service_name}.log"
    local pid_file="$PID_DIR/${service_name}.pid"
    
    echo -e "${BLUE}📋 Starting $service_name...${NC}"
    
    if check_service "$service_name"; then
        return 0
    fi
    
    # Start the service in background
    nohup bash -c "$command" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"
    
    # Give it a moment to start
    sleep 2
    
    # Check if it's still running
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name started successfully (PID: $pid)${NC}"
        echo -e "   📄 Logs: $log_file"
    else
        echo -e "${RED}❌ Failed to start $service_name${NC}"
        echo -e "   📄 Check logs: $log_file"
        rm -f "$pid_file"
        return 1
    fi
}

# 1. Check for .env file
echo -e "${BLUE}🔍 Checking configuration...${NC}"
if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}❌ .env file not found!${NC}"
    echo -e "   Please copy .env.template to .env and configure your settings:"
    echo -e "   ${YELLOW}cp .env.template .env${NC}"
    echo -e "   ${YELLOW}nano .env${NC}"
    exit 1
else
    echo -e "${GREEN}✅ .env file found${NC}"
fi

# 2. Check Python dependencies
echo -e "${BLUE}🐍 Checking Python dependencies...${NC}"
cd "$PROJECT_DIR"
if ! python -c "import fastapi, uvicorn, sqlalchemy" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  Installing Python dependencies...${NC}"
    pip install -r requirements.txt || {
        echo -e "${RED}❌ Failed to install dependencies${NC}"
        exit 1
    }
fi
echo -e "${GREEN}✅ Python dependencies ready${NC}"

# 3. Start PostgreSQL database (if using Docker)
echo -e "${BLUE}🗄️  Starting PostgreSQL database...${NC}"
if [ -f "$PROJECT_DIR/docker-compose.yml" ]; then
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose up -d db || {
            echo -e "${RED}❌ Failed to start database with Docker Compose${NC}"
            exit 1
        }
        echo -e "${GREEN}✅ PostgreSQL database started${NC}"
        
        # Wait for database to be ready
        echo -e "${BLUE}⏳ Waiting for database to be ready...${NC}"
        sleep 5
    else
        echo -e "${YELLOW}⚠️  Docker Compose not found, assuming database is already running${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  docker-compose.yml not found, assuming database is already running${NC}"
fi

# 4. Run database migrations/setup
echo -e "${BLUE}🔧 Running database setup...${NC}"
python -m src.database.database check || {
    echo -e "${YELLOW}⚠️  Database connection failed, attempting to create tables...${NC}"
    python -m src.database.database init || {
        echo -e "${RED}❌ Database setup failed${NC}"
        exit 1
    }
}
echo -e "${GREEN}✅ Database ready${NC}"

# 5. Start FastAPI server
echo -e "${BLUE}🌐 Starting FastAPI server...${NC}"
API_COMMAND="cd '$PROJECT_DIR' && python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"
start_service "api" "$API_COMMAND"

# 6. Start scheduled data pipeline (if available)
echo -e "${BLUE}📊 Starting data pipeline scheduler...${NC}"
if [ -f "$PROJECT_DIR/src/data_pipeline/scheduler.py" ]; then
    PIPELINE_COMMAND="cd '$PROJECT_DIR' && python -m src.data_pipeline.scheduler"
    start_service "pipeline" "$PIPELINE_COMMAND"
else
    echo -e "${YELLOW}⚠️  Scheduler not found, skipping automated pipeline${NC}"
fi

# 7. Show status
echo ""
echo -e "${GREEN}🎉 AlphaGen Investment Platform Started Successfully!${NC}"
echo ""
echo -e "${BLUE}📊 Service Status:${NC}"
echo -e "   🌐 API Server: http://localhost:8000"
echo -e "   📚 API Docs: http://localhost:8000/docs"
echo -e "   ❤️  Health Check: http://localhost:8000/health"
echo ""
echo -e "${BLUE}📄 Logs Directory: $LOGS_DIR${NC}"
echo -e "${BLUE}🔧 PID Files: $PID_DIR${NC}"
echo ""
echo -e "${BLUE}🛑 To stop all services, run:${NC} ${YELLOW}./stop.sh${NC}"
echo ""
echo -e "${BLUE}📋 Available API Endpoints:${NC}"
echo -e "   GET  /api/v1/recommendations/"
echo -e "   GET  /api/v1/recommendations/{symbol}"
echo -e "   GET  /api/v1/scores/quantitative/{symbol}"
echo -e "   GET  /api/v1/scores/qualitative/{symbol}"
echo -e "   GET  /api/v1/history/scores/{symbol}"
echo -e "   POST /api/v1/portfolio/{portfolio_name}/trade"
echo -e "   GET  /api/v1/portfolio/{portfolio_name}"
echo -e "   GET  /api/v1/risk/{symbol}"
echo ""

# Optional: Monitor logs in the background
if command -v tail >/dev/null 2>&1; then
    echo -e "${BLUE}📖 Monitoring logs... (Press Ctrl+C to stop monitoring)${NC}"
    trap 'echo -e "\n${BLUE}👋 Log monitoring stopped. Services are still running.${NC}"; exit 0' INT
    tail -f "$LOGS_DIR"/*.log 2>/dev/null || {
        echo -e "${YELLOW}⚠️  No logs to monitor yet${NC}"
        echo -e "${BLUE}✅ All services started. Check individual log files for details.${NC}"
    }
fi
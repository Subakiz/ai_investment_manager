#!/bin/bash

# AlphaGen Investment Platform - Shutdown Script
# This script gracefully stops all components of the application

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="$PROJECT_DIR/.pids"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping AlphaGen Investment Platform...${NC}"
echo "Project Directory: $PROJECT_DIR"
echo ""

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="$PID_DIR/${service_name}.pid"
    
    echo -e "${BLUE}🔄 Stopping $service_name...${NC}"
    
    if [ ! -f "$pid_file" ]; then
        echo -e "${YELLOW}⚠️  $service_name PID file not found${NC}"
        return 0
    fi
    
    local pid=$(cat "$pid_file")
    
    if ! ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  $service_name is not running${NC}"
        rm -f "$pid_file"
        return 0
    fi
    
    # Try graceful shutdown first
    echo -e "   📤 Sending SIGTERM to $service_name (PID: $pid)..."
    kill "$pid" 2>/dev/null || true
    
    # Wait for graceful shutdown
    local count=0
    while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
        echo -e "   ⏳ Waiting for graceful shutdown... ($count/10)"
    done
    
    # Force kill if still running
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "   💀 Force killing $service_name..."
        kill -9 "$pid" 2>/dev/null || true
        sleep 2
    fi
    
    # Clean up PID file
    rm -f "$pid_file"
    
    if ps -p "$pid" > /dev/null 2>&1; then
        echo -e "${RED}❌ Failed to stop $service_name${NC}"
        return 1
    else
        echo -e "${GREEN}✅ $service_name stopped${NC}"
        return 0
    fi
}

# Stop services in reverse order
services=("pipeline" "api")

for service in "${services[@]}"; do
    stop_service "$service"
done

# Stop Docker services if available
if [ -f "$PROJECT_DIR/docker-compose.yml" ] && command -v docker-compose >/dev/null 2>&1; then
    echo -e "${BLUE}🐳 Stopping Docker services...${NC}"
    cd "$PROJECT_DIR"
    docker-compose stop || {
        echo -e "${YELLOW}⚠️  Failed to stop some Docker services${NC}"
    }
    echo -e "${GREEN}✅ Docker services stopped${NC}"
fi

# Clean up any remaining processes (careful approach)
echo -e "${BLUE}🧹 Cleaning up remaining processes...${NC}"

# Find and kill any remaining AlphaGen processes
remaining_pids=$(ps aux | grep -E "(uvicorn|src\.api\.main|src\.data_pipeline)" | grep -v grep | awk '{print $2}' || true)

if [ -n "$remaining_pids" ]; then
    echo -e "${YELLOW}⚠️  Found remaining processes, terminating...${NC}"
    for pid in $remaining_pids; do
        if ps -p "$pid" > /dev/null 2>&1; then
            echo -e "   🔫 Terminating process $pid"
            kill "$pid" 2>/dev/null || true
        fi
    done
    sleep 2
    
    # Force kill any stubborn processes
    remaining_pids=$(ps aux | grep -E "(uvicorn|src\.api\.main|src\.data_pipeline)" | grep -v grep | awk '{print $2}' || true)
    if [ -n "$remaining_pids" ]; then
        echo -e "${YELLOW}⚠️  Force killing stubborn processes...${NC}"
        for pid in $remaining_pids; do
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" 2>/dev/null || true
            fi
        done
    fi
fi

# Clean up PID directory
if [ -d "$PID_DIR" ]; then
    echo -e "${BLUE}🧹 Cleaning up PID files...${NC}"
    rm -f "$PID_DIR"/*.pid
    rmdir "$PID_DIR" 2>/dev/null || true
fi

# Final status check
echo ""
echo -e "${GREEN}🎉 AlphaGen Investment Platform Stopped Successfully!${NC}"
echo ""

# Check if any related processes are still running
remaining_procs=$(ps aux | grep -E "(uvicorn|src\.api\.main|src\.data_pipeline)" | grep -v grep | wc -l || echo "0")
if [ "$remaining_procs" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Warning: $remaining_procs related processes may still be running${NC}"
    echo -e "   Use: ${BLUE}ps aux | grep -E '(uvicorn|src\.api\.main|src\.data_pipeline)'${NC} to check"
else
    echo -e "${GREEN}✅ All AlphaGen processes stopped cleanly${NC}"
fi

echo ""
echo -e "${BLUE}📋 Summary:${NC}"
echo -e "   🌐 API Server: Stopped"
echo -e "   📊 Data Pipeline: Stopped"
echo -e "   🐳 Docker Services: Stopped"
echo ""
echo -e "${BLUE}🚀 To restart the platform, run:${NC} ${YELLOW}./start.sh${NC}"
echo ""
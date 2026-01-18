#!/bin/bash
# ==========================================
# Echolet Development Server
# Starts backend, agent, and worker locally
# ==========================================
# Usage: ./dev.sh [all|backend|agent|worker]
# ==========================================

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE="${1:-all}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# PIDs for cleanup
PIDS=()

cleanup() {
    echo ""
    echo -e "${YELLOW}[*] Shutting down services...${NC}"
    for pid in "${PIDS[@]}"; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    wait 2>/dev/null
    echo -e "${GREEN}[✓] All services stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Load environment variables from .env
load_env() {
    if [ -f "$ROOT_DIR/.env" ]; then
        echo -e "${CYAN}[*] Loading environment from .env${NC}"
        set -a
        source "$ROOT_DIR/.env"
        set +a
    else
        echo -e "${YELLOW}[!] No .env file found. Copy .env.example to .env${NC}"
        exit 1
    fi
}

# Start backend
start_backend() {
    echo -e "${GREEN}[+] Starting Backend API...${NC}"
    cd "$ROOT_DIR/backend"
    uv run uvicorn main:app --host 127.0.0.1 --port 8000 --reload &
    PIDS+=($!)
    cd "$ROOT_DIR"
}

# Start agent
start_agent() {
    echo -e "${GREEN}[+] Starting Voice Agent...${NC}"
    cd "$ROOT_DIR/agent"
    uv run python agent.py dev &
    PIDS+=($!)
    cd "$ROOT_DIR"
}

# Start worker
start_worker() {
    echo -e "${GREEN}[+] Starting SQS Worker...${NC}"
    cd "$ROOT_DIR/worker"
    uv run python worker.py &
    PIDS+=($!)
    cd "$ROOT_DIR"
}

# Main
echo ""
echo -e "${MAGENTA}========================================${NC}"
echo -e "${MAGENTA}   Echolet Development Environment${NC}"
echo -e "${MAGENTA}========================================${NC}"
echo ""

load_env

case "$SERVICE" in
    all)
        start_backend
        sleep 0.5
        start_agent
        sleep 0.5
        start_worker
        echo ""
        echo -e "${GREEN}[✓] All services started${NC}"
        echo ""
        echo -e "${CYAN}Services:${NC}"
        echo "  Backend API:  http://localhost:8000"
        echo "  Agent:        LiveKit dev mode"
        echo "  Worker:       SQS polling"
        echo ""
        echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"
        echo ""
        # Wait for all background processes
        wait
        ;;
    backend)
        start_backend
        wait
        ;;
    agent)
        start_agent
        wait
        ;;
    worker)
        start_worker
        wait
        ;;
    *)
        echo -e "${RED}Unknown service: $SERVICE${NC}"
        echo -e "${YELLOW}Usage: ./dev.sh [all|backend|agent|worker]${NC}"
        exit 1
        ;;
esac

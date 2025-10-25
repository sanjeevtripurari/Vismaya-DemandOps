#!/bin/bash
# Cross-platform Docker startup script for Vismaya DemandOps
# Works on Linux, Mac, and Windows (with Git Bash/WSL)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="Vismaya DemandOps"
CONTAINER_NAME="vismaya-demandops"
HEALTH_URL="http://localhost:8501/_stcore/health"
APP_URL="http://localhost:8501"

echo -e "${BLUE}🚀 Starting ${PROJECT_NAME}${NC}"
echo "=================================="

# Function to print colored output
print_status() {
    local message=$1
    local status=${2:-"INFO"}
    
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️ $message${NC}"
            ;;
        *)
            echo -e "${BLUE}ℹ️ $message${NC}"
            ;;
    esac
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_status "Docker not found. Please install Docker Desktop." "ERROR"
        echo "Download from: https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_status "Docker Compose not found. Please install Docker Compose." "ERROR"
        exit 1
    fi
    
    # Determine compose command
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    print_status "Docker and Docker Compose found" "SUCCESS"
}

# Setup environment
setup_environment() {
    print_status "Setting up environment..."
    
    # Check if .env exists
    if [ ! -f "../.env" ]; then
        if [ -f "../.env.example" ]; then
            print_status "Creating .env from template..."
            cp ../.env.example ../.env
            print_status "Please edit .env with your AWS credentials" "WARNING"
            echo "Required variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION"
            read -p "Press Enter when ready to continue..."
        else
            print_status ".env.example not found" "ERROR"
            exit 1
        fi
    fi
    
    # Create logs directory if it doesn't exist
    mkdir -p ../logs
    
    print_status "Environment setup complete" "SUCCESS"
}

# Start services
start_services() {
    print_status "Starting Docker services..."
    
    # Stop any existing containers
    $COMPOSE_CMD down 2>/dev/null || true
    
    # Build and start
    $COMPOSE_CMD up -d --build
    
    if [ $? -eq 0 ]; then
        print_status "Services started successfully" "SUCCESS"
    else
        print_status "Failed to start services" "ERROR"
        exit 1
    fi
}

# Wait for health check
wait_for_health() {
    print_status "Waiting for application to be ready..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f $HEALTH_URL &> /dev/null; then
            print_status "Application is healthy and ready!" "SUCCESS"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_status "Application failed to become healthy" "WARNING"
    print_status "Check logs with: $COMPOSE_CMD logs -f" "INFO"
}

# Show status
show_status() {
    echo ""
    print_status "🎉 ${PROJECT_NAME} is running!" "SUCCESS"
    echo ""
    echo -e "${GREEN}📊 Application URL: ${APP_URL}${NC}"
    echo -e "${BLUE}📋 View logs: ${COMPOSE_CMD} logs -f${NC}"
    echo -e "${BLUE}🛑 Stop services: ${COMPOSE_CMD} down${NC}"
    echo ""
    
    # Try to open browser (cross-platform)
    if command -v xdg-open &> /dev/null; then
        # Linux
        xdg-open $APP_URL &> /dev/null &
    elif command -v open &> /dev/null; then
        # Mac
        open $APP_URL &> /dev/null &
    elif command -v start &> /dev/null; then
        # Windows
        start $APP_URL &> /dev/null &
    else
        print_status "Please open ${APP_URL} in your browser" "INFO"
    fi
}

# Main execution
main() {
    check_prerequisites
    setup_environment
    start_services
    wait_for_health
    show_status
}

# Run main function
main "$@"
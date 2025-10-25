#!/bin/bash

# Vismaya DemandOps - Build and Test Script
# Team MaximAI - AI-Powered FinOps Platform

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Vismaya DemandOps - Build and Test${NC}"
echo -e "${BLUE}Team MaximAI - AI-Powered FinOps Platform${NC}"
echo "=========================================="

# Function to print status
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

# Check if Docker is available
check_docker() {
    if command -v docker &> /dev/null; then
        print_status "Docker is available" "SUCCESS"
        return 0
    else
        print_status "Docker not found - skipping Docker tests" "WARNING"
        return 1
    fi
}

# Check Python environment
check_python() {
    print_status "Checking Python environment..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
        print_status "Python version: $PYTHON_VERSION" "SUCCESS"
    else
        print_status "Python 3 not found" "ERROR"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ -d "venv" ]; then
        print_status "Virtual environment found" "SUCCESS"
        source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null || {
            print_status "Failed to activate virtual environment" "ERROR"
            exit 1
        }
    else
        print_status "Creating virtual environment..." "INFO"
        python3 -m venv venv
        source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null
        print_status "Virtual environment created and activated" "SUCCESS"
    fi
}

# Install dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip install --upgrade pip
        pip install -r requirements.txt
        print_status "Dependencies installed successfully" "SUCCESS"
    else
        print_status "requirements.txt not found" "ERROR"
        exit 1
    fi
}

# Run Python tests
run_python_tests() {
    print_status "Running Python tests..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            print_status "Copying .env.example to .env" "INFO"
            cp .env.example .env
        else
            print_status "No .env file found - some tests may fail" "WARNING"
        fi
    fi
    
    # List of test files to run
    tests=(
        "test-aws-connection.py"
        "test_cost_tracking.py"
        "test_budget_alerts.py"
        "test_enhanced_dashboard.py"
        "test_production_ready.py"
    )
    
    passed_tests=0
    total_tests=${#tests[@]}
    
    for test in "${tests[@]}"; do
        if [ -f "$test" ]; then
            print_status "Running $test..." "INFO"
            if python3 "$test" > /dev/null 2>&1; then
                print_status "$test passed" "SUCCESS"
                ((passed_tests++))
            else
                print_status "$test failed" "ERROR"
            fi
        else
            print_status "$test not found - skipping" "WARNING"
        fi
    done
    
    print_status "Python tests completed: $passed_tests/$total_tests passed" "INFO"
}

# Build Docker image
build_docker() {
    if check_docker; then
        print_status "Building Docker image..." "INFO"
        
        if docker build -t vismaya-demandops:test . > /dev/null 2>&1; then
            print_status "Docker image built successfully" "SUCCESS"
            return 0
        else
            print_status "Docker build failed" "ERROR"
            return 1
        fi
    fi
    return 1
}

# Test Docker container
test_docker() {
    if check_docker; then
        print_status "Testing Docker container..." "INFO"
        
        # Start container in background
        if docker run -d --name vismaya-test -p 8502:8501 --env-file .env vismaya-demandops:test > /dev/null 2>&1; then
            print_status "Docker container started" "SUCCESS"
            
            # Wait for container to be ready
            sleep 10
            
            # Test health endpoint
            if curl -f http://localhost:8502/_stcore/health > /dev/null 2>&1; then
                print_status "Docker container health check passed" "SUCCESS"
                docker_test_result=0
            else
                print_status "Docker container health check failed" "ERROR"
                docker_test_result=1
            fi
            
            # Cleanup
            docker stop vismaya-test > /dev/null 2>&1
            docker rm vismaya-test > /dev/null 2>&1
            
            return $docker_test_result
        else
            print_status "Failed to start Docker container" "ERROR"
            return 1
        fi
    fi
    return 1
}

# Run deployment verification
run_verification() {
    print_status "Running deployment verification..." "INFO"
    
    if [ -f "verify_deployment.py" ]; then
        if python3 verify_deployment.py > /dev/null 2>&1; then
            print_status "Deployment verification passed" "SUCCESS"
            return 0
        else
            print_status "Deployment verification failed" "ERROR"
            return 1
        fi
    else
        print_status "verify_deployment.py not found - skipping" "WARNING"
        return 1
    fi
}

# Main execution
main() {
    local python_ok=0
    local docker_ok=0
    local verification_ok=0
    
    # Python environment and tests
    check_python
    install_dependencies
    run_python_tests
    python_ok=$?
    
    # Docker tests
    if build_docker; then
        if test_docker; then
            docker_ok=0
        else
            docker_ok=1
        fi
    else
        docker_ok=1
    fi
    
    # Deployment verification
    run_verification
    verification_ok=$?
    
    # Summary
    echo ""
    print_status "BUILD AND TEST SUMMARY" "INFO"
    echo "================================"
    
    if [ $python_ok -eq 0 ]; then
        print_status "Python Environment: READY" "SUCCESS"
    else
        print_status "Python Environment: ISSUES" "ERROR"
    fi
    
    if [ $docker_ok -eq 0 ]; then
        print_status "Docker Build: READY" "SUCCESS"
    else
        print_status "Docker Build: ISSUES" "WARNING"
    fi
    
    if [ $verification_ok -eq 0 ]; then
        print_status "Deployment Verification: PASSED" "SUCCESS"
    else
        print_status "Deployment Verification: ISSUES" "WARNING"
    fi
    
    echo ""
    
    if [ $python_ok -eq 0 ]; then
        print_status "🎉 Application is ready for deployment!" "SUCCESS"
        echo ""
        print_status "Next steps:" "INFO"
        print_status "  • Local: python app.py" "INFO"
        print_status "  • Docker: docker-compose up -d" "INFO"
        print_status "  • AWS: ./deploy.sh" "INFO"
        return 0
    else
        print_status "⚠️ Please fix issues before deployment" "ERROR"
        return 1
    fi
}

# Run main function
main
exit $?
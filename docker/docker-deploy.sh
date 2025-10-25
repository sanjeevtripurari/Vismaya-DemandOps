#!/bin/bash

# Docker Deployment Script for Vismaya DemandOps

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="vismaya-demandops"
CONTAINER_NAME="vismaya"
PORT="8501"
REGION="us-east-2"

echo -e "${BLUE}🐳 Vismaya DemandOps - Docker Deployment${NC}"
echo -e "${BLUE}Team MaximAI - AI-Powered FinOps Platform${NC}"
echo "=============================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found. Please install Docker first${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose not found. Please install Docker Compose first${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose found${NC}"

# Function to build image
build_image() {
    echo -e "${YELLOW}🔨 Building Docker image...${NC}"
    docker build -t $IMAGE_NAME .
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Image built successfully${NC}"
    else
        echo -e "${RED}❌ Image build failed${NC}"
        exit 1
    fi
}

# Function to run with Docker Compose
run_compose() {
    echo -e "${YELLOW}🚀 Starting with Docker Compose...${NC}"
    
    # Stop existing containers
    docker-compose down 2>/dev/null || true
    
    # Start services
    docker-compose up -d
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Application started successfully${NC}"
        echo -e "${BLUE}📊 Dashboard available at: http://localhost:$PORT${NC}"
    else
        echo -e "${RED}❌ Failed to start application${NC}"
        exit 1
    fi
}

# Function to run with plain Docker
run_docker() {
    echo -e "${YELLOW}🚀 Starting with Docker...${NC}"
    
    # Stop and remove existing container
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
    
    # Run new container
    docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:$PORT \
        --env-file .env \
        --restart unless-stopped \
        $IMAGE_NAME
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Container started successfully${NC}"
        echo -e "${BLUE}📊 Dashboard available at: http://localhost:$PORT${NC}"
    else
        echo -e "${RED}❌ Failed to start container${NC}"
        exit 1
    fi
}

# Function to push to ECR
push_to_ecr() {
    echo -e "${YELLOW}📤 Pushing to Amazon ECR...${NC}"
    
    # Get AWS account ID
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to get AWS account ID${NC}"
        exit 1
    fi
    
    ECR_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$IMAGE_NAME"
    
    # Create ECR repository if it doesn't exist
    aws ecr describe-repositories --repository-names $IMAGE_NAME --region $REGION 2>/dev/null || \
    aws ecr create-repository --repository-name $IMAGE_NAME --region $REGION
    
    # Get login token
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ECR_URI
    
    # Tag and push image
    docker tag $IMAGE_NAME:latest $ECR_URI:latest
    docker push $ECR_URI:latest
    
    echo -e "${GREEN}✅ Image pushed to ECR: $ECR_URI:latest${NC}"
}

# Function to show logs
show_logs() {
    echo -e "${YELLOW}📋 Showing application logs...${NC}"
    
    if docker ps | grep -q $CONTAINER_NAME; then
        docker logs -f --tail 50 $CONTAINER_NAME
    elif docker-compose ps | grep -q vismaya; then
        docker-compose logs -f --tail 50
    else
        echo -e "${RED}❌ No running containers found${NC}"
    fi
}

# Function to show status
show_status() {
    echo -e "${YELLOW}📊 Application Status${NC}"
    echo "===================="
    
    # Check Docker container
    if docker ps | grep -q $CONTAINER_NAME; then
        echo -e "${GREEN}✅ Docker container is running${NC}"
        docker ps --filter name=$CONTAINER_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    elif docker-compose ps | grep -q vismaya; then
        echo -e "${GREEN}✅ Docker Compose services are running${NC}"
        docker-compose ps
    else
        echo -e "${RED}❌ No containers are running${NC}"
    fi
    
    # Check if port is accessible
    if curl -s http://localhost:$PORT/_stcore/health > /dev/null; then
        echo -e "${GREEN}✅ Application is healthy${NC}"
    else
        echo -e "${RED}❌ Application is not responding${NC}"
    fi
}

# Function to cleanup
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    
    # Stop and remove containers
    docker-compose down 2>/dev/null || true
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
    
    # Remove unused images
    docker image prune -f
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Main menu
case "${1:-menu}" in
    "build")
        build_image
        ;;
    "compose")
        build_image
        run_compose
        ;;
    "docker")
        build_image
        run_docker
        ;;
    "push")
        build_image
        push_to_ecr
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "cleanup")
        cleanup
        ;;
    "menu"|*)
        echo "Usage: $0 {build|compose|docker|push|logs|status|cleanup}"
        echo ""
        echo "Commands:"
        echo "  build    - Build Docker image"
        echo "  compose  - Build and run with Docker Compose"
        echo "  docker   - Build and run with plain Docker"
        echo "  push     - Build and push to Amazon ECR"
        echo "  logs     - Show application logs"
        echo "  status   - Show application status"
        echo "  cleanup  - Stop containers and cleanup"
        echo ""
        echo "Examples:"
        echo "  $0 compose  # Start with Docker Compose"
        echo "  $0 logs     # View logs"
        echo "  $0 status   # Check status"
        ;;
esac
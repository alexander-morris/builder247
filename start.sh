#!/bin/bash

# Exit on any error
set -e

# Function to cleanup on exit
cleanup() {
    echo "Cleaning up..."
    docker stop ai-agent-container 2>/dev/null || true
    docker rm ai-agent-container 2>/dev/null || true
}

# Function to handle errors
handle_error() {
    echo "Error occurred on line $1"
    cleanup
    exit 1
}

# Set up error trap
trap 'handle_error $LINENO' ERR

# Set up cleanup trap
trap cleanup EXIT

# Create logs directory if it doesn't exist
mkdir -p logs

# Check if .env file exists and load it
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    exit 1
fi

# Remove existing container if it exists
echo "Removing any existing containers..."
docker rm -f ai-agent-container 2>/dev/null || true

echo "Building Docker container..."
if ! docker build -t ai-agent-container .; then
    echo "Error: Docker build failed!"
    exit 1
fi

echo "Starting container..."
if ! docker run -d --name ai-agent-container \
    -p 2222:22 \
    --env-file .env \
    -v "$(pwd)/logs:/app/logs" \
    -v "$(pwd)/src:/app/src" \
    -v "$(pwd)/tests:/app/tests" \
    ai-agent-container; then
    echo "Error: Failed to start container!"
    exit 1
fi

echo "Waiting for agent setup to complete..."
sleep 2

# Wait for setup to complete by checking logs
while ! docker logs ai-agent-container 2>&1 | grep -q "Environment setup completed successfully"; do
    if ! docker ps | grep -q ai-agent-container; then
        echo "Error: Container failed to start properly!"
        docker logs ai-agent-container
        exit 1
    fi
    echo "Still waiting for setup..."
    sleep 2
done

echo -e "\nSetup completed successfully!"
echo "Opening shell access to container..."
echo "Note: The agent CLI is running in the background. To access it, run 'python src/main.py'"
echo "----------------------------------------"

# Open shell in container
docker exec -it ai-agent-container /bin/bash 
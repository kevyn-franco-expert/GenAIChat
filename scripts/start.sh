#!/bin/bash

# Set up environment if needed
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file with your AWS credentials before running the application."
    exit 1
fi

# Start the application with Docker Compose
docker-compose up -d

# Wait for the API to be ready
echo "Waiting for API to start..."
sleep 5

# Check if the API is running
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)

if [ $response -eq 200 ]; then
    echo "API is running! Access it at: http://localhost:8000"
    echo "API documentation available at: http://localhost:8000/docs"
else
    echo "API is not responding. Check logs with: docker-compose logs -f api"
fi
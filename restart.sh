#!/bin/bash

echo "Stopping Docker Compose services..."
docker compose down

docker volume prune -af
echo "Starting Docker Compose services in detached mode..."
docker compose up -d

echo "Services have been restarted successfully!"
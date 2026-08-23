#!/bin/bash

# Exit on any error
set -e

echo "=========================================="
echo "🚀 Car Pricing ML Engine - Zero Downtime Deployment"
echo "=========================================="

# echo "[1/4] Updating system packages (Skipped during fast deploy)..."
# sudo apt-get update -y
# sudo apt-get upgrade -y

echo "[1/3] Pulling latest code..."
git pull origin main || echo "Git pull failed or not in a git repository. Proceeding with local files."

echo "[2/3] Building new Docker images in the background..."
# Build images WITHOUT stopping the currently running containers
sudo docker-compose build

echo "[3/3] Deploying with Zero Downtime..."
# Upgrading containers (Docker Compose recreates them instantly if image changed)
sudo docker-compose up -d

echo "⏳ Waiting 10 seconds for the ML Engine to load data..."
sleep 10

echo "🔄 Reloading Nginx to clear any stale DNS cache..."
sudo docker-compose exec -T nginx nginx -s reload || echo "Nginx reload failed, it might not be fully up yet."

echo "=========================================="
echo "✅ Deployment Complete! System is fully zırhlı."
echo "API is running on port 8000"
echo "Frontend is running on port 3000"
echo "=========================================="

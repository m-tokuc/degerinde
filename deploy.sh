#!/bin/bash

# Exit on any error
set -e

echo "=========================================="
echo "🚀 Car Pricing ML Engine - Deployment Script"
echo "=========================================="

echo "[1/4] Updating system packages..."
sudo apt-get update -y
sudo apt-get upgrade -y

echo "[2/4] Installing Docker and Docker Compose..."
# Install prerequisites
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Compose
sudo apt-get update -y
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin docker-compose

# Start and enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Add current user to the docker group so we can run docker without sudo (requires re-login or newgroup)
sudo usermod -aG docker $USER

echo "[3/4] Pulling latest code..."
# (Assuming the repo is already cloned if this script is running from it. If not, add git pull origin main here)

echo "[4/4] Spinning up Docker containers..."
# Use sudo to run docker-compose just in case the group change hasn't taken effect in the current session
sudo docker-compose up -d --build

echo "=========================================="
echo "✅ Deployment Complete!"
echo "API is running on port 8000"
echo "Frontend is running on port 3000"
echo "=========================================="

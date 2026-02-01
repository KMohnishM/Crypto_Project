#!/bin/bash
# Setup script for development environment

# Create necessary directories
mkdir -p ./data/patient_samples

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker and Docker Compose."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose."
    exit 1
fi

# Install Python dependencies for local development
echo "Installing Python dependencies for local development..."
pip install -r services/main_host/requirements.txt
pip install -r services/ml_service/requirements.txt
pip install -r services/patient_simulator/requirements.txt

echo "Setup complete! You can now run the system with: docker-compose up"
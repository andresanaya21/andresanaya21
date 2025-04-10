#!/bin/bash

# Install dependencies
sudo apt update
sudo apt install -y python3-pip

# Clone or upload project
git clone <your-repo-url>
cd mock_api
pip3 install -r requirements.txt

# Run FastAPI server
nohup uvicorn main:app --host 0.0.0.0 --port 8000 &

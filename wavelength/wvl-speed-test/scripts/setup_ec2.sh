#!/bin/bash
sudo yum update -y
sudo yum install python3 git -y
pip3 install fastapi uvicorn

# Create app directory
mkdir -p ~/ogw-api && cd ~/ogw-api

# Save this as server.py
cat <<EOF > server.py
from fastapi import FastAPI
import random
from datetime import datetime

app = FastAPI()

@app.get("/api/v1/getNetworkQuality")
def get_qos(ueId: str):
    return {
        "ueId": ueId,
        "latency": round(random.uniform(10, 40), 2),
        "bandwidth": round(random.uniform(20, 80), 2),
        "jitter": round(random.uniform(1, 5), 2),
        "timestamp": datetime.utcnow().isoformat()
    }
EOF

# Launch the API server
nohup uvicorn server:app --host 0.0.0.0 --port 8000 &
echo "🚀 API server running on port 8000"

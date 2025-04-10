from fastapi import FastAPI, Query
import random
import time

app = FastAPI()

@app.get("/api/v1/networkQuality")
def get_network_quality(ueId: str = Query(...)):
    simulated_latency = random.uniform(10, 80)  # Simulate different zones
    simulated_bandwidth = random.uniform(20, 100)
    simulated_jitter = random.uniform(1, 10)

    # Optional: simulate delay
    time.sleep(simulated_latency / 1000.0)

    return {
        "ueId": ueId,
        "latency": round(simulated_latency, 2),
        "bandwidth": round(simulated_bandwidth, 2),
        "jitter": round(simulated_jitter, 2),
    }

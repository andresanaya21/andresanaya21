from flask import Flask, jsonify
import requests
import time

app = Flask(__name__)

@app.route('/')
def index():
    start_time = time.time()
    response = requests.get('http://nginx-service:80')
    latency = (time.time() - start_time) * 1000
    return jsonify({'latency': latency})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

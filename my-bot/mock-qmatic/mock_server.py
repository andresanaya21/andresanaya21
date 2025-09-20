from flask import Flask, send_from_directory, request, jsonify
from datetime import datetime
import os

app = Flask(__name__, static_url_path='', static_folder='static')

# Simple API to simulate dynamic behavior
@app.get('/api/config')
def api_config():
    # Query params to simulate scenarios
    no_slots = request.args.get('no_slots', '0') == '1'
    captcha = request.args.get('captcha', '0') == '1'
    earliest_only = request.args.get('earliest_only', '0') == '1'
    return jsonify({
        "no_slots": no_slots,
        "captcha": captcha,
        "earliest_only": earliest_only,
        "today": datetime.now().strftime("%Y-%m-%d")
    })

@app.route('/')
def root():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(host='0.0.0.0', port=5173, debug=True)

from flask import Flask, send_from_directory, request, jsonify
import json, os

app = Flask(__name__, static_url_path='', static_folder='static')

@app.get('/api/schema')
def api_schema():
    with open('schema.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    # pass-through query flags to simulate site states
    data["flags"] = {
        "no_slots": request.args.get("no_slots") == "1",
        "captcha": request.args.get("captcha") == "1"
    }
    return jsonify(data)

@app.route('/')
def root():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(host='0.0.0.0', port=5173, debug=True)

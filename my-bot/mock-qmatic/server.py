from flask import Flask, send_from_directory, request, jsonify, Response
import json, os

app = Flask(__name__, static_url_path='', static_folder='static')

@app.get('/api/schema')
def api_schema():
    try:
        with open('schema.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return Response(f"schema.json is invalid JSON:\n{e}", status=500, mimetype="text/plain")

    # Optional flags via query string (e.g., ?no_slots=1)
    flags = {
        "no_slots": request.args.get("no_slots") == "1",
        "captcha": request.args.get("captcha") == "1"
    }
    data["flags"] = flags
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

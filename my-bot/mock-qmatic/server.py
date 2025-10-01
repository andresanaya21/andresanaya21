from flask import Flask, send_from_directory, request, jsonify, Response
import json, os

app = Flask(__name__, static_url_path='', static_folder='static')

DEFAULT_TIMES = ["09:00", "09:20", "09:40", "10:00", "10:20", "10:40"]

def ensure_times_for_enabled_days(schema, no_slots: bool):
  fh = schema.get("fecha_hora", {})
  months = fh.get("months", [])
  for m in months:
    year = m.get("year")
    month = m.get("month")
    enabled_days = m.get("enabled_days", [])
    times_map = m.setdefault("times_by_date", {})

    if enabled_days is None:  # only when omitted -> all days enabled; we won't try to guess times
      continue

    for dd in enabled_days:
      try:
        d_int = int(dd)
      except ValueError:
        continue
      if not (1 <= d_int <= 31):
        continue
      iso = f"{year:04d}-{month:02d}-{d_int:02d}"
      if iso not in times_map:
        times_map[iso] = [] if no_slots else list(DEFAULT_TIMES)
  return schema

@app.get('/api/schema')
def api_schema():
  try:
    with open('schema.json', 'r', encoding='utf-8') as f:
      data = json.load(f)
  except json.JSONDecodeError as e:
    return Response(f"schema.json is invalid JSON:\n{e}", status=500, mimetype="text/plain")

  no_slots = request.args.get("no_slots") == "1"
  data["flags"] = { "no_slots": no_slots }

  data = ensure_times_for_enabled_days(data, no_slots=no_slots)
  return jsonify(data)

@app.route('/')
def root(): return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def static_proxy(path): return send_from_directory('static', path)

if __name__ == '__main__':
  os.makedirs('static', exist_ok=True)
  app.run(host='0.0.0.0', port=5173, debug=True)
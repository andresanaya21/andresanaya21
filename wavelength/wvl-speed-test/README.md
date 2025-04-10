🔨 Build all 
---

docker build -t mock_api_region ./mock_api
docker build -t cli_tool ./cli_tool
docker build -t web_ui ./web_ui

🧪 Test run:
-----

# Run the API
docker run -p 8000:8000 mock_api_region

# Or the CLI
docker run --rm cli_tool python speedtest.py

# Or Streamlit UI
docker run -p 8501:8501 web_ui

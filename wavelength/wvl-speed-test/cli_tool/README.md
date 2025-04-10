cd cli_tool
pip install -r requirements.txt
python speedtest.py

---

docker run --rm cli_tool python speedtest.py --api getNetworkQuality --ue-id 12345

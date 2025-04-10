import streamlit as st
import requests
import time
import os
import pandas as pd

# API URLs (internal Docker names or env vars)
base_region = os.getenv("REGION_API", "http://mock-api-region:8000/api/v1")
base_edge = os.getenv("EDGE_API", "http://mock-api-wavelength:8000/api/v1")

st.set_page_config(page_title="OG Speed Tester", layout="centered")
st.title("🚀 Open Gateway Latency Speed Tester")

ue_id = st.text_input("📱 Enter UE ID", "12345")
run_test = st.button("🧪 Run Test")

def test_latency(url):
    start = time.time()
    response = requests.get(url)
    latency = (time.time() - start) * 1000  # in ms
    return round(latency, 2), response.json()

if run_test:
    url_r = f"{base_region}/networkQuality?ueId={ue_id}"
    url_e = f"{base_edge}/networkQuality?ueId={ue_id}"

    st.subheader("⏱️ Latency Measurements")

    try:
        latency_r, data_r = test_latency(url_r)
        latency_e, data_e = test_latency(url_e)

        # Show metric blocks
        col1, col2 = st.columns(2)
        col1.metric("🌎 Region Latency", f"{latency_r:.2f} ms")
        col2.metric("🏙️ Wavelength Latency", f"{latency_e:.2f} ms")

        # Visual comparison bar chart
        df = pd.DataFrame({
            "Zone": ["Region", "Wavelength"],
            "Latency (ms)": [latency_r, latency_e]
        })
        st.bar_chart(df.set_index("Zone"))

        # Speed advantage
        if latency_e > 0:
            boost = latency_r / latency_e
            st.success(f"⚡ Edge is **{boost:.2f}x** faster than Region!")
        else:
            st.warning("⚠️ Wavelength latency is zero (check API).")

        # Optional detailed stats
        st.subheader("📦 API Response")
        st.json({
            "Region": data_r,
            "Wavelength": data_e
        })

    except requests.exceptions.RequestException as e:
        st.error(f"🚨 Request failed: {e}")

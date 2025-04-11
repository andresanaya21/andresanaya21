import streamlit as st
import requests
import time
import os
import pandas as pd

# Load base URLs from environment or default to mock services
base_region = os.getenv("REGION_API", "http://mock-api-region:8000/api/v1")
base_edge = os.getenv("EDGE_API", "http://mock-api-wavelength:8000/api/v1")

# Streamlit page config
st.set_page_config(page_title="OG Speed Tester", layout="centered")
st.title("🚀 Open Gateway Latency Speed Tester")

# User input
ue_id = st.text_input("📱 Enter UE ID", "12345")
run_test = st.button("🧪 Run Test")

def test_latency(url):
    start = time.time()
    response = requests.get(url)
    latency = (time.time() - start) * 1000  # in ms
    response.raise_for_status()
    return round(latency, 2), response.json()

if run_test:
    url_r = f"{base_region}/networkQuality?ueId={ue_id}"
    url_e = f"{base_edge}/networkQuality?ueId={ue_id}"

    # Show the actual URLs being used
    st.subheader("🔗 API Endpoints Used")
    st.code(f"Region:     {url_r}\nWavelength: {url_e}", language="bash")

    st.subheader("⏱️ Latency Measurements")

    try:
        latency_r, data_r = test_latency(url_r)
        latency_e, data_e = test_latency(url_e)

        # Top-level latency display
        col1, col2 = st.columns(2)
        col1.metric("🌎 Region Latency", f"{latency_r:.2f} ms")
        col2.metric("🏙️ Wavelength Latency", f"{latency_e:.2f} ms")

        # Bar chart comparison
        df = pd.DataFrame({
            "Zone": ["Region", "Wavelength"],
            "Latency (ms)": [latency_r, latency_e]
        })
        st.bar_chart(df.set_index("Zone").sort_values("Latency (ms)"))

        # Smart speed advantage analysis
        if latency_r and latency_e:
            target = "edge" if latency_e < latency_r else "region"
            boost = (latency_r / latency_e) if latency_e > 0 else 0
            st.success(f"⚡ **HTTP Speed Advantage:** {boost:.2f}x faster at the {target}")

            # Backend (API-reported) latency comparison
            if "latency" in data_r and "latency" in data_e and data_e["latency"] > 0:
                backend_boost = data_r["latency"] / data_e["latency"]
                target_backend = "edge" if data_e["latency"] < data_r["latency"] else "region"
                st.success(f"📶 **Network Latency Advantage:** {backend_boost:.2f}x faster at the {target_backend}")

        # Extra network details
        st.subheader("📊 Detailed Network Metrics")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 🌎 Region")
            st.metric("Backend Latency", f"{data_r.get('latency', 'N/A')} ms")
            st.metric("Bandwidth", f"{data_r.get('bandwidth', 'N/A')} Mbps")
            st.metric("Jitter", f"{data_r.get('jitter', 'N/A')} ms")

        with col2:
            st.markdown("### 🏙️ Wavelength")
            st.metric("Backend Latency", f"{data_e.get('latency', 'N/A')} ms")
            st.metric("Bandwidth", f"{data_e.get('bandwidth', 'N/A')} Mbps")
            st.metric("Jitter", f"{data_e.get('jitter', 'N/A')} ms")

        # Raw output for debugging or inspection
        st.subheader("📦 Raw API Response")
        st.json({
            "Region": data_r,
            "Wavelength": data_e
        })

    except requests.exceptions.RequestException as e:
        st.error(f"🚨 Request failed: {e}")

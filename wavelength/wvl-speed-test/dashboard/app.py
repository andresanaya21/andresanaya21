import streamlit as st
import requests
import time

def measure_latency(url):
    start = time.time()
    try:
        r = requests.get(url)
        r.raise_for_status()
    except:
        return -1
    end = time.time()
    return round((end - start) * 1000, 2)

st.title("🌐 Wavelength vs Region API Speed Test")


region_url = st.text_input("Region API URL", "http://0.0.0.0:8000/api/v1/getNetworkQuality?ueId=12345")
edge_url = st.text_input("Wavelength API URL", "http://0.0.0.0:8001/api/v1/getNetworkQuality?ueId=12345")

if st.button("Run Test"):
    st.write("🚀 Testing Region...")
    region_latency = measure_latency(region_url)
    st.metric("Region Latency (ms)", region_latency)

    st.write("🏙️ Testing Wavelength...")
    edge_latency = measure_latency(edge_url)
    st.metric("Wavelength Latency (ms)", edge_latency)

    if region_latency > 0 and edge_latency > 0:
        diff = round(region_latency / edge_latency, 1)
        st.success(f"Wavelength is {diff}x faster than Region!")

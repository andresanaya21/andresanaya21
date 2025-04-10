import streamlit as st
import requests
import time
import os

st.title("🌐 Open Gateway Speed Tester")
ue_id = st.text_input("Enter UE ID", "12345")
run_test = st.button("🚀 Test Network Quality")


# base_url_region = "http://nlb-public-e8db26b18c16da25.elb.eu-west-3.amazonaws.com:8000"   # REGION_EC2_PUBLIC_IP
# base_url_edge = "http://80.26.149.238:8000" # WAVELENGTH_EC2_PUBLIC_IP

base_region = os.getenv("REGION_API", "http://mock-api-region:8000/api/v1")
base_edge = os.getenv("EDGE_API", "http://mock-api-wavelength:8000/api/v1")


def test_latency(url):
    start = time.time()
    response = requests.get(url)
    latency = (time.time() - start) * 1000
    return latency, response.json()

if run_test:
    url_r = f"{base_region}/networkQuality?ueId={ue_id}"
    url_e = f"{base_edge}/networkQuality?ueId={ue_id}"

    latency_r, data_r = test_latency(url_r)
    latency_e, data_e = test_latency(url_e)

    st.metric("🌎 Region Latency", f"{latency_r:.2f} ms")
    st.metric("🏙️ Wavelength Latency", f"{latency_e:.2f} ms")
    boost = latency_r / latency_e if latency_e > 0 else 0
    st.write(f"📊 Speed Boost: **{boost:.1f}x**")

    st.json({"Region": data_r, "Wavelength": data_e})

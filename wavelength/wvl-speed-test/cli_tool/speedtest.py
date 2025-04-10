import typer
import requests
import time

app = typer.Typer()

def measure_latency(url: str):
    start = time.time()
    response = requests.get(url)
    end = time.time()
    latency_ms = (end - start) * 1000
    return response.json(), latency_ms

@app.command()
def speedtest(api: str = "getNetworkQuality", ue_id: str = "12345"):
    base_url_region = "http://mock-api-region:8000/api/v1"
    base_url_wavelength = "http://mock-api-wavelength:8000/api/v1"


#    base_url_region = "http://nlb-public-e8db26b18c16da25.elb.eu-west-3.amazonaws.com:8000"   # REGION_EC2_PUBLIC_IP
#    base_url_edge = "http://80.26.149.238:8000" # WAVELENGTH_EC2_PUBLIC_IP

    url_region = f"{base_url_region}/{api}?ueId={ue_id}"
    url_edge = f"{base_url_wavelength}/{api}?ueId={ue_id}"

    typer.echo("Testing Region...")
    data_r, latency_r = measure_latency(url_region)
    typer.echo(f"🌎 Region     ⏱️  {latency_r:.2f}ms")

    typer.echo("Testing Wavelength...")
    data_e, latency_e = measure_latency(url_edge)
    typer.echo(f"🏙️ Wavelength ⏱️  {latency_e:.2f}ms ✅")

    boost = latency_r / latency_e if latency_e > 0 else 0
    typer.echo(f"📊 Speed Advantage: {boost:.1f}x faster at the edge!\n")

    typer.echo(f"Region Output: {data_r}")
    typer.echo(f"Wavelength Output: {data_e}")

if __name__ == "__main__":
    app()

import typer
import requests
import time
import os

app = typer.Typer()

def measure_latency(url: str):
    try:
        start = time.time()
        response = requests.get(url)
        end = time.time()
        latency_ms = (end - start) * 1000
        response.raise_for_status()
        return response.json(), latency_ms
    except requests.RequestException as e:
        return {"error": str(e)}, None

@app.command()
def speedtest(api: str = "networkQuality", ue_id: str = "12345"):
    # Read from environment variables
    base_url_region = os.environ.get("BASE_URL_REGION", "http://mock-api-region:8000/api/v1")
    base_url_wavelength = os.environ.get("BASE_URL_WAVELENGTH", "http://mock-api-wavelength:8000/api/v1")

    url_region = f"{base_url_region}/{api}?ueId={ue_id}"
    url_edge = f"{base_url_wavelength}/{api}?ueId={ue_id}"

    typer.echo("🔍 Testing Region Endpoint...")
    typer.echo(f"🔗 URL: {url_region}")
    data_r, latency_r = measure_latency(url_region)
    region_faster = False
    if latency_r is not None:
        typer.echo(f"🌎 Region     ⏱️  {latency_r:.2f}ms")
    else:
        typer.echo("❌ Region test failed")

    typer.echo("\n🔍 Testing Wavelength Endpoint...")
    typer.echo(f"🔗 URL: {url_edge}")
    data_e, latency_e = measure_latency(url_edge)
    if latency_e is not None:
        if latency_r is not None and latency_e < latency_r:
            typer.echo(f"🏙️ Wavelength ⏱️  {latency_e:.2f}ms ✅")
        else:
            typer.echo(f"🏙️ Wavelength ⏱️  {latency_e:.2f}ms")
            region_faster = True
    else:
        typer.echo("❌ Wavelength test failed")

    if latency_r is not None and latency_e is not None:
        if region_faster:
            typer.echo("✅ Region is faster than Wavelength.\n")
        else:
            typer.echo("✅ Wavelength is faster than Region.\n")

        boost = latency_r / latency_e if latency_e > 0 else 0
        target = "edge" if not region_faster else "region"
        typer.echo(f"📊 HTTP Speed Advantage: {boost:.1f}x faster at the {target}!")

        if "latency" in data_r and "latency" in data_e and data_e["latency"] > 0:
            backend_boost = data_r["latency"] / data_e["latency"]
            typer.echo(f"📶 Network Latency Advantage: {backend_boost:.1f}x faster at the {target}!")
    else:
        typer.echo("\n⚠️ Could not compute speed advantage due to failed tests.")

    typer.echo("\n📦 Region Output:")
    typer.echo(data_r)

    typer.echo("\n📦 Wavelength Output:")
    typer.echo(data_e)

if __name__ == "__main__":
    app()

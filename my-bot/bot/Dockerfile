# Playwright base image (Chromium/Firefox/WebKit + Python)
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid

RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata ca-certificates curl && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps (Playwright already included in base image)
RUN pip install --no-cache-dir pytz

# Copy bot + tick runner
COPY book_appointment_real.py tick_runner.py /app/

RUN mkdir -p /app/artifacts /app/videos

# Default command runs the tick runner
CMD ["python", "tick_runner.py"]
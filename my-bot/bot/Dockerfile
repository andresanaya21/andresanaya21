FROM mcr.microsoft.com/playwright/python:v1.46.0-jammy

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid

RUN apt-get update && \
    apt-get install -y --no-install-recommends tzdata ca-certificates curl && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    curl -fsSL https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64 \
      -o /usr/local/bin/supercronic && \
    chmod +x /usr/local/bin/supercronic && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pin Python bindings to match the image
RUN pip install --no-cache-dir "playwright==1.46.0"

COPY book_appointment_real.py /app/book_appointment_real.py
RUN mkdir -p /app/artifacts /app/videos

CMD ["python", "book_appointment_real.py"]
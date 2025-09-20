FROM python:3.11-slim

WORKDIR /app

# System deps for browsers
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 libnspr4 libasound2 libx11-xcb1 libxcomposite1 libxcursor1 \
    libxdamage1 libxi6 libxtst6 libglib2.0-0 libxrandr2 libatk1.0-0 \
    libatk-bridge2.0-0 libdrm2 libgbm1 libxkbcommon0 libpango-1.0-0 \
    libcairo2 libatspi2.0-0 wget curl tzdata ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Python deps
RUN pip install --no-cache-dir playwright pytz

# Install browser binaries
RUN playwright install --with-deps

COPY book_appointment_real.py tick_runner.py /app/

CMD ["python", "tick_runner.py"]
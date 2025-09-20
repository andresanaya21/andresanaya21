---

# Mock Qmatic + Booking Bot

Automate appointment booking for the Ministry site, with a local mock for testing and a resilient Playwright bot.
Includes an always-on **tick runner** service that triggers the bot every 5 seconds, but only **Sunday → Wednesday, 12:10 → 14:00 (Europe/Madrid)**.

---

## 📂 Project structure

```
.
├── docker-compose.yml
├── mock-qmatic/
│   ├── server.py
│   ├── schema.json
│   └── static/
│       ├── index.html
│       └── app.js
└── bot/
    ├── book_appointment.py          # Bot for the local mock
    ├── book_appointment_real.py     # Resilient bot for the real site
    ├── tick_runner.py               # Scheduler loop (5s ticks, Sun–Wed 12:10–14:00)
    ├── Dockerfile                   # Playwright base + pytz
    ├── artifacts/                   # Screenshots & traces
    └── videos/                      # Playwright videos
```

---

## 1️⃣ Run the **mock** appointment site (Flask)

```bash
cd mock-qmatic/

python3 -m venv .venv
source .venv/bin/activate
pip install flask
python server.py
# -> http://localhost:5173
```

Use `?no_slots=1` to simulate “no availability”.

---

## 2️⃣ Run the bot locally (without Docker)

```bash
cd bot/

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install playwright
python -m playwright install
playwright install-deps  # Linux only, installs required system libs
```

### Run against the local mock

```bash
python book_appointment.py
```

### Run against the real site

Debug (headed, inspector):

```bash
PWDEBUG=1 HEADLESS=false python book_appointment_real.py
```

Slow motion:

```bash
HEADLESS=false SLOW_MO_MS=300 python book_appointment_real.py
```

Headless, fast:

```bash
HEADLESS=true SLOW_MO_MS=0 python book_appointment_real.py
```

Replay a trace:

```bash
playwright show-trace artifacts/trace.zip
```

---

## 3️⃣ Docker: build image

```bash
docker compose build --no-cache
```

This builds a single Playwright-based image used by both the one-shot bot and the tick runner.

---

## 4️⃣ Docker: run once (manual)

```bash
docker compose run --rm bot
```

Runs `book_appointment_real.py` once with the env vars configured in `docker-compose.yml`.

---

## 5️⃣ Docker: run continuously (tick runner)

Start the always-on scheduler (triggers every 5s, Sun–Wed, 12:10–14:00):

```bash
docker compose up -d ticker
docker compose logs -f ticker
```

You’ll see logs like:

```
[tick-runner] 2025-09-21T12:09:55+02:00 → outside window
[tick-runner] 2025-09-21T12:10:00+02:00 → starting bot: python /app/book_appointment_real.py
...
```

Artifacts and videos are persisted to `./bot/artifacts` and `./bot/videos`.

---

## ⚙️ Configuration

Both services share env vars defined in `docker-compose.yml`. You can also override them at runtime with `-e`.

| Variable             | Default                                                 | Purpose                                                 |
| -------------------- | ------------------------------------------------------- | ------------------------------------------------------- |
| `BASE_URL`           | `https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/` | Target site (use `http://localhost:5173` for mock)      |
| `TARGET_TRAMITE`     | Long text for target service                            | Which trámite to select                                 |
| `CONTACT_NAME`       | `Monica Pérez Villarroel`                               | Contact info                                            |
| `CONTACT_ID`         | `Z0428685Q`                                             | DNI/NIE/passport                                        |
| `CONTACT_EMAIL`      | …                                                       | Email                                                   |
| `CONTACT_PHONE`      | …                                                       | Phone                                                   |
| `HEADLESS`           | `true` in Docker                                        | Browser visible or not                                  |
| `SLOW_MO_MS`         | `0` in Docker                                           | Delay between actions                                   |
| `MAX_MONTHS_TO_SCAN` | `6`                                                     | How far ahead to search                                 |
| `DEFAULT_TIMEOUT_MS` | `25000`                                                 | Per-action timeout                                      |
| `TZ`                 | `Europe/Madrid`                                         | Timezone                                                |
| `TICK_INTERVAL`      | `5`                                                     | Tick interval (seconds) for the runner                  |
| `BOT_TIMEOUT`        | `180`                                                   | Max seconds per bot run before force kill               |
| `WINDOW_DAYS`        | `SUN,MON,TUE,WED`                                       | Which days                                              |
| `WINDOW_START`       | `12:10`                                                 | Start time                                              |
| `WINDOW_END`         | `14:00`                                                 | End time (inclusive)                                    |
| `BOT_EXTRA_ENV`      | empty                                                   | Extra env for bot, e.g. `HEADLESS=false,SLOW_MO_MS=250` |

---
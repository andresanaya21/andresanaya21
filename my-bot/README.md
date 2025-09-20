---

# Mock Qmatic + Booking Bot

Automate appointment booking for the Ministry site and test locally with a lightweight mock that mirrors the flow.

## Folder layout

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
    ├── book_appointment.py            # targets local mock
    ├── book_appointment_real.py       # resilient selectors for the real site
    ├── Dockerfile                     # Playwright image + supercronic
    ├── crontab                        # schedule for the scheduler service
    ├── artifacts/                     # screenshots & traces (mounted)
    └── videos/                        # Playwright videos (mounted)
```

---

## 1) Run the **mock** appointment web (Flask)

```bash
cd mock-qmatic/

python3 -m venv .venv
source .venv/bin/activate
pip install flask
python server.py
# -> http://localhost:5173
```

> Tip: you can simulate no availability with `?no_slots=1` (the mock UI reads it).

---

## 2) Run the **bot** against the mock (Playwright, local venv)

```bash
cd bot/

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install playwright
python -m playwright install
```

Linux-only (if browsers fail to launch):

```bash
# All OS deps in one go (recommended)
playwright install-deps
# or minimal packages:
sudo apt-get install -y libnspr4 libnss3 libasound2
```

Run the local mock bot:

```bash
python book_appointment.py
```

---

## 3) Run the **bot** against the real site

Debug/slow:

```bash
PWDEBUG=1 HEADLESS=false python book_appointment_real.py
```

Step through specific points:

```bash
BREAK_AT=after_step1,after_step2 HEADLESS=false SLOW_MO_MS=200 python book_appointment_real.py
```

Headless/fast:

```bash
HEADLESS=true SLOW_MO_MS=0 python book_appointment_real.py
```

Replay a trace:

```bash
playwright show-trace artifacts/trace.zip
```

### Contact details (env or edit in script)

```python
CONTACT = {
    "name": "Monica Pérez Villarroel",
    "id": "Z0428685Q",        # DNI/NIE/Pasaporte
    "email": "monicaperezvillarroel060@gmail.com",
    "phone": "613304514",
}
```

You can also export them as env vars:

```bash
export CONTACT_NAME="Monica Pérez Villarroel"
export CONTACT_ID="Z0428685Q"
export CONTACT_EMAIL="monicaperezvillarroel060@gmail.com"
export CONTACT_PHONE="613304514"
```

---

## 4) Docker & scheduler (every Sun–Wed, 12:10–14:00 Europe/Madrid)

### Build (no cache recommended after Dockerfile changes)

```bash
# Compose v2 (modern): 
docker compose build --no-cache
# Compose v1 (older): 
# docker-compose build --no-cache
```

### One-shot manual run

```bash
docker compose run --rm bot
# docker-compose run --rm bot
```

### Start scheduler daemon

```bash
docker compose up -d scheduler
docker compose logs -f scheduler
# docker-compose up -d scheduler
# docker-compose logs -f scheduler
```

The schedule is defined in `bot/crontab`:

```
# Every 10 min from 12:10..12:59 (Sun..Wed)
10-59/10 12 * * SUN,MON,TUE,WED  python /app/book_appointment_real.py >> /proc/1/fd/1 2>&1
# Every 10 min from 13:00..13:59 (Sun..Wed)
*/10      13 * * SUN,MON,TUE,WED  python /app/book_appointment_real.py >> /proc/1/fd/1 2>&1
# Once at 14:00 (Sun..Wed)
0         14 * * SUN,MON,TUE,WED  python /app/book_appointment_real.py >> /proc/1/fd/1 2>&1
```

Artifacts and videos are bind-mounted to `./bot/artifacts` and `./bot/videos`.

> **Note:** Remove the `version:` key from `docker-compose.yml` if you see a warning. Compose v2 ignores it.

---

## 5) Environment variables (bot)

You can override these when running locally or via Compose:

| Variable             | Default                                                                                           | What it does                                                                   |
| -------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `BASE_URL`           | `https://citaprevia.ciencia.gob.es/qmaticwebbooking/#/`                                           | Target site (use `http://localhost:5173` for the mock)                         |
| `TARGET_TRAMITE`     | `Asistencia telefónica para la homologación y equivalencia de títulos universitarios extranjeros` | Exact/partial match used by resilient selectors                                |
| `HEADLESS`           | `true` (Docker), `false` (debug)                                                                  | Browser UI visible or not                                                      |
| `SLOW_MO_MS`         | `0` (Docker), `150` (debug)                                                                       | Adds delay between operations                                                  |
| `DEFAULT_TIMEOUT_MS` | `25000`                                                                                           | Per-action timeout                                                             |
| `MAX_MONTHS_TO_SCAN` | `6`                                                                                               | How far ahead to search                                                        |
| `CONTACT_*`          | —                                                                                                 | Contact fields (see above)                                                     |
| `TZ`                 | `Europe/Madrid`                                                                                   | Scheduler timezone inside container                                            |
| `BREAK_AT`           | *empty*                                                                                           | Comma list of breakpoints: `after_step1,after_step2,after_step3,after_confirm` |

Example:

```bash
BASE_URL=http://localhost:5173 HEADLESS=false SLOW_MO_MS=250 python bot/book_appointment_real.py
```

---

## 6) Troubleshooting

### Playwright browsers fail to launch (Linux)

```
Error: Host system is missing dependencies ...
```

Fix:

```bash
playwright install-deps
# or:
sudo apt-get install -y libnspr4 libnss3 libasound2
```

### Version mismatch in Docker

```
Looks like Playwright was just updated to 1.xx. Please update docker image as well.
```

Use a matching image tag in `bot/Dockerfile`:

```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.55.0-jammy
```

…and **do not** `pip install playwright` again (the base image already includes the matching Python bindings & browsers).

### tzdata prompt during build hangs

Use non-interactive setup in `bot/Dockerfile`:

```dockerfile
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Madrid
RUN apt-get update && apt-get install -y --no-install-recommends tzdata \
 && ln -fs /usr/share/zoneinfo/$TZ /etc/localtime \
 && dpkg-reconfigure -f noninteractive tzdata
```

### Can’t see what’s happening (too fast)

Use:

```bash
HEADLESS=false SLOW_MO_MS=300 python bot/book_appointment_real.py
# or the inspector:
PWDEBUG=1 python bot/book_appointment_real.py
```

Open traces:

```bash
playwright show-trace bot/artifacts/trace.zip
```

### Real site changed selectors

The resilient selectors already try radio lists, Material combobox/overlay, and iframes. If something still fails, run:

```bash
PWDEBUG=1 HEADLESS=false python bot/book_appointment_real.py
```

then share `bot/artifacts/trace.zip` (it records DOM snapshots) and we’ll tune a selector quickly.

---

## 7) Quick commands (cheat sheet)

```bash
# Mock server:
(cd mock-qmatic && python -m venv .venv && source .venv/bin/activate && pip install flask && python server.py)

# Bot (local mock):
(cd bot && python -m venv .venv && source .venv/bin/activate && pip install playwright && python -m playwright install && python book_appointment.py)

# Bot (real site, debug):
(cd bot && source .venv/bin/activate && PWDEBUG=1 HEADLESS=false python book_appointment_real.py)

# Docker (manual bot):
docker compose build --no-cache bot
docker compose run --rm bot

# Docker (scheduler):
docker compose up -d scheduler
docker compose logs -f scheduler
```

---
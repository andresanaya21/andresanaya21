import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, time as dtime
from typing import Optional, Set

import pytz

# -------------------------
# Config (env-overridable)
# -------------------------
TZ = os.getenv("TZ", "Europe/Madrid")
TICK_INTERVAL = int(os.getenv("TICK_INTERVAL", "5"))  # seconds
BOT_CMD = os.getenv("BOT_CMD", "python /app/book_appointment_real.py")

# Window config (defaults: Sun–Wed, 12:10 → 14:00 inclusive)
WINDOW_DAYS = os.getenv("WINDOW_DAYS", "SUN,MON,TUE,WED")  # comma list
WINDOW_START = os.getenv("WINDOW_START", "12:10")          # HH:MM (24h)
WINDOW_END = os.getenv("WINDOW_END", "14:00")              # HH:MM (24h) inclusive

# Per-run hard timeout (seconds). If the bot exceeds this, it will be terminated.
BOT_TIMEOUT = int(os.getenv("BOT_TIMEOUT", "180"))         # 3 minutes

# Optional additional env vars passed to the bot process (comma-separated VAR=VAL)
BOT_EXTRA_ENV = os.getenv("BOT_EXTRA_ENV", "")             # e.g. "HEADLESS=true,SLOW_MO_MS=0"

# Optional start offset (seconds) to stagger multiple instances
START_OFFSET = int(os.getenv("START_OFFSET", "0"))

tz = pytz.timezone(TZ)

# -------------------------
# Helpers
# -------------------------
DAY_MAP = {
    "MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6
}

def parse_days(value: str) -> Set[int]:
    days = set()
    for tok in (t.strip().upper() for t in value.split(",") if t.strip()):
        if tok not in DAY_MAP:
            continue
        days.add(DAY_MAP[tok])
    return days

def parse_hhmm(s: str) -> dtime:
    hh, mm = s.strip().split(":")
    return dtime(int(hh), int(mm))

def now_madrid() -> datetime:
    return datetime.now(tz)

def log(msg: str):
    print(f"[tick-runner] {now_madrid().isoformat()} {msg}", flush=True)

@dataclass
class Window:
    days: Set[int]
    start: dtime
    end: dtime  # inclusive

    def contains(self, dt: datetime) -> bool:
        wd = dt.weekday()  # Mon=0..Sun=6
        if wd not in self.days:
            return False
        t = dt.time()
        # inclusive end
        return (t >= self.start) and (t <= self.end)

def build_env() -> dict:
    env = os.environ.copy()
    if BOT_EXTRA_ENV:
        for pair in BOT_EXTRA_ENV.split(","):
            pair = pair.strip()
            if not pair or "=" not in pair: 
                continue
            k, v = pair.split("=", 1)
            env[k.strip()] = v.strip()
    return env

def build_cmd() -> list:
    # keep it simple: run via /bin/sh -lc so you can pass a full command line in BOT_CMD
    return ["/bin/sh", "-lc", BOT_CMD]

# -------------------------
# Runner
# -------------------------
class TickRunner:
    def __init__(self, window: Window):
        self.window = window
        self.current_proc: Optional[subprocess.Popen] = None
        self.stop = False

        signal.signal(signal.SIGTERM, self._on_stop)
        signal.signal(signal.SIGINT, self._on_stop)

    def _on_stop(self, *_):
        log("received stop signal — shutting down")
        self.stop = True

    def _start_bot(self):
        if self.current_proc and self.current_proc.poll() is None:
            log("previous run still active — skipping this tick")
            return

        # Clean up finished process if any
        if self.current_proc and self.current_proc.poll() is not None:
            rc = self.current_proc.returncode
            log(f"previous run finished with exit code {rc}")
            self.current_proc = None

        # Spawn a new run
        cmd = build_cmd()
        env = build_env()
        log(f"starting bot: {BOT_CMD}")
        self.current_proc = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

    def _pump_output_and_enforce_timeout(self, start_ts: float):
        """Stream child output and enforce BOT_TIMEOUT."""
        if not self.current_proc:
            return

        # Non-blocking read loop with timeout enforcement
        while True:
            if self.current_proc.poll() is not None:
                # process ended, drain remaining output
                for line in self.current_proc.stdout or []:
                    sys.stdout.write(line)
                rc = self.current_proc.returncode
                log(f"bot finished with exit code {rc}")
                self.current_proc = None
                return

            # Stream any available lines
            if self.current_proc.stdout:
                line = self.current_proc.stdout.readline()
                if line:
                    sys.stdout.write(line)

            # timeout?
            if time.time() - start_ts > BOT_TIMEOUT:
                log(f"bot exceeded timeout ({BOT_TIMEOUT}s) — terminating")
                try:
                    self.current_proc.terminate()
                    # give it a moment
                    try:
                        self.current_proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        log("terminate timed out — killing")
                        self.current_proc.kill()
                finally:
                    self.current_proc = None
                return

            # short sleep to avoid busy loop
            time.sleep(0.1)

    def loop(self):
        log(f"start — TZ={TZ}, tick={TICK_INTERVAL}s, window_days={WINDOW_DAYS}, window={WINDOW_START}→{WINDOW_END} (inclusive)")
        while not self.stop:
            now = now_madrid()
            if self.window.contains(now):
                # start if not running
                if not (self.current_proc and self.current_proc.poll() is None):
                    self._start_bot()
                    # enforce timeout and stream output for this run
                    self._pump_output_and_enforce_timeout(time.time())
                else:
                    log("run in progress — not launching a second one")
            else:
                # if we exit the window and a run is still active, let it finish (or time out)
                if self.current_proc and self.current_proc.poll() is None:
                    log("outside window, but a run is active — letting it finish/timeout")
                else:
                    log("outside window — idle")
            # sleep tick interval
            slept = 0
            while slept < TICK_INTERVAL and not self.stop:
                time.sleep(1)
                slept += 1

        # shutdown: if a run is active, try to stop gracefully
        if self.current_proc and self.current_proc.poll() is None:
            log("stopping active run on shutdown")
            try:
                self.current_proc.terminate()
                self.current_proc.wait(timeout=5)
            except Exception:
                self.current_proc.kill()
        log("bye")

# -------------------------
# Main
# -------------------------
def main():
    window = Window(
        days=parse_days(WINDOW_DAYS or "SUN,MON,TUE,WED"),
        start=parse_hhmm(WINDOW_START or "12:10"),
        end=parse_hhmm(WINDOW_END or "14:00"),
    )

    if START_OFFSET > 0:
        log(f"start offset — sleeping {START_OFFSET}s before entering loop")
        time.sleep(START_OFFSET)

    runner = TickRunner(window)
    runner.loop()

if __name__ == "__main__":
    main()

import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, time as dtime, timedelta
from typing import Optional, Set

import pytz

# -------------------------
# Config (env-overridable)
# -------------------------
TZ = os.getenv("TZ", "Europe/Madrid")
# Loop poll frequency (seconds)
TICK_INTERVAL = int(os.getenv("TICK_INTERVAL", "1"))

# Slot cadence: run every N minutes
SLOT_MINUTES = int(os.getenv("SLOT_MINUTES", "10"))

# How long we keep relaunching within each slot (e.g., 300s = 5 minutes)
RUN_WINDOW_SECONDS = int(os.getenv("RUN_WINDOW_SECONDS", "300"))

# Optional grace window to activate a slot if we happen to start late (sec).
# Not critical for the repeated-runs behavior but harmless to keep.
LAUNCH_GRACE_SECONDS = int(os.getenv("LAUNCH_GRACE_SECONDS", "30"))

# Command to run your bot
BOT_CMD = os.getenv("BOT_CMD", "python /app/book_appointment_real.py")

# Time window (inclusive end means a slot that starts exactly at WINDOW_END is allowed)
WINDOW_DAYS = os.getenv("WINDOW_DAYS", "MON,TUE,WED,THU,FRI")
WINDOW_START = os.getenv("WINDOW_START", "12:00")
WINDOW_END = os.getenv("WINDOW_END", "14:00")

# Per-run hard timeout (seconds). Each bot run will be terminated if it exceeds this,
# and we also enforce the remaining time of the active slot window.
BOT_TIMEOUT = int(os.getenv("BOT_TIMEOUT", "300"))  # 5 minutes default

# Extra env forwarded to the bot process (comma-separated VAR=VAL)
BOT_EXTRA_ENV = os.getenv("BOT_EXTRA_ENV", "")

# Optional start offset (seconds) to stagger multiple instances
START_OFFSET = int(os.getenv("START_OFFSET", "0"))

tz = pytz.timezone(TZ)

# -------------------------
# Helpers
# -------------------------
DAY_MAP = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}

def parse_days(value: str) -> Set[int]:
    days = set()
    for tok in (t.strip().upper() for t in value.split(",") if t.strip()):
        if tok in DAY_MAP:
            days.add(DAY_MAP[tok])
    return days

def parse_hhmm(s: str) -> dtime:
    hh, mm = s.strip().split(":")
    return dtime(int(hh), int(mm))

def now_local() -> datetime:
    return datetime.now(tz)

def log(msg: str):
    print(f"[tick-runner] {now_local().isoformat()} {msg}", flush=True)

def build_env() -> dict:
    env = os.environ.copy()
    if BOT_EXTRA_ENV:
        for pair in BOT_EXTRA_ENV.split(","):
            pair = pair.strip()
            if pair and "=" in pair:
                k, v = pair.split("=", 1)
                env[k.strip()] = v.strip()
    return env

def build_cmd() -> list:
    # run via shell so BOT_CMD can be a full command line
    return ["/bin/sh", "-lc", BOT_CMD]

def floor_to_slot(dt: datetime, minutes: int) -> datetime:
    """Return dt floored down to the nearest N-minute boundary (seconds=0)."""
    return dt.replace(minute=(dt.minute // minutes) * minutes, second=0, microsecond=0)

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
        return (t >= self.start) and (t <= self.end)

# -------------------------
# Runner
# -------------------------
class TickRunner:
    def __init__(self, window: Window):
        self.window = window
        self.current_proc: Optional[subprocess.Popen] = None
        self.stop = False

        # Active slot tracking
        self.active_slot_key: Optional[str] = None
        self.active_slot_end_ts: Optional[float] = None  # epoch seconds when window ends

        signal.signal(signal.SIGTERM, self._on_stop)
        signal.signal(signal.SIGINT, self._on_stop)

    def _on_stop(self, *_):
        log("received stop signal — shutting down")
        self.stop = True

    def _slot_key(self, slot_dt: datetime) -> str:
        return slot_dt.strftime("%Y-%m-%d %H:%M")

    def _activate_slot_if_needed(self, now: datetime, slot: datetime):
        """
        If we're in a new slot and within its activation window, mark it active.
        The slot remains active for RUN_WINDOW_SECONDS, during which we keep
        launching runs sequentially.
        """
        slot_key = self._slot_key(slot)
        if self.active_slot_key == slot_key:
            return  # already active

        # Only activate if inside the global window
        if not self.window.contains(now):
            return

        slot_end = slot + timedelta(seconds=RUN_WINDOW_SECONDS)
        # Activate if we're within the 5-min window, or within grace right after slot start
        if now <= slot_end or now <= slot + timedelta(seconds=LAUNCH_GRACE_SECONDS):
            self.active_slot_key = slot_key
            self.active_slot_end_ts = slot_end.timestamp()
            log(f"activated slot {slot_key} (window until {slot_end.time().isoformat(timespec='seconds')})")

    def _deactivate_slot_if_expired(self, now_ts: float):
        if self.active_slot_end_ts is not None and now_ts >= self.active_slot_end_ts:
            log(f"slot window ended ({self.active_slot_key})")
            self.active_slot_key = None
            self.active_slot_end_ts = None

    def _start_bot(self):
        # Clean up finished process if any
        if self.current_proc and self.current_proc.poll() is not None:
            rc = self.current_proc.returncode
            log(f"previous run finished with exit code {rc}")
            self.current_proc = None

        if self.current_proc and self.current_proc.poll() is None:
            log("run in progress — not launching another concurrently")
            return False

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
        return True

    def _pump_output_and_enforce_deadlines(self, hard_deadline_ts: Optional[float]):
        """
        Stream child output and enforce both BOT_TIMEOUT and the slot hard deadline.
        hard_deadline_ts: epoch seconds when the slot window ends; we stop the run there.
        """
        if not self.current_proc:
            return

        start_ts = time.time()

        def time_left():
            left = BOT_TIMEOUT - (time.time() - start_ts)
            if hard_deadline_ts is not None:
                left = min(left, hard_deadline_ts - time.time())
            return left

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

            # deadlines?
            left = time_left()
            if left is not None and left <= 0:
                # Stop due to BOT_TIMEOUT or slot window end
                reason = "timeout" if (time.time() - start_ts) >= BOT_TIMEOUT else "slot window end"
                log(f"bot exceeded {reason} — terminating")
                try:
                    self.current_proc.terminate()
                    try:
                        self.current_proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        log("terminate timed out — killing")
                        self.current_proc.kill()
                finally:
                    self.current_proc = None
                return

            time.sleep(0.1)

    def loop(self):
        log(f"start — TZ={TZ}, slots={SLOT_MINUTES}m, run_window={RUN_WINDOW_SECONDS}s, "
            f"window_days={WINDOW_DAYS}, window={WINDOW_START}→{WINDOW_END} (inclusive)")
        while not self.stop:
            now = now_local()
            now_ts = time.time()

            # Determine current slot and activate if needed
            slot = floor_to_slot(now, SLOT_MINUTES)
            self._activate_slot_if_needed(now, slot)

            # If active slot window expired, deactivate
            self._deactivate_slot_if_expired(now_ts)

            # If slot is active and inside global time window, keep launching sequentially
            if self.active_slot_key and self.active_slot_end_ts and self.window.contains(now):
                # If nothing running, (re)start immediately and pump until finish/deadline
                if not (self.current_proc and self.current_proc.poll() is None):
                    started = self._start_bot()
                    if started:
                        self._pump_output_and_enforce_deadlines(self.active_slot_end_ts)
                else:
                    # A run is already in progress; just let it continue
                    pass
            else:
                # Outside active window; if a run is still active, let it finish (but BOT_TIMEOUT still applies)
                if self.current_proc and self.current_proc.poll() is None:
                    log("outside slot window, but a run is active — letting it finish/timeout")

            # sleep a bit
            slept = 0
            while slept < TICK_INTERVAL and not self.stop:
                time.sleep(1)
                slept += 1

        # shutdown: stop active run gracefully
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
        days=parse_days(WINDOW_DAYS or "MON,TUE,WED,THU,FRI"),
        start=parse_hhmm(WINDOW_START or "12:00"),
        end=parse_hhmm(WINDOW_END or "14:00"),
    )

    if START_OFFSET > 0:
        log(f"start offset — sleeping {START_OFFSET}s before entering loop")
        time.sleep(START_OFFSET)

    runner = TickRunner(window)
    runner.loop()

if __name__ == "__main__":
    main()

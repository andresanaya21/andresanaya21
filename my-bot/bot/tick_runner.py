import os
import subprocess
import time
from datetime import datetime
import pytz

# Timezone (set by container env TZ=Europe/Madrid)
TZ = os.getenv("TZ", "Europe/Madrid")
tz = pytz.timezone(TZ)

# Command to run the bot once
BOT_CMD = ["python", "/app/book_appointment_real.py"]

# Interval between ticks (seconds)
INTERVAL = int(os.getenv("TICK_INTERVAL", "5"))

def in_window(now: datetime) -> bool:
    """True if Sun–Wed and between 12:10 and 14:00 inclusive (Europe/Madrid)."""
    # Python weekday(): Monday=0 … Sunday=6
    wd = now.weekday()  # Sun=6, Mon=0, Tue=1, Wed=2
    if wd not in (6, 0, 1, 2):
        return False
    h, m = now.hour, now.minute
    if h < 12 or h > 14:
        return False
    if h == 12 and m < 10:
        return False
    if h == 14 and m > 0:
        return False
    return True

def main():
    print(f"[tick-runner] Start. TZ={TZ} interval={INTERVAL}s; window: Sun–Wed 12:10–14:00")
    while True:
        now = datetime.now(tz)
        if in_window(now):
            print(f"[tick-runner] {now.isoformat()} → running bot")
            try:
                result = subprocess.run(BOT_CMD, capture_output=True, text=True)
                if result.stdout:
                    print(result.stdout, end="")
                if result.stderr:
                    print("[stderr]", result.stderr, end="")
            except Exception as e:
                print(f"[tick-runner] ERROR: {e}")
        else:
            print(f"[tick-runner] {now.isoformat()} → outside window")
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
import os
import subprocess
import time
from datetime import datetime
import pytz

# Timezone
TZ = os.getenv("TZ", "Europe/Madrid")
tz = pytz.timezone(TZ)

# Path to the bot script
BOT_CMD = ["python", "/app/book_appointment_real.py"]

# Interval in seconds
INTERVAL = 5

def in_window(now: datetime) -> bool:
    """Return True if current time is Sun–Wed, 12:10–14:00 (inclusive)."""
    # weekday(): Monday=0 … Sunday=6
    wd = now.weekday()
    if wd not in (6, 0, 1, 2):  # Sun=6, Mon=0, Tue=1, Wed=2
        return False

    hour, minute = now.hour, now.minute
    if hour < 12 or hour > 14:
        return False
    if hour == 12 and minute < 10:
        return False
    if hour == 14 and minute > 0:
        return False
    return True

def main():
    print(f"[tick-runner] Starting loop in {TZ}, interval={INTERVAL}s")
    while True:
        now = datetime.now(tz)
        if in_window(now):
            print(f"[tick-runner] {now} → running bot")
            try:
                result = subprocess.run(BOT_CMD, capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print("[stderr]", result.stderr)
            except Exception as e:
                print(f"[tick-runner] ERROR running bot: {e}")
        else:
            print(f"[tick-runner] {now} → outside window, idle")

        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import time
import subprocess
from gpiozero import DistanceSensor

# ====== EDIT THESE ======
MAC_USER = "orenagiv"
MAC_HOST = "10.176.46.25"   # or your Mac's IP, e.g., "192.168.1.25"
# ========================

# GPIO pins (BCM numbering)
TRIG_PIN = 23
ECHO_PIN = 24

# Trigger threshold & debounce
TRIGGER_CM = 15.0        # fire when closer than 15 cm
HYSTERESIS_CM = 3.0      # must move back past 18 cm to re-arm
COOLDOWN_SEC = 0.8       # block repeat fires for 0.8s
SAMPLE_PERIOD = 0.03     # read every 30 ms
STABLE_COUNT = 3         # require N consecutive readings under/over threshold

sensor = DistanceSensor(echo=ECHO_PIN, trigger=TRIG_PIN, max_distance=2.0)  # meters

def send_spacebar():
    # AppleScript to press Space (key code 49)
    cmd = [
        "ssh",
        f"{MAC_USER}@{MAC_HOST}",
        'osascript -e \'tell application "System Events" to key code 49\''
    ]
    try:
        subprocess.run(cmd, check=True, timeout=3)
    except Exception as e:
        print(f"[WARN] Failed to send spacebar: {e}")

def cm(meters):
    return meters * 100.0

def main():
    last_fire = 0.0
    armed = True
    under_count = 0
    over_count = 0
    low = TRIGGER_CM
    high = TRIGGER_CM + HYSTERESIS_CM

    print(f"Armed. Wave within {TRIGGER_CM} cm to press Space on the Mac.")
    while True:
        d = cm(sensor.distance)  # distance in cm
        now = time.time()

        if armed:
            if d <= low:
                under_count += 1
                over_count = 0
                if under_count >= STABLE_COUNT and (now - last_fire) > COOLDOWN_SEC:
                    print(f"Trigger: {d:.1f} cm → SPACE")
                    send_spacebar()
                    last_fire = now
                    armed = False
                    under_count = 0
            else:
                under_count = 0
        else:
            # Re-arm only after moving away beyond hysteresis distance
            if d >= high:
                over_count += 1
                if over_count >= STABLE_COUNT:
                    armed = True
                    over_count = 0
            else:
                over_count = 0

        time.sleep(SAMPLE_PERIOD)

if __name__ == "__main__":
    main()
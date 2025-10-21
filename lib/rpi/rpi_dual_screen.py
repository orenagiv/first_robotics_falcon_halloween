import cv2
import RPi.GPIO as GPIO
import time
import random

PIR_PIN = 14

# Paths to your videos
VIDEO_PATH1 = "../../assets/videos/dual_video_1_left_720p.mp4"
VIDEO_PATH2 = "../../assets/videos/dual_video_1_right_720p.mp4"

# --- Setup GPIO ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

# --- Setup Video ---
cap1 = cv2.VideoCapture(VIDEO_PATH1)
if not cap1.isOpened():
    print("❌ Cannot open video 1")
    GPIO.cleanup()
    exit()

cap2 = cv2.VideoCapture(VIDEO_PATH2)
if not cap2.isOpened():
    print("❌ Cannot open video 2")
    cap1.release()
    GPIO.cleanup()
    exit()

# --- Create fullscreen windows ---
cv2.namedWindow("Screen1", cv2.WINDOW_NORMAL)
cv2.namedWindow("Screen2", cv2.WINDOW_NORMAL)

# Move windows to different monitors
# Adjust X offsets if your screens are positioned differently
cv2.moveWindow("Screen1", 0, 0)            
cv2.moveWindow("Screen2", 1280, 0)         

# Fullscreen mode
cv2.setWindowProperty("Screen1", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.setWindowProperty("Screen2", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

paused = True
print("✅ System ready — press 'q' to quit")

def play_video(cap, window_name, duration=5):
    """Play video for a given duration in fullscreen."""
    start_time = time.time()
    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()

        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            raise KeyboardInterrupt

    # Pause on current frame
    current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)

def show_last_frame(cap, window_name):
    """Keep last frame on screen while paused."""
    current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
    cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
    ret, frame = cap.read()
    if ret:
        cv2.imshow(window_name, frame)

try:
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        if GPIO.input(PIR_PIN):  # Motion detected
            # Decide randomly which screen goes first
            first_screen = random.choice(["Screen1", "Screen2"])
            second_screen = "Screen2" if first_screen == "Screen1" else "Screen1"
            
            # Map screen name to video capture
            cap_map = {"Screen1": cap1, "Screen2": cap2}

            # Random delay between 0 and 5
            delay = random.randint(0, 5)

            print(f"💡 Motion detected")
            print(f"▶️ First video: {first_screen}, Delay before second: {delay}s")

            paused = False
            play_video(cap_map[first_screen], first_screen, duration=5)

            if delay > 0:
                print(f"⏸ Paused first video — waiting {delay} seconds")
                time.sleep(delay)

                print(f"▶️ Playing second video on {second_screen}")
                play_video(cap_map[second_screen], second_screen, duration=5)
            else:
                print(f"🚫 No second video this time")

            print("⏸ Paused videos — waiting for next motion")
            paused = True

        if paused:
            show_last_frame(cap1, "Screen1")
            show_last_frame(cap2, "Screen2")
            time.sleep(0.1)

except KeyboardInterrupt:
    print("👋 Exiting program...")

finally:
    cap1.release()
    cap2.release()
    cv2.destroyAllWindows()
    GPIO.cleanup()


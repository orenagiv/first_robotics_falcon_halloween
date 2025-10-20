import cv2
import RPi.GPIO as GPIO
import time

PIR_PIN = 14
VIDEO_PATH = "../../assets/videos/single_screen_1/UP_Madam_LivingNightmare_TV_V.mp4"

# --- Setup GPIO ---
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

# --- Setup Video ---
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print("❌ Cannot open video file")
    GPIO.cleanup()
    exit()

paused = True
print("✅ System ready — press 'q' to quit")

try:
    while True:
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

        if GPIO.input(PIR_PIN):  # Motion detected
            print("💡 Motion detected — playing video for 5 seconds")
            start_time = time.time()
            paused = False

            while time.time() - start_time < 5:
                ret, frame = cap.read()
                if not ret:
                    # restart from beginning
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ret, frame = cap.read()

                cv2.imshow("Video", frame)

                # allow quit inside playback loop
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    raise KeyboardInterrupt

            paused = True
            print("⏸ Paused video again")

        if paused:
            current_frame = int(cap.get(cv2.CAP_PROP_POS_FRAMES))
            cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = cap.read()
            if ret:
                cv2.imshow("Video", frame)
            time.sleep(0.1)

except KeyboardInterrupt:
    print("👋 Exiting program...")

finally:
    cap.release()
    cv2.destroyAllWindows()
    GPIO.cleanup()

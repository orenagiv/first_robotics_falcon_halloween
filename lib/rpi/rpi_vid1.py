# The following script will load specific video (assets/single_screen_1/UP_Madam_LivingNightmare_TV_V.mp4) and pause on the first frame.
# This script is a python script that will run on Raspberry Pi.
# We will use a motion detection sensor "GPIO" connected to pin 14.
# When the sensor detects motion closer than one meter of range - then play the video.
# When the video ends go back to the first frame of the video.

import cv2
try:
    import RPi.GPIO as GPIO
except Exception:
    # Allow running/testing on non-RPi systems by providing a dummy GPIO
    class _DummyGPIO:
        BCM = 'BCM'
        IN = 'IN'

        def setmode(self, mode):
            print(f"DummyGPIO: setmode({mode})")

        def setup(self, pin, mode):
            print(f"DummyGPIO: setup(pin={pin}, mode={mode})")

        def input(self, pin):
            # Always return 0 (no motion) by default. You can change to 1 for testing.
            return 0

        def cleanup(self):
            print("DummyGPIO: cleanup()")

    GPIO = _DummyGPIO()
import time
import os
import threading

# GPIO setup
PIR_PIN = 14  # GPIO pin for PIR motion sensor
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

# Video configuration
VIDEO_PATH = "../../assets/videos/single_video_1_720p.mp4"

class VideoPlayer:
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = None
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        # init_video returns a bool; store it so callers can verify
        self.initialized = self.init_video()
        
    def init_video(self):
        """Initialize video capture and get video properties"""
        if not os.path.exists(self.video_path):
            print(f"Error: Video file not found at {self.video_path}")
            return False
            
        self.cap = cv2.VideoCapture(self.video_path)
        if not self.cap.isOpened():
            print("Error: Could not open video file")
            return False
            
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"Video loaded: {self.total_frames} frames at {self.fps} FPS")
        
        # Set up display window
        cv2.namedWindow('Halloween Video', cv2.WINDOW_FULLSCREEN)
        return True
        
    def show_first_frame(self):
        """Display the first frame of the video"""
        if self.cap is None:
            return
            
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = self.cap.read()
        if ret:
            cv2.imshow('Halloween Video', frame)
            cv2.waitKey(1)
            self.current_frame = 0
            
    def play_video(self):
        """Play the video from current position"""
        if self.cap is None or self.is_playing:
            return
            
        self.is_playing = True
        print("Playing video...")
        
        frame_delay = 1.0 / self.fps
        
        while self.is_playing and self.current_frame < self.total_frames:
            ret, frame = self.cap.read()
            if not ret:
                break
                
            cv2.imshow('Halloween Video', frame)
            self.current_frame += 1
            
            # Check for ESC key to exit
            key = cv2.waitKey(int(frame_delay * 1000)) & 0xFF
            if key == 27:  # ESC key
                break
                
        self.is_playing = False
        print("Video finished playing")
        
        # Return to first frame
        self.show_first_frame()
        
    def cleanup(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()

def detect_motion():
    """Detect motion using PIR sensor"""
    return GPIO.input(PIR_PIN)

def main():
    """Main function"""
    try:
        print("Initializing Halloween Video Player...")
        
        # Initialize video player
        player = VideoPlayer(VIDEO_PATH)
        if not getattr(player, 'initialized', False):
            print("Video player failed to initialize. Exiting.")
            return
        
        # Show first frame initially
        player.show_first_frame()
        print("Showing first frame. Waiting for motion detection...")
        
        last_trigger_time = 0
        cooldown_period = 2  # Seconds to wait before allowing another trigger
        
        while True:
            try:
                # Check for motion
                motion_detected = detect_motion()
                current_time = time.time()
                
                # Check if motion detected and cooldown period has passed
                if (motion_detected and 
                    not player.is_playing and 
                    current_time - last_trigger_time > cooldown_period):
                    
                    print("Motion detected - Playing video!")
                    last_trigger_time = current_time

                    # Run play_video() in the main thread (or a separate process) so
                    # OpenCV GUI calls (imshow/waitKey) run in the main thread of
                    # that process. Using a background thread can prevent window
                    # updates on many platforms.
                    player.play_video()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\nShutting down...")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(1)
                
    except Exception as e:
        print(f"Error initializing: {e}")
    finally:
        # Cleanup
        player.cleanup()
        GPIO.cleanup()
        print("Cleanup complete")

if __name__ == "__main__":
    main()
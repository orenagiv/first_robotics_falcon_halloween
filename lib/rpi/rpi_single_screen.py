# The following script will load and rotate through 3 single screen videos and pause on the first frame.
# This script is a python script that will run on Raspberry Pi.
# We will use a motion detection sensor "GPIO" connected to pin 14.
# When the sensor detects motion closer than one meter of range - then play the video.
# When the video ends go back to the first frame of the next video (rotating through all 3 videos).

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
VIDEO_PATHS = [
    "../../assets/videos/single_video_1_720p.mp4",
    "../../assets/videos/single_video_2_720p.mp4",
    "../../assets/videos/single_video_3_720p.mp4"
]

class VideoPlayer:
    def __init__(self, video_paths):
        self.video_paths = video_paths
        self.current_video_index = 0
        self.cap = None
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        # init_video returns a bool; store it so callers can verify
        self.initialized = self.init_video()
        
    def init_video(self):
        """Initialize video capture and get video properties"""
        current_video_path = self.video_paths[self.current_video_index]
        
        if not os.path.exists(current_video_path):
            print(f"Error: Video file not found at {current_video_path}")
            return False
            
        self.cap = cv2.VideoCapture(current_video_path)
        if not self.cap.isOpened():
            print("Error: Could not open video file")
            return False
            
        self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        print(f"Video {self.current_video_index + 1} loaded: {self.total_frames} frames at {self.fps} FPS")
        
        # Set up display window for true full-screen
        cv2.namedWindow('Halloween Video', cv2.WINDOW_NORMAL)
        cv2.moveWindow('Halloween Video', 0, 0)  # Position at top-left
        cv2.setWindowProperty('Halloween Video', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
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
        print(f"Playing video {self.current_video_index + 1}...")
        
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
        print(f"Video {self.current_video_index + 1} finished playing")
        
        # Move to next video (rotate)
        self.rotate_to_next_video()
        
        # Return to first frame of new video
        self.show_first_frame()
        
    def rotate_to_next_video(self):
        """Rotate to the next video"""
        # Clean up current video capture
        if self.cap:
            self.cap.release()
            
        # Move to next video (with wraparound)
        self.current_video_index = (self.current_video_index + 1) % len(self.video_paths)
        print(f"Rotating to video {self.current_video_index + 1}")
        
        # Initialize new video
        self.init_video()
        
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
        player = VideoPlayer(VIDEO_PATHS)
        if not getattr(player, 'initialized', False):
            print("Video player failed to initialize. Exiting.")
            return
        
        # Show first frame initially
        player.show_first_frame()
        print("Showing first frame. Waiting for motion detection...")
        print(f"Starting with video {player.current_video_index + 1} of {len(VIDEO_PATHS)}")
        
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
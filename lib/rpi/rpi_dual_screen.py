# The following script will load dual videos (left and right screens) and pause on the first frame.
# This script is a python script that will run on Raspberry Pi.
# We will use a motion detection sensor "GPIO" connected to pin 14.
# When the sensor detects motion closer than one meter of range - then play the videos.
# When the videos end go back to the first frame of the videos.
# The script rotates between 3 sets of dual videos: dual_video_1, dual_video_2, dual_video_3

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
VIDEO_SETS = [
    {
        'left': "../../assets/videos/dual_video_1_left_720p.mp4",
        'right': "../../assets/videos/dual_video_1_right_720p.mp4"
    },
    {
        'left': "../../assets/videos/dual_video_2_left_720p.mp4",
        'right': "../../assets/videos/dual_video_2_right_720p.mp4"
    },
    {
        'left': "../../assets/videos/dual_video_3_left_720p.mp4",
        'right': "../../assets/videos/dual_video_3_right_720p.mp4"
    }
]

class DualVideoPlayer:
    def __init__(self, video_sets):
        self.video_sets = video_sets
        self.current_set_index = 0
        self.cap_left = None
        self.cap_right = None
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        # init_video returns a bool; store it so callers can verify
        self.initialized = self.init_video()
        
    def init_video(self):
        """Initialize video captures for current video set and get video properties"""
        current_set = self.video_sets[self.current_set_index]
        
        # Check if both video files exist
        if not os.path.exists(current_set['left']):
            print(f"Error: Left video file not found at {current_set['left']}")
            return False
        if not os.path.exists(current_set['right']):
            print(f"Error: Right video file not found at {current_set['right']}")
            return False
            
        # Initialize both video captures
        self.cap_left = cv2.VideoCapture(current_set['left'])
        self.cap_right = cv2.VideoCapture(current_set['right'])
        
        if not self.cap_left.isOpened():
            print("Error: Could not open left video file")
            return False
        if not self.cap_right.isOpened():
            print("Error: Could not open right video file")
            return False
            
        # Get video properties (assuming both videos have same properties)
        self.total_frames = int(self.cap_left.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap_left.get(cv2.CAP_PROP_FPS)
        print(f"Video set {self.current_set_index + 1} loaded: {self.total_frames} frames at {self.fps} FPS")
        
        # Set up display windows for dual screens
        cv2.namedWindow('Halloween Video Left', cv2.WINDOW_NORMAL)
        cv2.namedWindow('Halloween Video Right', cv2.WINDOW_NORMAL)
        
        # Position windows for dual screen setup
        # Assuming two screens side by side at 1280x720 resolution
        cv2.moveWindow('Halloween Video Left', 0, 0)  # Left screen
        cv2.moveWindow('Halloween Video Right', 1280, 0)  # Right screen
        
        # Set to fullscreen
        cv2.setWindowProperty('Halloween Video Left', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        cv2.setWindowProperty('Halloween Video Right', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        return True
        
    def show_first_frame(self):
        """Display the first frame of both videos"""
        if self.cap_left is None or self.cap_right is None:
            return
            
        # Set both videos to first frame
        self.cap_left.set(cv2.CAP_PROP_POS_FRAMES, 0)
        self.cap_right.set(cv2.CAP_PROP_POS_FRAMES, 0)
        
        # Read and display first frames
        ret_left, frame_left = self.cap_left.read()
        ret_right, frame_right = self.cap_right.read()
        
        if ret_left and ret_right:
            cv2.imshow('Halloween Video Left', frame_left)
            cv2.imshow('Halloween Video Right', frame_right)
            cv2.waitKey(1)
            self.current_frame = 0
            
    def play_video(self):
        """Play both videos simultaneously from current position"""
        if self.cap_left is None or self.cap_right is None or self.is_playing:
            return
            
        self.is_playing = True
        print(f"Playing video set {self.current_set_index + 1}...")
        
        frame_delay = 1.0 / self.fps
        
        while self.is_playing and self.current_frame < self.total_frames:
            # Read frames from both videos
            ret_left, frame_left = self.cap_left.read()
            ret_right, frame_right = self.cap_right.read()
            
            if not ret_left or not ret_right:
                break
                
            # Display both frames
            cv2.imshow('Halloween Video Left', frame_left)
            cv2.imshow('Halloween Video Right', frame_right)
            self.current_frame += 1
            
            # Check for ESC key to exit
            key = cv2.waitKey(int(frame_delay * 1000)) & 0xFF
            if key == 27:  # ESC key
                break
                
        self.is_playing = False
        print(f"Video set {self.current_set_index + 1} finished playing")
        
        # Move to next video set (rotate)
        self.rotate_to_next_set()
        
        # Return to first frame of new set
        self.show_first_frame()
        
    def rotate_to_next_set(self):
        """Rotate to the next video set"""
        # Clean up current video captures
        if self.cap_left:
            self.cap_left.release()
        if self.cap_right:
            self.cap_right.release()
            
        # Move to next set (with wraparound)
        self.current_set_index = (self.current_set_index + 1) % len(self.video_sets)
        print(f"Rotating to video set {self.current_set_index + 1}")
        
        # Initialize new video set
        self.init_video()
        
    def cleanup(self):
        """Clean up resources"""
        if self.cap_left:
            self.cap_left.release()
        if self.cap_right:
            self.cap_right.release()
        cv2.destroyAllWindows()

def detect_motion():
    """Detect motion using PIR sensor"""
    return GPIO.input(PIR_PIN)

def main():
    """Main function"""
    try:
        print("Initializing Halloween Dual Video Player...")
        
        # Initialize dual video player
        player = DualVideoPlayer(VIDEO_SETS)
        if not getattr(player, 'initialized', False):
            print("Dual video player failed to initialize. Exiting.")
            return
        
        # Show first frame initially
        player.show_first_frame()
        print("Showing first frames. Waiting for motion detection...")
        
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
                    
                    print("Motion detected - Playing dual videos!")
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
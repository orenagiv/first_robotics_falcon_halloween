# The following script will load specific video (assets/single_screen_1/UP_Madam_LivingNightmare_TV_V.mp4) and pause on the first frame.
# This script is a python script that will run on Raspberry Pi.
# We will use a motion detection sensor "GPIO" connected to pin 14.
# When the sensor detects motion closer than one meter of range - then play the video.
# When the video ends go back to the first frame of the video.

import cv2
import RPi.GPIO as GPIO
import time
import os
import threading

# GPIO setup
TRIGGER_PIN = 18  # GPIO pin for ultrasonic sensor trigger
ECHO_PIN = 14     # GPIO pin for ultrasonic sensor echo
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIGGER_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# Video configuration
VIDEO_PATH = "../../assets/videos/single_screen_1/UP_Madam_LivingNightmare_TV_V.mp4"
MOTION_THRESHOLD = 100  # Distance threshold in cm (1 meter)

class VideoPlayer:
    def __init__(self, video_path):
        self.video_path = video_path
        self.cap = None
        self.is_playing = False
        self.current_frame = 0
        self.total_frames = 0
        self.fps = 30
        self.init_video()
        
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

def measure_distance():
    """Measure distance using ultrasonic sensor"""
    # Send trigger pulse
    GPIO.output(TRIGGER_PIN, True)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.output(TRIGGER_PIN, False)
    
    # Measure echo time
    start_time = time.time()
    stop_time = time.time()
    
    # Wait for echo start
    timeout = time.time() + 1  # 1 second timeout
    while GPIO.input(ECHO_PIN) == 0 and time.time() < timeout:
        start_time = time.time()
    
    # Wait for echo end
    timeout = time.time() + 1  # 1 second timeout
    while GPIO.input(ECHO_PIN) == 1 and time.time() < timeout:
        stop_time = time.time()
    
    # Calculate distance
    time_elapsed = stop_time - start_time
    distance = (time_elapsed * 34300) / 2  # Speed of sound = 343 m/s
    
    return distance

def main():
    """Main function"""
    try:
        print("Initializing Halloween Video Player...")
        
        # Initialize video player
        player = VideoPlayer(VIDEO_PATH)
        
        # Show first frame initially
        player.show_first_frame()
        print("Showing first frame. Waiting for motion detection...")
        
        last_trigger_time = 0
        cooldown_period = 2  # Seconds to wait before allowing another trigger
        
        while True:
            try:
                # Measure distance
                distance = measure_distance()
                current_time = time.time()
                
                # Check if motion detected within threshold and cooldown period has passed
                if (distance < MOTION_THRESHOLD and 
                    distance > 0 and 
                    not player.is_playing and 
                    current_time - last_trigger_time > cooldown_period):
                    
                    print(f"Motion detected at {distance:.1f}cm - Playing video!")
                    last_trigger_time = current_time
                    
                    # Play video in a separate thread to avoid blocking distance measurement
                    video_thread = threading.Thread(target=player.play_video)
                    video_thread.daemon = True
                    video_thread.start()
                
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
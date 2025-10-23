# Simplified Halloween Video Player for Raspberry Pi
# Rotates through 3 videos, shows first frame when idle, plays on motion detection

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
            # For testing purposes, you can change this to return 1 to simulate motion
            # or add logic to simulate motion detection
            return 0

        def cleanup(self):
            print("DummyGPIO: cleanup()")

    GPIO = _DummyGPIO()

import time
import os
import subprocess
import signal
import vlc

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global shutdown_requested
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    shutdown_requested = True

def configure_display():
    """Configure display resolution for portrait mode videos"""
    try:
        # Set resolution to 720x1280 (portrait mode, no rotation needed)
        subprocess.run(['xrandr', '--output', 'HDMI-1', '--mode', '720x1280'], check=True)
        print("Display resolution set to 720x1280 (portrait)")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not configure display: {e}")
        try:
            # Try HDMI-2 if HDMI-1 fails
            subprocess.run(['xrandr', '--output', 'HDMI-2', '--mode', '720x1280'], check=True)
            print("Display configured on HDMI-2")
        except subprocess.CalledProcessError as e2:
            print(f"Warning: Could not configure display on HDMI-2: {e2}")
    except Exception as e:
        print(f"Warning: Unexpected error configuring display: {e}")

# GPIO setup
PIR_PIN = 14  # GPIO pin for PIR motion sensor
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

# Video configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_PATHS = [
    os.path.join(SCRIPT_DIR, "../../assets/videos/single_video_1_720x1280p.mp4"),
    os.path.join(SCRIPT_DIR, "../../assets/videos/single_video_2_720x1280p.mp4"),
    os.path.join(SCRIPT_DIR, "../../assets/videos/single_video_3_720x1280p.mp4")
]

# Debug: Print the video paths to verify they're correct
print(f"Script directory: {SCRIPT_DIR}")
for i, path in enumerate(VIDEO_PATHS):
    print(f"Video {i+1} path: {path}")
    print(f"Video {i+1} exists: {os.path.exists(path)}")

class SimpleVideoPlayer:
    def __init__(self, video_paths):
        print("Initializing SimpleVideoPlayer...")
        self.video_paths = video_paths
        self.current_video_index = 0
        self.is_playing = False
        self.vlc_instance = None
        self.vlc_player = None
        
        # Check if video files exist
        print("Checking video files...")
        self.initialized = self._check_videos()
        if self.initialized:
            print("Videos found, starting VLC instance...")
            vlc_started = self._start_vlc_instance()
            if not vlc_started:
                print("Failed to start VLC, marking as not initialized")
                self.initialized = False
        else:
            print("Video check failed")
        
    def _check_videos(self):
        """Check if all video files exist"""
        for i, video_path in enumerate(self.video_paths):
            if not os.path.exists(video_path):
                print(f"Error: Video file not found at {video_path}")
                return False
            print(f"Video {i + 1} found: {video_path}")
        return True
    
    def _start_vlc_instance(self):
        """Start a VLC instance using python-vlc"""
        try:
            # Check if VLC is available
            try:
                vlc.Instance()
                print("VLC is available")
            except Exception as e:
                print(f"VLC is not available or not installed: {e}")
                return False
            
            # Create VLC instance with appropriate options
            self.vlc_instance = vlc.Instance([
                '--intf', 'dummy',  # No interface
                '--fullscreen',     # Start in fullscreen
                '--no-video-title-show',  # Don't show video title
                '--no-osd',         # No on-screen display
                '--no-audio',       # Disable audio to reduce overhead
                '--video-on-top',   # Ensure video stays on top
                '--no-video-deco',  # No window decorations
                '--quiet'           # Reduce console output
            ])
            
            # Create media player
            self.vlc_player = self.vlc_instance.media_player_new()
            
            print("VLC instance and player created successfully")
            return True
            
        except Exception as e:
            print(f"Error starting VLC instance: {e}")
            return False
    
    def show_first_frame(self):
        """Show the first frame of current video and pause"""
        if not self.initialized:
            return False
            
        current_video = self.video_paths[self.current_video_index]
        print(f"Showing first frame of video {self.current_video_index + 1}")
        
        try:
            # Create media for current video
            media = self.vlc_instance.media_new(current_video)
            self.vlc_player.set_media(media)
            
            # Start playing to load the first frame
            self.vlc_player.play()
            
            # Wait a moment for the video to start
            time.sleep(0.5)
            
            # Pause to show only the first frame
            self.vlc_player.pause()
            
            print(f"First frame displayed for video {self.current_video_index + 1}")
            return True
            
        except Exception as e:
            print(f"Error showing first frame: {e}")
            return False
    
    def play_video(self):
        """Play the current video from start to finish"""
        if self.is_playing:
            return
            
        if not self.initialized:
            return
            
        current_video = self.video_paths[self.current_video_index]
        print(f"Playing video {self.current_video_index + 1}: {current_video}")
        
        self.is_playing = True
        
        try:
            # Create media for current video
            media = self.vlc_instance.media_new(current_video)
            self.vlc_player.set_media(media)
            
            # Start playing
            self.vlc_player.play()
            
            # Wait for video to finish playing
            self._wait_for_video_end()
            
            print(f"Video {self.current_video_index + 1} finished playing")
            
        except Exception as e:
            print(f"Error playing video: {e}")
        finally:
            self.is_playing = False
            # Move to next video
            self._rotate_to_next_video()
    
    def _wait_for_video_end(self):
        """Wait for current video to finish playing"""
        print("Waiting for video to finish...")
        
        # Wait for the video to start
        time.sleep(1)
        
        while not shutdown_requested and self.is_playing:
            state = self.vlc_player.get_state()
            
            if state == vlc.State.Ended:
                print("Video playback ended")
                break
            elif state == vlc.State.Error:
                print("Video playback error")
                break
            elif state == vlc.State.Stopped:
                print("Video playback stopped")
                break
                
            # Check every 0.1 seconds
            time.sleep(0.1)
    
    def _rotate_to_next_video(self):
        """Move to the next video in the sequence"""
        self.current_video_index = (self.current_video_index + 1) % len(self.video_paths)
        print(f"Rotated to video {self.current_video_index + 1}")
    
    def cleanup(self):
        """Clean up resources"""
        self.is_playing = False
        if self.vlc_player:
            try:
                self.vlc_player.stop()
                self.vlc_player.release()
                print("VLC player stopped and released")
            except Exception as e:
                print(f"Error during VLC player cleanup: {e}")
            finally:
                self.vlc_player = None
        
        if self.vlc_instance:
            try:
                self.vlc_instance.release()
                print("VLC instance released")
            except Exception as e:
                print(f"Error during VLC instance cleanup: {e}")
            finally:
                self.vlc_instance = None

def detect_motion():
    """Detect motion using PIR sensor"""
    return GPIO.input(PIR_PIN)

def main():
    """Main function"""
    global shutdown_requested
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print("Initializing Simple Halloween Video Player...")
        print(f"Python version: {subprocess.run(['python3', '--version'], capture_output=True, text=True).stdout.strip()}")
        
        # Check if VLC is available
        try:
            vlc.Instance()
            print("VLC library is available")
        except Exception as e:
            print(f"Error: VLC not available. Please install VLC and python-vlc.")
            print(f"Install with: pip install python-vlc")
            return
        
        # Configure display resolution and orientation
        configure_display()
        
        # Initialize video player
        print("Creating video player instance...")
        player = SimpleVideoPlayer(VIDEO_PATHS)
        if not player.initialized:
            print("Video player failed to initialize. Exiting.")
            return
        
        print("Video player initialized successfully")
        
        # Show first frame initially
        print("Attempting to show initial first frame...")
        for attempt in range(3):  # Try up to 3 times
            print(f"First frame attempt {attempt + 1}...")
            if player.show_first_frame():
                print("Initial first frame displayed successfully")
                break
            else:
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2)
        else:
            print("Warning: Failed to show initial first frame after 3 attempts")
            # Continue anyway - maybe the video will display when motion is detected
            
        print("Showing first frame. Waiting for motion detection...")
        print(f"Starting with video {player.current_video_index + 1} of {len(VIDEO_PATHS)}")
        
        last_trigger_time = 0
        cooldown_period = 3  # Seconds to wait before allowing another trigger
        last_debug_time = 0  # Track debug output timing
        
        while not shutdown_requested:
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

                    # Play the video (this will block until video finishes)
                    player.play_video()
                    
                    # After video finishes, show the first frame of the next video
                    print(f"Video finished. Now showing video {player.current_video_index + 1}")
                    if not player.show_first_frame():
                        print("Warning: Failed to show first frame after video playback")
                    else:
                        print("Ready for next motion detection...")
                
                # Debug output every 10 seconds to show status
                if current_time - last_debug_time >= 10:
                    print(f"Status: Motion={motion_detected}, Playing={player.is_playing}, Video={player.current_video_index + 1}")
                    last_debug_time = current_time
                
                # Small delay to prevent excessive CPU usage
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                print("\nShutting down...")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(1)
                
    except Exception as e:
        print(f"Error initializing: {e}")
    finally:
        # Clean up
        if 'player' in locals():
            player.cleanup()
        GPIO.cleanup()
        print("Cleanup complete")

if __name__ == "__main__":
    main()
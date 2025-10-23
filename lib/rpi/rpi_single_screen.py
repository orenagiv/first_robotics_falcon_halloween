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
        self.vlc_process = None
        
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
        """Start a persistent VLC instance with RC interface"""
        try:
            # Check if VLC is available
            try:
                subprocess.run(['vlc', '--version'], capture_output=True, check=True)
                print("VLC is available")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"VLC is not available or not installed: {e}")
                return False
            
            # Kill any existing VLC instances first
            self._kill_existing_vlc()
            
            cmd = [
                'vlc',
                '--fullscreen',
                '--no-video-title-show',
                '--no-osd',
                '--no-audio',  # Disable audio to reduce overhead
                '--intf', 'rc',  # Remote control interface
                '--video-on-top',  # Ensure video stays on top
                '--no-video-deco',  # No window decorations
                '--start-paused'
            ]
            
            print(f"Starting VLC with command: {' '.join(cmd)}")
            
            self.vlc_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            time.sleep(3)  # Give VLC time to start
            
            # Check if VLC process is still running
            if self.vlc_process.poll() is None:
                print("VLC process started successfully")
                return True
            else:
                # VLC process died, get error output
                try:
                    stdout, stderr = self.vlc_process.communicate(timeout=1)
                    print(f"VLC process failed to start. Return code: {self.vlc_process.returncode}")
                    print(f"STDOUT: {stdout}")
                    print(f"STDERR: {stderr}")
                except subprocess.TimeoutExpired:
                    print("VLC process failed to start (timeout getting output)")
                self.vlc_process = None
                return False
            
        except Exception as e:
            print(f"Error starting VLC instance: {e}")
            return False
    
    def _send_vlc_command(self, command):
        """Send command to VLC via stdin"""
        try:
            if self.vlc_process and self.vlc_process.poll() is None:
                self.vlc_process.stdin.write(f"{command}\n")
                self.vlc_process.stdin.flush()
                print(f"VLC command sent: {command}")
                return True
            else:
                print(f"VLC process not available (poll result: {self.vlc_process.poll() if self.vlc_process else 'None'})")
                return False
        except BrokenPipeError:
            print(f"Broken pipe when sending VLC command '{command}' - VLC may have crashed")
            self.vlc_process = None
            return False
        except Exception as e:
            print(f"Error sending VLC command '{command}': {e}")
            return False
    
    def _get_video_duration(self, video_path):
        """Get video duration in seconds using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-show_entries', 
                'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                return duration
        except Exception as e:
            print(f"Could not get video duration: {e}")
        
        # Fallback to default duration if ffprobe fails
        return 30.0  # Default 30 seconds
    
    def _kill_existing_vlc(self):
        """Kill any existing VLC processes"""
        try:
            subprocess.run(['pkill', '-f', 'vlc'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(0.5)  # Give time for processes to die
        except Exception:
            pass
    
    def show_first_frame(self):
        """Show the first frame of current video and pause"""
        if not self.initialized:
            return False
            
        current_video = self.video_paths[self.current_video_index]
        print(f"Showing first frame of video {self.current_video_index + 1}")
        
        try:
            # Clear the playlist and add the current video
            self._send_vlc_command("clear")
            time.sleep(0.2)  # Small delay after clear
            self._send_vlc_command(f"add {current_video}")
            time.sleep(0.3)  # Allow time for video to be added
            
            # Start playing to load the video
            self._send_vlc_command("play")
            time.sleep(1.5)  # Longer wait to ensure first frame loads properly
            
            # Seek to beginning and pause
            self._send_vlc_command("seek 0")
            time.sleep(0.2)
            self._send_vlc_command("pause")
            
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
            # Since show_first_frame() already loaded the video and paused it,
            # we just need to seek to the beginning and resume playback
            self._send_vlc_command("seek 0")
            time.sleep(0.1)  # Brief pause to ensure seek completes
            self._send_vlc_command("play")
            
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
        current_video = self.video_paths[self.current_video_index]
        video_duration = self._get_video_duration(current_video)
        print(f"Video duration: {video_duration:.1f} seconds")
        
        # Add a small buffer to ensure video finishes completely
        wait_time = video_duration + 2.0
        start_time = time.time()
        
        while not shutdown_requested and self.is_playing:
            elapsed_time = time.time() - start_time
            
            if elapsed_time >= wait_time:
                print("Video playback should be complete")
                break
                
            # Check every 0.5 seconds
            time.sleep(0.5)
    
    def _rotate_to_next_video(self):
        """Move to the next video in the sequence"""
        self.current_video_index = (self.current_video_index + 1) % len(self.video_paths)
        print(f"Rotated to video {self.current_video_index + 1}")
    
    def cleanup(self):
        """Clean up resources"""
        self.is_playing = False
        if self.vlc_process:
            try:
                self._send_vlc_command("quit")
                try:
                    self.vlc_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print("VLC didn't quit gracefully, terminating...")
                    self.vlc_process.terminate()
                    try:
                        self.vlc_process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        print("Force killing VLC process...")
                        self.vlc_process.kill()
            except Exception as e:
                print(f"Error during VLC cleanup: {e}")
                try:
                    self.vlc_process.terminate()
                except:
                    pass
            finally:
                self.vlc_process = None

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
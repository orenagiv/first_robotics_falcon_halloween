# The following script will load dual videos (left and right screens) and pause on the first frame.
# This script is a python script that will run on Raspberry Pi.
# We will use a motion detection sensor "GPIO" connected to pin 14.
# When the sensor detects motion closer than one meter of range - then play the videos.
# When the videos end go back to the first frame of the videos.
# The script rotates between 3 sets of dual videos: dual_video_1, dual_video_2, dual_video_3

# Using VLC for better performance and audio support
# Note: For proper dual-screen positioning, ensure X11 environment is configured for dual displays
# The xrandr commands in configure_display() should position screens correctly

# Standard library imports
import time
import os
import subprocess
import signal
import sys

# Third-party imports
import vlc

# Add the parent directory to the path so we can import from lib
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local imports
from common.configure_displays import configure_display

# GPIO setup with fallback for non-RPi systems
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

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global shutdown_requested
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    shutdown_requested = True

# GPIO setup
PIR_PIN = 14  # GPIO pin for PIR motion sensor
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

# Video configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VIDEO_SETS = [
    {
        'left': os.path.join(SCRIPT_DIR, "../../assets/videos/single_video_1_720x1280p.mp4"),
        'right': os.path.join(SCRIPT_DIR, "../../assets/videos/single_video_2_720x1280p.mp4")
    },
    # {
    #     'left': os.path.join(SCRIPT_DIR, "../../assets/videos/dual_video_1_left_720x1280p.mp4"),
    #     'right': os.path.join(SCRIPT_DIR, "../../assets/videos/dual_video_1_right_720x1280p.mp4")
    # },
    # {
    #     'left': os.path.join(SCRIPT_DIR, "../../assets/videos/dual_video_2_left_720x1280p.mp4"),
    #     'right': os.path.join(SCRIPT_DIR, "../../assets/videos/dual_video_2_right_720x1280p.mp4")
    # },
    # {
    #     'left': os.path.join(SCRIPT_DIR, "../../assets/videos/dual_video_3_left_720x1280p.mp4"),
    #     'right': os.path.join(SCRIPT_DIR, "../../assets/videos/dual_video_3_right_720x1280p.mp4")
    # }
]

# Debug: Print the video paths to verify they're correct
print(f"Script directory: {SCRIPT_DIR}")
for i, video_set in enumerate(VIDEO_SETS):
    print(f"Video set {i+1} left path: {video_set['left']}")
    print(f"Video set {i+1} left exists: {os.path.exists(video_set['left'])}")
    print(f"Video set {i+1} right path: {video_set['right']}")
    print(f"Video set {i+1} right exists: {os.path.exists(video_set['right'])}")

class DualVideoPlayer:
    def __init__(self, video_sets):
        print("Initializing DualVideoPlayer...")
        self.video_sets = video_sets
        self.current_set_index = 0
        self.is_playing = False
        self.vlc_instance_left = None
        self.vlc_instance_right = None
        self.vlc_player_left = None
        self.vlc_player_right = None
        
        # Check if video files exist
        print("Checking video files...")
        self.initialized = self._check_videos()
        if self.initialized:
            print("Videos found, starting VLC instances...")
            vlc_started = self._start_vlc_instances()
            if not vlc_started:
                print("Failed to start VLC instances, marking as not initialized")
                self.initialized = False
        else:
            print("Video check failed")
        
    def _check_videos(self):
        """Check if all video files exist"""
        for i, video_set in enumerate(self.video_sets):
            if not os.path.exists(video_set['left']):
                print(f"Error: Left video file not found at {video_set['left']}")
                return False
            if not os.path.exists(video_set['right']):
                print(f"Error: Right video file not found at {video_set['right']}")
                return False
            print(f"Video set {i + 1} found: left={video_set['left']}, right={video_set['right']}")
        return True
    
    def _start_vlc_instances(self):
        """Start VLC instances for both left and right screens using python-vlc"""
        try:
            # Check if VLC is available
            try:
                vlc.Instance()
                print("VLC is available")
            except Exception as e:
                print(f"VLC is not available or not installed: {e}")
                return False
            
            # Create VLC instance for left screen - windowed mode first, then position
            self.vlc_instance_left = vlc.Instance([
                '--intf', 'dummy',  # No interface
                '--no-video-title-show',  # Don't show video title
                '--no-osd',         # No on-screen display
                '--video-on-top',   # Ensure video stays on top
                '--no-video-deco',  # No window decorations
                '--no-embedded-video',  # Don't embed video in interface
                '--no-qt-privacy-ask',  # Don't ask for privacy settings
                '--aout', 'alsa',   # Use ALSA audio output (common on Raspberry Pi)
                # '--no-audio',
                '--quiet'           # Reduce console output
            ])
            
            # Create VLC instance for right screen - windowed mode first, then position
            self.vlc_instance_right = vlc.Instance([
                '--intf', 'dummy',  # No interface
                '--no-video-title-show',  # Don't show video title
                '--no-osd',         # No on-screen display
                '--video-on-top',   # Ensure video stays on top
                '--no-video-deco',  # No window decorations
                '--no-embedded-video',  # Don't embed video in interface
                '--no-qt-privacy-ask',  # Don't ask for privacy settings
                '--aout', 'alsa',   # Use ALSA audio output (common on Raspberry Pi)
                # '--no-audio',
                '--quiet'           # Reduce console output
            ])
            
            # Create media players
            self.vlc_player_left = self.vlc_instance_left.media_player_new()
            self.vlc_player_right = self.vlc_instance_right.media_player_new()
            
            # Don't set fullscreen immediately - we'll position windows first when playing

            # Set volume to 100% for left player (audio), 0% for right player (no audio to avoid duplicate)
            self.vlc_player_left.audio_set_volume(100)
            self.vlc_player_right.audio_set_volume(100)  # Mute right player to avoid audio overlap
            print("VLC instances created: Left with audio (100%), Right muted")
            print("Window positioning will be handled when videos are played")
            
            print("VLC instances and players created successfully")
            return True
            
        except Exception as e:
            print(f"Error starting VLC instances: {e}")
            return False
    
    def _position_and_fullscreen_videos(self):
        """Position video windows on correct displays and set fullscreen"""
        try:
            print("Positioning video windows on dual screens...")
            
            # Wait a moment for windows to appear
            time.sleep(1.0)
            
            # Method 1: Try using xdotool to position windows
            try:
                # Get all VLC windows
                result = subprocess.run(['xdotool', 'search', '--class', 'vlc'], 
                                      capture_output=True, text=True, check=True)
                window_ids = result.stdout.strip().split('\n')
                
                if len(window_ids) >= 2:
                    # Move first VLC window to left screen (0,0)
                    subprocess.run(['xdotool', 'windowmove', window_ids[0], '0', '0'], check=True)
                    # Move second VLC window to right screen (720,0) 
                    subprocess.run(['xdotool', 'windowmove', window_ids[1], '720', '0'], check=True)
                    print(f"Positioned windows using xdotool: left at (0,0), right at (720,0)")
                    
                    # Now set both to fullscreen
                    self.vlc_player_left.set_fullscreen(True)
                    self.vlc_player_right.set_fullscreen(True)
                    print("Set both videos to fullscreen")
                    return True
                else:
                    print(f"Found {len(window_ids)} VLC windows, expected 2")
                    
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"xdotool positioning failed: {e}")
                
            # Method 2: Fallback - try using wmctrl if available
            try:
                # List all windows to find VLC windows
                result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, check=True)
                vlc_windows = [line for line in result.stdout.split('\n') if 'vlc' in line.lower()]
                
                if len(vlc_windows) >= 2:
                    # Extract window IDs and move them
                    window_id_1 = vlc_windows[0].split()[0]
                    window_id_2 = vlc_windows[1].split()[0]
                    
                    # Move windows to different screens
                    subprocess.run(['wmctrl', '-i', '-r', window_id_1, '-e', '0,0,0,720,1280'], check=True)
                    subprocess.run(['wmctrl', '-i', '-r', window_id_2, '-e', '0,720,0,720,1280'], check=True)
                    print("Positioned windows using wmctrl")
                    
                    # Set fullscreen
                    self.vlc_player_left.set_fullscreen(True)
                    self.vlc_player_right.set_fullscreen(True)
                    return True
                    
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                print(f"wmctrl positioning failed: {e}")
            
            # Method 3: Fallback - just set fullscreen and hope for the best
            print("Window positioning tools not available, setting fullscreen directly")
            self.vlc_player_left.set_fullscreen(True)
            self.vlc_player_right.set_fullscreen(True)
            return True
                    
        except Exception as e:
            print(f"Error in positioning videos: {e}")
            # Still try to set fullscreen as fallback
            try:
                self.vlc_player_left.set_fullscreen(True)
                self.vlc_player_right.set_fullscreen(True)
            except:
                pass
            return False
    
    def set_fullscreen(self):
        """Set both players to fullscreen mode with proper positioning"""
        try:
            self._position_and_fullscreen_videos()
        except Exception as e:
            print(f"Error setting fullscreen: {e}")
    
    def show_first_frame(self):
        """Show the first frame of current video set and pause"""
        if not self.initialized:
            return False
            
        current_set = self.video_sets[self.current_set_index]
        print(f"Showing first frame of video set {self.current_set_index + 1}")
        
        try:
            # Create media for current video set
            media_left = self.vlc_instance_left.media_new(current_set['left'])
            media_right = self.vlc_instance_right.media_new(current_set['right'])
            
            self.vlc_player_left.set_media(media_left)
            self.vlc_player_right.set_media(media_right)
            
            # Start playing to load the first frame
            self.vlc_player_left.play()
            self.vlc_player_right.play()

            # Position windows and set fullscreen
            self._position_and_fullscreen_videos()

            # Wait a moment for the videos to start and positioning to take effect
            time.sleep(0.5)
            
            # Pause to show only the first frame
            self.vlc_player_left.pause()
            self.vlc_player_right.pause()
            
            print(f"First frames displayed for video set {self.current_set_index + 1}")
            return True
            
        except Exception as e:
            print(f"Error showing first frame: {e}")
            return False
    
    def play_video(self):
        """Play the current video set from start to finish"""
        if self.is_playing:
            return
            
        if not self.initialized:
            return
            
        current_set = self.video_sets[self.current_set_index]
        print(f"Playing video set {self.current_set_index + 1}: left={current_set['left']}, right={current_set['right']}")
        
        self.is_playing = True
        
        try:
            # Create media for current video set
            media_left = self.vlc_instance_left.media_new(current_set['left'])
            media_right = self.vlc_instance_right.media_new(current_set['right'])
            
            self.vlc_player_left.set_media(media_left)
            self.vlc_player_right.set_media(media_right)
            
            # Start playing both videos simultaneously
            self.vlc_player_left.play()
            self.vlc_player_right.play()
            
            # Position windows and set fullscreen for playback
            self._position_and_fullscreen_videos()
            
            # Wait for videos to finish playing
            self._wait_for_videos_end()
            
            print(f"Video set {self.current_set_index + 1} finished playing")
            
        except Exception as e:
            print(f"Error playing videos: {e}")
        finally:
            self.is_playing = False
            # Move to next video set
            self._rotate_to_next_set()
    
    def _wait_for_videos_end(self):
        """Wait for both videos to finish playing"""
        print("Waiting for videos to finish...")
        
        # Wait for the videos to start
        time.sleep(1)
        
        while not shutdown_requested and self.is_playing:
            state_left = self.vlc_player_left.get_state()
            state_right = self.vlc_player_right.get_state()
            
            # Check if both videos have ended
            if (state_left == vlc.State.Ended or state_left == vlc.State.Error or state_left == vlc.State.Stopped) and \
               (state_right == vlc.State.Ended or state_right == vlc.State.Error or state_right == vlc.State.Stopped):
                print("Both videos finished")
                break
                
            # Check every 0.1 seconds
            time.sleep(0.1)
    
    def _rotate_to_next_set(self):
        """Move to the next video set in the sequence"""
        self.current_set_index = (self.current_set_index + 1) % len(self.video_sets)
        print(f"Rotated to video set {self.current_set_index + 1}")
    
    def cleanup(self):
        """Clean up resources"""
        self.is_playing = False
        
        if self.vlc_player_left:
            try:
                self.vlc_player_left.stop()
                self.vlc_player_left.release()
                print("Left VLC player stopped and released")
            except Exception as e:
                print(f"Error during left VLC player cleanup: {e}")
            finally:
                self.vlc_player_left = None
        
        if self.vlc_player_right:
            try:
                self.vlc_player_right.stop()
                self.vlc_player_right.release()
                print("Right VLC player stopped and released")
            except Exception as e:
                print(f"Error during right VLC player cleanup: {e}")
            finally:
                self.vlc_player_right = None
        
        if self.vlc_instance_left:
            try:
                self.vlc_instance_left.release()
                print("Left VLC instance released")
            except Exception as e:
                print(f"Error during left VLC instance cleanup: {e}")
            finally:
                self.vlc_instance_left = None
                
        if self.vlc_instance_right:
            try:
                self.vlc_instance_right.release()
                print("Right VLC instance released")
            except Exception as e:
                print(f"Error during right VLC instance cleanup: {e}")
            finally:
                self.vlc_instance_right = None

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
        print("Initializing Halloween Dual Video Player...")
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
        configure_display('dual')
        
        # Initialize dual video player
        print("Creating dual video player instance...")
        player = DualVideoPlayer(VIDEO_SETS)
        if not player.initialized:
            print("Dual video player failed to initialize. Exiting.")
            return
        
        print("Dual video player initialized successfully")
        
        # Show first frame initially
        print("Attempting to show initial first frames...")
        for attempt in range(3):  # Try up to 3 times
            print(f"First frame attempt {attempt + 1}...")
            if player.show_first_frame():
                print("Initial first frames displayed successfully")
                break
            else:
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2)
        else:
            print("Warning: Failed to show initial first frames after 3 attempts")
            # Continue anyway - maybe the videos will display when motion is detected
            
        print("Showing first frames. Waiting for motion detection...")
        print(f"Starting with video set {player.current_set_index + 1} of {len(VIDEO_SETS)}")
        
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
                    
                    print("Motion detected - Playing dual videos!")
                    last_trigger_time = current_time

                    # Play the videos (this will block until videos finish)
                    player.play_video()
                    
                    # After videos finish, show the first frame of the next video set
                    print(f"Videos finished. Now showing video set {player.current_set_index + 1}")
                    if not player.show_first_frame():
                        print("Warning: Failed to show first frames after video playback")
                    else:
                        print("Ready for next motion detection...")
                
                # Debug output every 10 seconds to show status
                if current_time - last_debug_time >= 10:
                    print(f"Status: Motion={motion_detected}, Playing={player.is_playing}, Video_set={player.current_set_index + 1}")
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
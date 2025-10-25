# Unified Halloween Video Player for Raspberry Pi
# Supports both single screen and dual screen modes
# Rotates through videos, shows first frame when idle, plays on motion detection

try:
    from gpiozero import MotionSensor
    PIR_AVAILABLE = True
except ImportError:
    # Allow running/testing on non-RPi systems by providing a dummy MotionSensor
    print("Warning: gpiozero not available. Creating dummy MotionSensor for testing.")
    class _DummyMotionSensor:
        def __init__(self, pin):
            self.pin = pin
            print(f"DummyMotionSensor: initialized on pin {pin}")
        
        @property
        def motion_detected(self):
            # For testing purposes, you can change this to return True to simulate motion
            return False
        
        def close(self):
            print("DummyMotionSensor: closed")
    
    MotionSensor = _DummyMotionSensor
    PIR_AVAILABLE = False

import time
import os
import subprocess
import signal
import vlc
import sys

# Add the parent directory to the path so we can import from lib
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Local imports
from common.configure_displays import configure_display

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global shutdown_requested
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    shutdown_requested = True

# PIR Motion Sensor setup
PIR_PIN = 14  # GPIO pin for PIR motion sensor
motion_sensor = None  # Will be initialized in main()

# Motion detection configuration
MOTION_THRESHOLD = 0.5  # Sensitivity: 0.0 (most sensitive) to 1.0 (least sensitive)
MOTION_SAMPLE_RATE = 10  # Samples per second
MOTION_QUEUE_LEN = 1    # Number of samples to average over
MOTION_DEBOUNCE_TIME = 0.5  # Minimum time between motion detections (seconds)
MOTION_CONFIRMATION_COUNT = 2  # Number of consecutive positive readings required
EXTENDED_COOLDOWN = 2  # Extra cooldown after video plays (seconds)

# Motion detection state
motion_confirmation_counter = 0
last_motion_time = 0

# Video configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Single video paths
SINGLE_VIDEO_PATHS = [
    # os.path.join(SCRIPT_DIR, "../../assets/videos/single_video_1_720x1280p.mp4"),
    # os.path.join(SCRIPT_DIR, "../../assets/videos/single_video_2_720x1280p.mp4"),
    os.path.join(SCRIPT_DIR, "../../assets/videos/single_video_3_720x1280p.mp4")
]

# Dual video sets
DUAL_VIDEO_SETS = [
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
for i, path in enumerate(SINGLE_VIDEO_PATHS):
    print(f"Single video {i+1} path: {path}")
    print(f"Single video {i+1} exists: {os.path.exists(path)}")

for i, video_set in enumerate(DUAL_VIDEO_SETS):
    print(f"Dual video set {i+1} left path: {video_set['left']}")
    print(f"Dual video set {i+1} left exists: {os.path.exists(video_set['left'])}")
    print(f"Dual video set {i+1} right path: {video_set['right']}")
    print(f"Dual video set {i+1} right exists: {os.path.exists(video_set['right'])}")

class UnifiedVideoPlayer:
    def __init__(self, mode="single"):
        print(f"Initializing UnifiedVideoPlayer in {mode} mode...")
        self.mode = mode
        self.current_index = 0
        self.is_playing = False
        
        # Select video paths based on mode
        if mode == "single":
            self.video_paths = SINGLE_VIDEO_PATHS
            print(f"Using single video mode with {len(self.video_paths)} videos")
        elif mode == "dual":
            self.video_paths = DUAL_VIDEO_SETS
            print(f"Using dual video mode with {len(self.video_paths)} video sets")
        else:
            raise ValueError(f"Invalid mode: {mode}. Must be 'single' or 'dual'")
        
        # VLC instances
        if mode == "single":
            self.vlc_instance = None
            self.vlc_player = None
        else:  # dual
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
        if self.mode == "single":
            for i, video_path in enumerate(self.video_paths):
                if not os.path.exists(video_path):
                    print(f"Error: Video file not found at {video_path}")
                    return False
                print(f"Video {i + 1} found: {video_path}")
        else:  # dual
            for i, video_set in enumerate(self.video_paths):
                if not os.path.exists(video_set['left']):
                    print(f"Error: Left video file not found at {video_set['left']}")
                    return False
                if not os.path.exists(video_set['right']):
                    print(f"Error: Right video file not found at {video_set['right']}")
                    return False
                print(f"Video set {i + 1} found: left={video_set['left']}, right={video_set['right']}")
        return True
    
    def _start_vlc_instances(self):
        """Start VLC instances based on mode"""
        try:
            # Check if VLC is available
            try:
                vlc.Instance()
                print("VLC is available")
            except Exception as e:
                print(f"VLC is not available or not installed: {e}")
                return False
            
            if self.mode == "single":
                return self._start_single_vlc_instance()
            else:  # dual
                return self._start_dual_vlc_instances()
                
        except Exception as e:
            print(f"Error starting VLC instances: {e}")
            return False
    
    def _start_single_vlc_instance(self):
        """Start VLC instance for single screen"""
        try:
            # Create VLC instance with appropriate options
            self.vlc_instance = vlc.Instance([
                '--intf', 'dummy',  # No interface
                '--fullscreen',     # Start in fullscreen
                '--no-video-title-show',  # Don't show video title
                '--no-osd',         # No on-screen display
                '--video-on-top',   # Ensure video stays on top
                '--no-video-deco',  # No window decorations
                '--no-embedded-video',  # Don't embed video in interface
                '--no-qt-privacy-ask',  # Don't ask for privacy settings
                '--aout', 'alsa',   # Use ALSA audio output (common on Raspberry Pi)
                '--quiet'           # Reduce console output
            ])
            
            # Create media player
            self.vlc_player = self.vlc_instance.media_player_new()
            
            # Explicitly set fullscreen mode
            self.vlc_player.set_fullscreen(True)

            # Set volume to 100% (VLC volume range is 0-100)
            self.vlc_player.audio_set_volume(100)
            print("Single screen VLC instance created with audio enabled")
            return True
            
        except Exception as e:
            print(f"Error starting single VLC instance: {e}")
            return False
    
    def _start_dual_vlc_instances(self):
        """Start VLC instances for dual screens"""
        try:
            # Create VLC instance for left screen
            self.vlc_instance_left = vlc.Instance([
                '--intf', 'dummy',  # No interface
                '--no-video-title-show',  # Don't show video title
                '--no-osd',         # No on-screen display
                '--video-on-top',   # Ensure video stays on top
                '--no-video-deco',  # No window decorations
                '--no-embedded-video',  # Don't embed video in interface
                '--no-qt-privacy-ask',  # Don't ask for privacy settings
                '--aout', 'alsa',   # Use ALSA audio output (common on Raspberry Pi)
                '--quiet'           # Reduce console output
            ])
            
            # Create VLC instance for right screen
            self.vlc_instance_right = vlc.Instance([
                '--intf', 'dummy',  # No interface
                '--no-video-title-show',  # Don't show video title
                '--no-osd',         # No on-screen display
                '--video-on-top',   # Ensure video stays on top
                '--no-video-deco',  # No window decorations
                '--no-embedded-video',  # Don't embed video in interface
                '--no-qt-privacy-ask',  # Don't ask for privacy settings
                '--aout', 'alsa',   # Use ALSA audio output (common on Raspberry Pi)
                '--quiet'           # Reduce console output
            ])
            
            # Create media players
            self.vlc_player_left = self.vlc_instance_left.media_player_new()
            self.vlc_player_right = self.vlc_instance_right.media_player_new()
            
            # Set volume to 100% for left player (audio), mute right player to avoid duplicate audio
            self.vlc_player_left.audio_set_volume(100)
            self.vlc_player_right.audio_set_volume(0)  # Mute right player
            print("Dual screen VLC instances created: Left with audio, Right muted")
            
            # Position windows and set fullscreen for dual mode
            self._position_and_fullscreen_videos()
            
            return True
            
        except Exception as e:
            print(f"Error starting dual VLC instances: {e}")
            return False
    
    def _position_and_fullscreen_videos(self):
        """Position video windows on correct displays and set fullscreen (dual mode only)"""
        if self.mode == "single":
            return True
            
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
                raise Exception(f"Failed to position VLC windows on dual screens. xdotool error: {e}")
                    
        except Exception as e:
            print(f"Error in positioning videos: {e}")
            raise Exception(f"Critical error in video positioning: {e}")
    
    def show_first_frame(self):
        """Show the first frame of current video(s) and pause"""
        if not self.initialized:
            return False
            
        if self.mode == "single":
            return self._show_first_frame_single()
        else:  # dual
            return self._show_first_frame_dual()
    
    def _show_first_frame_single(self):
        """Show first frame for single video mode"""
        current_video = self.video_paths[self.current_index]
        print(f"Showing first frame of video {self.current_index + 1}")
        
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
            
            print(f"First frame displayed for video {self.current_index + 1}")
            return True
            
        except Exception as e:
            print(f"Error showing first frame: {e}")
            return False
    
    def _show_first_frame_dual(self):
        """Show first frame for dual video mode"""
        current_set = self.video_paths[self.current_index]
        print(f"Showing first frame of video set {self.current_index + 1}")
        
        try:
            # Create media for current video set
            media_left = self.vlc_instance_left.media_new(current_set['left'])
            media_right = self.vlc_instance_right.media_new(current_set['right'])
            
            self.vlc_player_left.set_media(media_left)
            self.vlc_player_right.set_media(media_right)
            
            # Start playing to load the first frame
            self.vlc_player_left.play()
            self.vlc_player_right.play()
            
            # Wait a moment for the videos to start
            time.sleep(0.5)
            
            # Pause to show only the first frame
            self.vlc_player_left.pause()
            self.vlc_player_right.pause()
            
            print(f"First frames displayed for video set {self.current_index + 1}")
            return True
            
        except Exception as e:
            print(f"Error showing first frame: {e}")
            return False
    
    def play_video(self):
        """Play the current video(s) from start to finish"""
        if self.is_playing:
            return
            
        if not self.initialized:
            return
            
        if self.mode == "single":
            self._play_video_single()
        else:  # dual
            self._play_video_dual()
    
    def _play_video_single(self):
        """Play video for single mode"""
        current_video = self.video_paths[self.current_index]
        print(f"Playing video {self.current_index + 1}: {current_video}")
        
        self.is_playing = True
        
        try:
            # Create media for current video
            media = self.vlc_instance.media_new(current_video)
            self.vlc_player.set_media(media)
            
            # Start playing
            self.vlc_player.play()
            
            # Wait for video to finish playing
            self._wait_for_video_end_single()
            
            print(f"Video {self.current_index + 1} finished playing")
            
        except Exception as e:
            print(f"Error playing video: {e}")
        finally:
            self.is_playing = False
            # Move to next video
            self._rotate_to_next()
    
    def _play_video_dual(self):
        """Play videos for dual mode"""
        current_set = self.video_paths[self.current_index]
        print(f"Playing video set {self.current_index + 1}: left={current_set['left']}, right={current_set['right']}")
        
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
            
            # Wait for videos to finish playing
            self._wait_for_videos_end_dual()
            
            print(f"Video set {self.current_index + 1} finished playing")
            
        except Exception as e:
            print(f"Error playing videos: {e}")
        finally:
            self.is_playing = False
            # Move to next video set
            self._rotate_to_next()
    
    def _wait_for_video_end_single(self):
        """Wait for single video to finish playing"""
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
    
    def _wait_for_videos_end_dual(self):
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
    
    def _rotate_to_next(self):
        """Move to the next video/video set in the sequence"""
        self.current_index = (self.current_index + 1) % len(self.video_paths)
        if self.mode == "single":
            print(f"Rotated to video {self.current_index + 1}")
        else:
            print(f"Rotated to video set {self.current_index + 1}")
    
    def cleanup(self):
        """Clean up resources"""
        self.is_playing = False
        
        if self.mode == "single":
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
        else:  # dual
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

def detect_motion_filtered():
    """Enhanced motion detection with filtering and debouncing"""
    global motion_sensor, motion_confirmation_counter, last_motion_time
    
    if motion_sensor is None:
        return False
    
    current_time = time.time()
    
    # Check raw motion sensor
    raw_motion = motion_sensor.motion_detected
    
    # Debounce: ignore rapid successive triggers
    if current_time - last_motion_time < MOTION_DEBOUNCE_TIME:
        return False
    
    if raw_motion:
        motion_confirmation_counter += 1
        print(f"Motion detected ({motion_confirmation_counter}/{MOTION_CONFIRMATION_COUNT})")
        
        # Require multiple consecutive positive readings
        if motion_confirmation_counter >= MOTION_CONFIRMATION_COUNT:
            last_motion_time = current_time
            motion_confirmation_counter = 0
            return True
    else:
        # Reset counter if no motion detected
        motion_confirmation_counter = 0
    
    return False

def detect_motion():
    """Detect motion using PIR sensor with gpiozero"""
    # Use the filtered version for better reliability
    return detect_motion_filtered()

def print_usage():
    """Print usage information"""
    print("Usage: python3 rpi_video_screen.py [mode]")
    print("  mode: 'single' or 'dual' (default: 'single')")
    print("")
    print("Examples:")
    print("  python3 rpi_video_screen.py single")
    print("  python3 rpi_video_screen.py dual")

def main():
    """Main function"""
    global shutdown_requested, motion_sensor
    
    # Parse command line arguments
    mode = "single"  # default mode
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode not in ["single", "dual"]:
            print(f"Error: Invalid mode '{mode}'. Must be 'single' or 'dual'")
            print_usage()
            return
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        print(f"Initializing Unified Halloween Video Player in {mode} mode...")
        print(f"Python version: {subprocess.run(['python3', '--version'], capture_output=True, text=True).stdout.strip()}")
        
        # Initialize PIR motion sensor with configurable parameters
        try:
            motion_sensor = MotionSensor(
                pin=PIR_PIN,
                threshold=MOTION_THRESHOLD,      # Sensitivity: 0.0 (most sensitive) to 1.0 (least sensitive)
                sample_rate=MOTION_SAMPLE_RATE,  # How often to check (samples per second)
                queue_len=MOTION_QUEUE_LEN       # Number of samples to average over
            )
            if PIR_AVAILABLE:
                print(f"PIR motion sensor initialized on GPIO pin {PIR_PIN}")
                print(f"  Threshold: {MOTION_THRESHOLD} (0.0=most sensitive, 1.0=least sensitive)")
                print(f"  Sample rate: {MOTION_SAMPLE_RATE} samples/second")
                print(f"  Queue length: {MOTION_QUEUE_LEN} samples")
                print(f"  Debounce time: {MOTION_DEBOUNCE_TIME}s")
                print(f"  Confirmation count: {MOTION_CONFIRMATION_COUNT}")
                print(f"  Extended cooldown: {EXTENDED_COOLDOWN}s")
            else:
                print(f"Using dummy motion sensor (gpiozero not available)")
        except Exception as e:
            print(f"Warning: Failed to initialize motion sensor: {e}")
            print("Motion detection will be disabled")
            motion_sensor = None
        
        # Check if VLC is available
        try:
            vlc.Instance()
            print("VLC library is available")
        except Exception as e:
            print(f"Error: VLC not available. Please install VLC and python-vlc.")
            print(f"Install with: pip install python-vlc")
            return
        
        # Configure display resolution and orientation based on mode
        configure_display(mode)
        
        # Initialize video player
        print(f"Creating video player instance in {mode} mode...")
        player = UnifiedVideoPlayer(mode)
        if not player.initialized:
            print("Video player failed to initialize. Exiting.")
            return
        
        print("Video player initialized successfully")
        
        # Show first frame initially
        print("Attempting to show initial first frame(s)...")
        for attempt in range(3):  # Try up to 3 times
            print(f"First frame attempt {attempt + 1}...")
            if player.show_first_frame():
                print("Initial first frame(s) displayed successfully")
                break
            else:
                print(f"Attempt {attempt + 1} failed, retrying...")
                time.sleep(2)
        else:
            print("Warning: Failed to show initial first frame(s) after 3 attempts")
            # Continue anyway - maybe the video will display when motion is detected
            
        print("Showing first frame(s). Waiting for motion detection...")
        if mode == "single":
            print(f"Starting with video {player.current_index + 1} of {len(player.video_paths)}")
        else:
            print(f"Starting with video set {player.current_index + 1} of {len(player.video_paths)}")
        
        last_trigger_time = 0
        cooldown_period = 3  # Base seconds to wait before allowing another trigger
        last_debug_time = 0  # Track debug output timing
        
        while not shutdown_requested:
            try:
                # Check for motion with enhanced filtering
                motion_detected = detect_motion()
                current_time = time.time()
                
                # Use extended cooldown period for more reliable operation
                effective_cooldown = cooldown_period + EXTENDED_COOLDOWN
                
                # Check if motion detected and cooldown period has passed
                if (motion_detected and 
                    not player.is_playing and 
                    current_time - last_trigger_time > effective_cooldown):
                    
                    if mode == "single":
                        print("Motion detected - Playing video!")
                    else:
                        print("Motion detected - Playing dual videos!")
                    last_trigger_time = current_time

                    # Play the video(s) (this will block until video(s) finish)
                    player.play_video()
                    
                    # After video(s) finish, show the first frame of the next video/set
                    if mode == "single":
                        print(f"Video finished. Now showing video {player.current_index + 1}")
                    else:
                        print(f"Videos finished. Now showing video set {player.current_index + 1}")
                    
                    if not player.show_first_frame():
                        print("Warning: Failed to show first frame(s) after video playback")
                    else:
                        print("Ready for next motion detection...")
                
                # Debug output every 10 seconds to show status
                if current_time - last_debug_time >= 10:
                    if mode == "single":
                        print(f"Status: Motion={motion_detected}, Playing={player.is_playing}, Video={player.current_index + 1}")
                    else:
                        print(f"Status: Motion={motion_detected}, Playing={player.is_playing}, Video_set={player.current_index + 1}")
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
        if motion_sensor is not None:
            try:
                motion_sensor.close()
                print("Motion sensor cleaned up")
            except Exception as e:
                print(f"Error cleaning up motion sensor: {e}")
        print("Cleanup complete")

if __name__ == "__main__":
    main()
# Unified Halloween Video Player for Raspberry Pi
# Supports both single screen and dual screen modes
# Rotates through videos, shows first frame when idle, plays on motion detection

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
import sys

# Global flag for graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global shutdown_requested
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    shutdown_requested = True

def configure_display_single():
    """Configure display resolution for single portrait mode video"""
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

def configure_display_dual():
    """Configure dual display resolution for portrait mode videos on dual screens"""
    try:
        # Configure first screen (HDMI-1) for left video - 720x1280 portrait
        subprocess.run(['xrandr', '--output', 'HDMI-1', '--mode', '720x1280'], check=True)
        print("Left display (HDMI-1) resolution set to 720x1280 (portrait)")
        
        # Configure second screen (HDMI-2) for right video - 720x1280 portrait
        # Position it to the right of the first screen
        subprocess.run(['xrandr', '--output', 'HDMI-2', '--mode', '720x1280', '--right-of', 'HDMI-1'], check=True)
        print("Right display (HDMI-2) resolution set to 720x1280 (portrait) and positioned to the right")
        
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not configure dual displays: {e}")
        print("Attempting fallback configuration...")
        try:
            # Fallback: try to configure displays separately
            subprocess.run(['xrandr', '--output', 'HDMI-1', '--mode', '720x1280'], check=True)
            subprocess.run(['xrandr', '--output', 'HDMI-2', '--mode', '720x1280'], check=True)
            print("Fallback display configuration applied")
        except subprocess.CalledProcessError as e2:
            print(f"Warning: Fallback display configuration failed: {e2}")
    except Exception as e:
        print(f"Warning: Unexpected error configuring displays: {e}")

# GPIO setup
PIR_PIN = 14  # GPIO pin for PIR motion sensor
GPIO.setmode(GPIO.BCM)
GPIO.setup(PIR_PIN, GPIO.IN)

# Video configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Single video paths
SINGLE_VIDEO_PATHS = [
    os.path.join(SCRIPT_DIR, "../../assets/videos/single_video_1_720x1280p.mp4"),
    os.path.join(SCRIPT_DIR, "../../assets/videos/single_video_2_720x1280p.mp4"),
    os.path.join(SCRIPT_DIR, "../../assets/videos/single_video_3_720x1280p.mp4")
]

# Dual video sets
DUAL_VIDEO_SETS = [
    {
        'left': os.path.join(SCRIPT_DIR, "../../assets/videos/dual_video_1_left_720x1280p.mp4"),
        'right': os.path.join(SCRIPT_DIR, "../../assets/videos/dual_video_1_right_720x1280p.mp4")
    },
    {
        'left': os.path.join(SCRIPT_DIR, "../../assets/videos/dual_video_2_left_720x1280p.mp4"),
        'right': os.path.join(SCRIPT_DIR, "../../assets/videos/dual_video_2_right_720x1280p.mp4")
    },
    {
        'left': os.path.join(SCRIPT_DIR, "../../assets/videos/dual_video_3_left_720x1280p.mp4"),
        'right': os.path.join(SCRIPT_DIR, "../../assets/videos/dual_video_3_right_720x1280p.mp4")
    }
]

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
            
            # Position windows and set fullscreen
            self._position_and_fullscreen_videos()
            
            # Wait a moment for the videos to start and positioning to take effect
            time.sleep(1.0)
            
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
            
            # Position windows and set fullscreen for playback
            self._position_and_fullscreen_videos()
            
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

def detect_motion():
    """Detect motion using PIR sensor"""
    return GPIO.input(PIR_PIN)

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
    global shutdown_requested
    
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
        
        # Check if VLC is available
        try:
            vlc.Instance()
            print("VLC library is available")
        except Exception as e:
            print(f"Error: VLC not available. Please install VLC and python-vlc.")
            print(f"Install with: pip install python-vlc")
            return
        
        # Configure display resolution and orientation based on mode
        if mode == "single":
            configure_display_single()
        else:  # dual
            configure_display_dual()
        
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
        GPIO.cleanup()
        print("Cleanup complete")

if __name__ == "__main__":
    main()
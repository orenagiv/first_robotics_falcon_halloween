# Display configuration utilities for Raspberry Pi
# Handles automatic display detection, resolution setting, and orientation configuration

import os
import subprocess
import re


def configure_single_display():
    """Configure single display resolution for portrait mode videos"""
    try:
        # Set the DISPLAY environment variable
        os.environ['DISPLAY'] = ':0'
        
        # Get available displays and modes
        result = subprocess.run(['xrandr'], capture_output=True, text=True, check=True)
        xrandr_output = result.stdout
        print("Available displays and modes:")
        print(xrandr_output)
        
        # Find connected displays
        displays = re.findall(r'(\S+) connected', xrandr_output)
        print(f"Found connected displays: {displays}")
        
        if not displays:
            print("No connected displays found")
            return False
        
        # Try different resolution and rotation combinations
        configs_to_try = [
            {'mode': '1280x720', 'rotate': 'left'},
            {'mode': '848x480', 'rotate': 'left'},
        ]
        
        for display in displays:
            for config in configs_to_try:
                try:
                    cmd = ['xrandr', '--output', display, '--mode', config['mode']]
                    if config['rotate']:
                        cmd.extend(['--rotate', config['rotate']])
                    
                    subprocess.run(cmd, check=True)
                    print(f"Successfully set {display} to {config['mode']} rotated {config['rotate']}")
                    return True  # Success, exit
                    
                except subprocess.CalledProcessError:
                    print(f"Failed to set {display} to {config['mode']} rotated {config['rotate']}")
                    continue
        
        print("Warning: Could not configure any display for portrait mode")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not run xrandr: {e}")
        return False
    except Exception as e:
        print(f"Warning: Unexpected error configuring display: {e}")
        return False


def configure_dual_display():
    """Configure dual display resolution for portrait mode videos on dual screens"""
    try:
        # Set the DISPLAY environment variable
        os.environ['DISPLAY'] = ':0'
        
        # Get available displays and modes
        result = subprocess.run(['xrandr'], capture_output=True, text=True, check=True)
        xrandr_output = result.stdout
        print("Available displays and modes:")
        print(xrandr_output)
        
        # Find connected displays
        displays = re.findall(r'(\S+) connected', xrandr_output)
        print(f"Found connected displays: {displays}")
        
        if len(displays) < 2:
            print(f"Warning: Found only {len(displays)} display(s), dual screen requires 2")
            if len(displays) == 1:
                print("Configuring single display in portrait mode...")
                return configure_single_display()
            print("No displays found")
            return False
        
        # Try different resolution and rotation combinations for dual displays
        configs_to_try = [
            {'mode': '1280x720', 'rotate': 'left'},
            {'mode': '1920x1080', 'rotate': 'left'},
            {'mode': '1680x1050', 'rotate': 'left'},
            {'mode': '1024x768', 'rotate': 'left'},
        ]
        
        # Configure first display
        display1 = displays[0]
        display2 = displays[1]
        
        for config in configs_to_try:
            try:
                # Configure first screen (left) for left video - portrait mode
                subprocess.run(['xrandr', '--output', display1, '--mode', config['mode'], '--rotate', config['rotate']], check=True)
                print(f"Left display ({display1}) set to {config['mode']} rotated {config['rotate']}")
                
                # Configure second screen (right) for right video - portrait mode, positioned to the right
                subprocess.run(['xrandr', '--output', display2, '--mode', config['mode'], '--rotate', config['rotate'], '--right-of', display1], check=True)
                print(f"Right display ({display2}) set to {config['mode']} rotated {config['rotate']} and positioned to the right")
                
                return True  # Success, exit
                
            except subprocess.CalledProcessError as e:
                print(f"Failed to configure dual displays with {config['mode']}: {e}")
                continue
        
        print("Warning: Could not configure dual displays with any supported mode")
        print("Attempting fallback configuration...")
        try:
            # Fallback: try individual configuration without positioning
            subprocess.run(['xrandr', '--output', display1, '--mode', '1280x720', '--rotate', 'left'], check=False)
            subprocess.run(['xrandr', '--output', display2, '--mode', '1280x720', '--rotate', 'left'], check=False)
            print("Fallback dual display configuration attempted")
            return True
        except Exception as e2:
            print(f"Fallback configuration also failed: {e2}")
            return False
        
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not run xrandr: {e}")
        return False
    except Exception as e:
        print(f"Warning: Unexpected error configuring displays: {e}")
        return False


def get_display_info():
    """Get information about available displays and their modes"""
    try:
        # Set the DISPLAY environment variable
        os.environ['DISPLAY'] = ':0'
        
        # Get available displays and modes
        result = subprocess.run(['xrandr'], capture_output=True, text=True, check=True)
        xrandr_output = result.stdout
        
        # Find connected displays
        displays = re.findall(r'(\S+) connected', xrandr_output)
        
        return {
            'displays': displays,
            'xrandr_output': xrandr_output,
            'display_count': len(displays)
        }
        
    except subprocess.CalledProcessError as e:
        print(f"Warning: Could not run xrandr: {e}")
        return {
            'displays': [],
            'xrandr_output': '',
            'display_count': 0
        }
    except Exception as e:
        print(f"Warning: Unexpected error getting display info: {e}")
        return {
            'displays': [],
            'xrandr_output': '',
            'display_count': 0
        }


# Convenience function that automatically chooses single or dual display configuration
def configure_display(mode='auto'):
    """
    Configure display(s) for portrait mode videos
    
    Args:
        mode (str): 'auto', 'single', or 'dual'
                   'auto' will detect and configure based on available displays
    
    Returns:
        bool: True if configuration was successful, False otherwise
    """
    display_info = get_display_info()
    display_count = display_info['display_count']
    
    print(f"Display configuration mode: {mode}")
    print(f"Detected {display_count} display(s)")
    
    if mode == 'auto':
        if display_count >= 2:
            print("Auto mode: Configuring dual displays")
            return configure_dual_display()
        elif display_count == 1:
            print("Auto mode: Configuring single display")
            return configure_single_display()
        else:
            print("Auto mode: No displays found")
            return False
    elif mode == 'single':
        print("Single mode: Configuring single display")
        return configure_single_display()
    elif mode == 'dual':
        print("Dual mode: Configuring dual displays")
        return configure_dual_display()
    else:
        print(f"Unknown mode: {mode}. Use 'auto', 'single', or 'dual'")
        return False
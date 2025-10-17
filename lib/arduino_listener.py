import serial
import time
import pyautogui

# Replace this with the port your Arduino is on!
ARDUINO_PORT = '/dev/cu.usbserial-210'
BAUD_RATE = 9600

print("Connecting to Arduino...")

try:
    # Set up the serial connection
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    # A short delay to allow the connection to establish
    time.sleep(2) 
    print("Connected! Listening for commands...")

    # Infinite loop to keep listening
    while True:
        # Read a line from the serial port
        line = ser.readline()
        
        # If a line was received
        if line:
            # Decode bytes to a string and remove whitespace
            message = line.decode('utf-8').strip()
            
            # Print all messages to console for debugging
            print(f"Arduino: {message}")
            
            # Check if we got our "PLAY" command
            if message == "PLAY":
                print("Detected 'PLAY' command -> Triggering click")
                # pyautogui.press('space')
                pyautogui.click(x=200, y=200) # Click at specific coordinates

except serial.SerialException as e:
    print(f"Error: Could not open port {ARDUINO_PORT}. {e}")
except FileNotFoundError:
    print(f"Error: Port {ARDUINO_PORT} not found. Is the Arduino connected?")
except KeyboardInterrupt:
    print("\nStopping Arduino listener...")
    if 'ser' in locals():
        ser.close()
except Exception as e:
    print(f"Unexpected error: {e}")
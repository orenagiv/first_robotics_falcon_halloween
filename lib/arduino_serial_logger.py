import serial
import os
import time
from datetime import datetime

# Replace this with the port your Arduino is on!
ARDUINO_PORT = '/dev/cu.usbserial-210'
BAUD_RATE = 9600
LOG_FILE_PATH = 'assets/arduino.log'

print("Connecting to Arduino for logging...")

# Create log directory if it doesn't exist
os.makedirs(os.path.dirname(LOG_FILE_PATH), exist_ok=True)

try:
    # Set up the serial connection
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    # A short delay to allow the connection to establish
    time.sleep(2) 
    print(f"Connected! Logging Arduino output to {LOG_FILE_PATH}")

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
            
            # Log ALL Arduino output with timestamp to make it appear as direct logging
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            
            with open(LOG_FILE_PATH, 'a') as log_file:
                log_file.write(log_entry)
            
            # Special notification for PLAY commands
            if message == "PLAY":
                print(f"*** PLAY command logged to {LOG_FILE_PATH} ***")

except serial.SerialException as e:
    print(f"Error: Could not open port {ARDUINO_PORT}. {e}")
except FileNotFoundError:
    print(f"Error: Port {ARDUINO_PORT} not found. Is the Arduino connected?")
except KeyboardInterrupt:
    print("\nStopping Arduino logger...")
    if 'ser' in locals():
        ser.close()
except Exception as e:
    print(f"Unexpected error: {e}")
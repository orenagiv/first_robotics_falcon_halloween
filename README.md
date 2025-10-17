# HALLOWEEN FRAME

## OVERVIEW
This is an Arduino project that uses Ultrasonic sensor to detect a user getting close to a frame and trigger a spooky video to play on a connected monitor.

The system works in two parts:

1. **Arduino Sketch** (`lib/arduino_detect_distance.cpp`): Uses an ultrasonic sensor to measure distance. When an object comes within 30cm, it sends "PLAY" via Serial.

2. **Trigger Listener** (`lib/arduino_listener.py`): Listens directly to the Arduino's Serial output. When it detects a "PLAY" command, it triggers a spacebar key press.

The `assets/index.html` file contains a simple HTML page that plays a spooky video when the spacebar is pressed.

## SETUP
### Install Python Libraries
1. Open the Terminal app on your Mac (you can find it in Applications > Utilities or search for it with Spotlight).
2. Install the libraries by running these two commands, pressing Enter after each one:
```bash
pip3 install pyserial
pip3 install pyautogui
```

### Find Your Arduino's Port
1. Connect your Arduino Uno to your Mac.
2. Open the Arduino IDE.
3. Go to the Tools > Port menu. You'll see something like /dev/cu.usbserial-210. Copy this port name exactly.

### Update the Arduino Listener Script
1. Update the `ARDUINO_PORT` in `lib/arduino_listener.py` with your Arduino's port name.

### Arduino <-> Ultrasonic Sensor Wiring
1. Setup the circuit per the docs/ultrasonic_circuit_tutorial.pdf (page 148).

### Running the System
1. Upload the `arduino_detect_distance.ino` sketch to your Arduino.
2. From the terminal, start the listener:
```bash
python3 lib/arduino_listener.py
```
3. Open `assets/index.html` in a web browser for the video display.

## MISC.
Trigger Spacebar on Mac command line:
```
osascript -e 'tell application "System Events" to key code 49'
```

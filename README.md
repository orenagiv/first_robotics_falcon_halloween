# HALLOWEEN FRAME

## OVERVIEW
The Halloween Frame is an interactive spooky display that plays a scary video when someone approaches it.  
The project has two versions: a prototype using an Arduino and a more advanced version planned for Raspberry Pi.

### TRACKER
#### Arduino Prototype
🎯 Quick & Dirty Arduino sketch to detect the distance of approaching users using Ultrasonic sensor.  
🎯 HTML file with a preview video (which plays upon click event).  
🎯 A Python script which listens to the Arduino's Serial output and triggers a click-event (which plays the video playback).  

#### Raspberry Pi Version
🎯 Setup Github Repo and VSCode Raspberry Pi remote-host (SSH) environment.  
🎯 Prepare HD videos for both dual-screens and single-screen.  
🚧 Implement the Python scripts for Raspberry Pi version.  
🚧 Integrate a camera to take a picture at the "scary" moment.  
🤌 Test.  
🤌 Packaging & Scenery.  
💅 Polish & Fingernails.  


## PROTOTYPE VERSION
The initial (quick and dirty) prototype is an Arduino project that uses an Ultrasonic sensor to detect a user getting close to a frame and trigger a spooky video to play on a connected monitor.

The system works in two parts:

1. **Arduino Sketch** (`lib/arduino_detect_distance.cpp`): Uses an ultrasonic sensor to measure distance. When an object comes within 30cm, it sends "PLAY" via Serial.

2. **Trigger Listener** (`lib/arduino_listener.py`): Listens directly to the Arduino's Serial output. When it detects a "PLAY" command, it triggers a spacebar key press.

The `assets/index.html` file contains a simple HTML page that plays a spooky video when the spacebar is pressed.

### SETUP
#### Install Python Libraries
1. Open the Terminal app on your Mac (you can find it in Applications > Utilities or search for it with Spotlight).
2. Install the libraries by running these two commands, pressing Enter after each one:
```bash
pip3 install pyserial
pip3 install pyautogui
```

#### Find Your Arduino's Port
1. Connect your Arduino Uno to your Mac.
2. Open the Arduino IDE.
3. Go to the Tools > Port menu. You'll see something like /dev/cu.usbserial-210. Copy this port name exactly.

#### Update the Arduino Listener Script
1. Update the `ARDUINO_PORT` in `lib/arduino_listener.py` with your Arduino's port name.

#### Arduino <-> Ultrasonic Sensor Wiring
1. Setup the circuit per the docs/ultrasonic_circuit_tutorial.pdf (page 148).

#### Running the System
1. Upload the `arduino_detect_distance.ino` sketch to your Arduino.
2. From the terminal, start the listener:
```bash
python3 lib/arduino_listener.py
```
3. Open `assets/index.html` in a web browser for the video display.

### MISC.
Trigger Spacebar on Mac command line:
```
osascript -e 'tell application "System Events" to key code 49'
```

## RASPBERRY PI VERSION
### Enable VNC on Raspberry Pi
- Connect to your Raspberry Pi with a physical keyboard, mouse and monitor.
- Open a terminal on the Raspberry Pi.
- Enable VNC on Raspberry Pi:
```
sudo raspi-config
```
Or via terminal:
```
sudo apt install realvnc-vnc-server
sudo systemctl enable vncserver-x11-serviced.service
sudo systemctl start vncserver-x11-serviced.service
```
- Install VNC Viewer on your Mac from: https://www.realvnc.com/en/connect/download/viewer/

### Remote SSH Setup
- Connect to your Raspberry Pi with a physical keyboard, mouse and monitor.
- Open a terminal on the Raspberry Pi.
- Check the username on your Raspberry Pi (default is "pi"):
```
whoami
```
- Enable SSH on Raspberry Pi:
```
sudo systemctl enable ssh
sudo systemctl start ssh
```
Or:
```
sudo raspi-config
```
- Find Raspberry Pi IP address:
```
hostname -I
```
Or simply use `raspberrypi.local` if your network supports mDNS.
- On your Mac (or Windows via Git Bash terminal), create SSH keys:
```
ssh-keygen -t rsa -b 4096 -f ~/.ssh/raspberry_pi.key
```
- Copy the public key to Raspberry Pi:
```
ssh-copy-id -i ~/.ssh/raspberry_pi.key.pub pi@raspberrypi.local
```
(You'll be prompted to enter the Raspberry Pi password, default is "raspberry".)
- Test the SSH connection using:
```
ssh -i ~/.ssh/raspberry_pi.key pi@raspberrypi.local
```
- Install the "Remote - SSH" extension in VSCode.
- In VSCode, press `F1`, type `Remote-SSH: Connect to Host...`, and enter:
```
ssh -i ~/.ssh/raspberry_pi.key pi@raspberrypi.local
```
- A new VSCode window will open connected to your Raspberry Pi.

### Copying files to Raspberry Pi
- Use `scp` to copy files from your Mac to Raspberry Pi:
```
scp -i ~/.ssh/raspberry_pi.key -r /path/to/local/folder pi@raspberrypi.local:/path/to/remote/folder
```

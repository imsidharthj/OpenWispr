# VoxType: Global Voice Dictation for Linux
VoxType is a voice-to-text dictation tool that allows you to type in any application on your Linux desktop simply by speaking. Hold down a hotkey, say what you want to type, and release. The text will appear wherever your cursor is.

This tool is designed to work on modern Linux distributions using the Wayland display server (such as recent versions of Ubuntu) but is also compatible with X11.

It is **platform-independent** for applications: all typing is simulated at the shell/input level, so it works with any app that accepts keyboard input.



# Setup Instructions
Follow these steps carefully to set up the tool and its dependencies.

## Step 1: Clone This Repository
First, get the project files onto your local machine.

- git clone <https://github.com/imsidharthj/VoxType.git>
- cd <VotType>

## Step 2: Install System Build Dependencies
We need some essential tools to build ydotool (our virtual keyboard) from source.

sudo apt update
sudo apt install git cmake scdoc build-essential

## Step 3: Build and Install ydotool
ydotool is the core utility that simulates keyboard presses. We will build it from its official source for maximum compatibility.

### Clone the ydotool repository
git clone https://github.com/ReimuNotMoe/ydotool.git
cd ydotool

### Create a build directory and compile the tool
mkdir build
cd build
cmake ..
make -j "$(nproc)"

### Install the compiled tool to your system
sudo make install

### Return to the project directory
cd ../..

## Step 4: Set Up the ydotool Service
ydotool requires a background service (daemon) to be running.

### Reload the systemd manager configuration
systemctl --user daemon-reload

### Start the ydotool service
systemctl --user start ydotoold.service

### (Optional) Check the status to ensure it's running
systemctl --user status ydotoold.service

Expected Output:
You should see Active: active (running). If it says inactive or failed, a system reboot after the next step often resolves the issue.

● ydotoold.service - Starts ydotoold Daemon
     Loaded: loaded (/usr/lib/systemd/user/ydotoold.service; static)
     Active: active (running) since Thu 2025-08-07 11:30:00 IST; 5s ago
   Main PID: 12345 (ydotoold)

## Step 5: Configure Critical Permissions (Very Important!)
For the tool to listen to your keyboard and simulate typing, your user account must be part of the input group.

### Add your current user to the 'input' group
### The $USER variable automatically uses your username
sudo usermod -aG input $USER

<br>

🛑 CRITICAL STEP: You MUST log out and log back in, or reboot your computer for this permission change to take effect. If you skip this, the tool will fail with a "Permission Denied" error.

<br>

## Step 6: Install Python Dependencies
This project requires several Python libraries. We will install them using a requirements.txt file.

Create a file named requirements.txt in the project directory.

Copy and paste the following content into that file:

### For audio recording and processing
sounddevice
numpy

### For hotkey detection on Wayland/X11
evdev

### For AI-based speech-to-text
torch
transformers

### For simulating keyboard input (primary method)
pydotool

Now, install all of them with a single command:

pip install -r requirements.txt



# ▶️ How to Use
Once all setup steps are complete, you can run the dictation service.

Start the Service:
Open a terminal in the project directory and run:

python3 whisper.py

You will see a confirmation that the service is running and listening for the hotkey.



# 📝 Workflow Guide

1. **Focus the cursor** in any input box (web browser, text editor, chat app, etc.).
2. **Press and hold** the `Ctrl` + `Alt` keys.
3. **Speak** clearly into your microphone.
4. **Release the keys** when done.
5. The tool will automatically transcribe your speech and **type the text into the input box** at your cursor's location.



# Dictate Anywhere:

Click on any input box in any application (web browser, text editor, etc.).

Press and hold the Left Ctrl + Left Alt keys.

You will see a "🔴 Recording..." message in your terminal.

Speak clearly.

Release the keys.

The terminal will show "⏹️ Processing..." and then the transcribed text will be typed out at your cursor's location.

Stop the Service:
To stop the tool, go back to the terminal where it is running and press Ctrl + C.


# 🎥 Demo Video

See a demonstration of SpeakWrite in action:  
[Loom Video Demo](https://www.loom.com/share/0c7021bebd934c9ea557f4876119940b?sid=8a5fe730-43ca-45f9-979a-9240b0550498)
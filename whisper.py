import subprocess
import sys
import time
import random
import threading
import logging

try:
    import sounddevice as sd
    import numpy as np
    from transformers import pipeline as hf_pipeline
    import evdev
    from evdev import ecodes
    VOICE_AVAILABLE = True
except ImportError as e:
    VOICE_AVAILABLE = False
    print(f"Voice input not available: {e}")
    print("Install with: pip install sounddevice transformers torch evdev")

if VOICE_AVAILABLE:
    try:
        logging.basicConfig(level=logging.ERROR)
        print("Initializing Whisper-tiny ASR model...")
        asr_pipeline = hf_pipeline(
            "automatic-speech-recognition",
            model="openai/whisper-tiny",
            device=-1
        )
        print("✓ Whisper ASR model loaded successfully")
    except Exception as e:
        print(f"Failed to load Whisper model: {e}")
        VOICE_AVAILABLE = False

recording_active = False
audio_data = []
SAMPLE_RATE = 16000

# ============================================================================
# TYPING FUNCTIONS
# ============================================================================

def init_pydotool():
    """Initialize pydotool connection"""
    try:
        import pydotool
        pydotool.init("/run/user/1000/.ydotool_socket")
        return True
    except Exception:
        return False

def type_with_human_speed(text, use_pydotool=True):
    """Type text with human-like timing"""
    if use_pydotool:
        try:
            import pydotool
            delays = []
            for char in text:
                base_delay = random.randint(50, 150)
                if char in '.,!?;:':
                    base_delay += random.randint(100, 200)
                delays.append(base_delay)
            
            for i, char in enumerate(text):
                pydotool.type_string(char)
                if i < len(text) - 1:
                    time.sleep(delays[i] / 1000.0)
            return True
        except Exception:
            return False
    else:
        try:
            for char in text:
                subprocess.run(['ydotool', 'type', char], check=True, capture_output=True)
                delay = random.randint(50, 150) / 1000.0
                if char in '.,!?;:':
                    delay += random.randint(100, 200) / 1000.0
                time.sleep(delay)
            return True
        except subprocess.CalledProcessError:
            return False

def type_text(text):
    """Main typing function with fallback"""
    if pydotool_available:
        if type_with_human_speed(text, use_pydotool=True):
            return True
    
    if type_with_human_speed(text, use_pydotool=False):
        return True
    
    print("Error: Both pydotool and subprocess typing methods failed")
    return False

# ============================================================================
# VOICE INPUT FUNCTIONS
# ============================================================================

def find_keyboard_device():
    """Finds the first device that looks like a keyboard."""
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    for device in devices:
        if 'keyboard' in device.name.lower() and ecodes.KEY_A in device.capabilities().get(ecodes.EV_KEY, []):
            print(f"✓ Found keyboard: {device.name}")
            return device
    return None

def transcribe_input_to_text():
    """Hybrid voice transcription: hotkey-controlled recording with simple audio processing"""
    if not VOICE_AVAILABLE:
        print("Error: Voice input not available")
        return None
    
    keyboard = find_keyboard_device()
    if not keyboard:
        print("\nError: Could not find a keyboard device. Ensure your user is in the 'input' group (`sudo usermod -aG input $USER`)")
        return None
    
    start_recording_event = threading.Event()
    stop_recording_event = threading.Event()
    exit_event = threading.Event()
    
    global recording_active, audio_data
    recording_active = False
    audio_data = []
    transcribed_text = ""
    
    MODIFIER_KEYS = {ecodes.KEY_LEFTCTRL, ecodes.KEY_RIGHTCTRL}
    TRIGGER_KEYS = {ecodes.KEY_LEFTALT, ecodes.KEY_RIGHTALT}
    
    def hotkey_listener():
        """Listens for Ctrl+Alt hotkey and signals start/stop events"""
        try:
            pressed_keys = set()
            was_recording = False
            
            with keyboard.grab_context():
                for event in keyboard.read_loop():
                    if exit_event.is_set():
                        break
                        
                    if event.type == ecodes.EV_KEY:
                        key_code = event.code
                        is_pressed = event.value in [1, 2]
                        
                        if is_pressed:
                            pressed_keys.add(key_code)
                        elif key_code in pressed_keys:
                            pressed_keys.remove(key_code)
                        
                        is_hotkey_active = any(mod in pressed_keys for mod in MODIFIER_KEYS) and \
                                          any(trig in pressed_keys for trig in TRIGGER_KEYS)
                        
                        if is_hotkey_active and not was_recording:
                            print("\r🔴 Recording... Release Ctrl+Alt to stop.", end='', flush=True)
                            start_recording_event.set()
                            was_recording = True
                        
                        elif not is_hotkey_active and was_recording:
                            print("\r⏹️  Processing...", end='', flush=True)
                            stop_recording_event.set()
                            was_recording = False
                            break
                            
        except OSError as e:
            print(f"\nError reading from keyboard device: {e}")
            exit_event.set()
        except Exception as e:
            print(f"\nAn unexpected error occurred in the hotkey listener: {e}")
            exit_event.set()
    
    def audio_recorder():
        """Simple audio recorder (same logic as first implementation)"""
        global audio_data, recording_active
        try:
            with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
                while recording_active:
                    chunk, _ = stream.read(int(SAMPLE_RATE * 0.5))
                    audio_data.extend(chunk.flatten())
        except Exception as e:
            print(f"\nAudio recording error: {e}")
    
    print("\n🎤 Hold Left/Right Ctrl + Left/Right Alt to start speaking.")
    
    hotkey_thread = threading.Thread(target=hotkey_listener, daemon=True)
    hotkey_thread.start()
    
    try:
        start_recording_event.wait()
        if exit_event.is_set():
            return None
        recording_active = True
        audio_data = []
        rec_thread = threading.Thread(target=audio_recorder)
        rec_thread.start()
        stop_recording_event.wait()
        recording_active = False
        rec_thread.join()
        
    except KeyboardInterrupt:
        print("\nExiting...")
        exit_event.set()
        return None
    finally:
        exit_event.set()
    
    try:
        if len(audio_data) > 0:
            final_audio = np.array(audio_data)
            result = asr_pipeline({"array": final_audio, "sampling_rate": SAMPLE_RATE})
            transcribed_text = result.get("text", "").strip()
    except Exception as e:
        print(f"\nFinal transcription error: {e}")
        return None
    
    if transcribed_text:
        print(f"\r✓ Final transcription: '{transcribed_text}'      ")
    else:
        print(f"\rCould not transcribe audio.                      ")
    
    return transcribed_text if transcribed_text else None

# ============================================================================
# BACKGROUND SERVICE
# ============================================================================

def run_dictation_service():
    """Main background service loop - continuous voice dictation"""
    print("\n🎯 Voice Dictation Service Started")
    
    service_running = True
    
    while service_running:
        try:
            transcribed_text = transcribe_input_to_text()
            if transcribed_text:
                print(f"\n⌨️  Typing: '{transcribed_text[:50]}{'...' if len(transcribed_text) > 50 else ''}'")
                if type_text(transcribed_text):
                    print("✓ Text typed successfully!")
                else:
                    print("✗ Failed to type text")
            else:
                print("\n❌ No text transcribed")
            print("\n🎤 Ready for next voice input...")
        except KeyboardInterrupt:
            print("\n\n🛑 Service stopped by user")
            service_running = False
            break
        except Exception as e:
            print(f"\n❌ Service error: {e}")
            time.sleep(1)

def main():
    """Initialize and start the background dictation service"""
    print("=== Background Voice Dictation Service ===")
    
    if not VOICE_AVAILABLE:
        print("❌ Voice input not available. Cannot start service.")
        sys.exit(1)
    print("✓ Voice input enabled (Ctrl+Alt to record)")
    
    global pydotool_available
    pydotool_available = init_pydotool()
    if pydotool_available:
        print("✓ pydotool initialized successfully")
    else:
        print("⚠ pydotool failed, will use ydotool subprocess fallback")
    
    run_dictation_service()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
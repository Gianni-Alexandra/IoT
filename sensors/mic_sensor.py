import os
from datetime import datetime

# === CONFIGURATION ===
DEVICE = "hw:3,0"               # Use `arecord -l` to confirm this
DURATION = 4                    # Duration of recording in seconds
SAVE_FOLDER = "recordings"      # Folder to store the recordings

# === Create recordings folder if it doesn't exist ===
os.makedirs(SAVE_FOLDER, exist_ok=True)

def get_filename():
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(SAVE_FOLDER, f"recording_{timestamp}.wav")

def record_audio(filename):
    print(f"\Recording {DURATION}s into {filename}...")
    cmd = f"arecord -D {DEVICE} -d {DURATION} -f S16_LE -r 44100 -c 1 -t wav {filename}"
    #cmd = f"arecord -D {DEVICE} -d {DURATION} -f S16_LE -r 44100 -c 1 -t wav {OUTPUT_FILE}"

    result = os.system(cmd)
    if result != 0:
        print("Recording failed..!")
    else:
        print("Recording complete!!")

def play_audio(filename):
    print(f"[🔊] Playing {filename}...")
    cmd = f"aplay {filename}"
    result = os.system(cmd)
    if result != 0:
        print("-Playback failed.")
    else:
        print("-Playback finished.")

if __name__ == "__main__":
    filename = get_filename()
    record_audio(filename)
    play_audio(filename)

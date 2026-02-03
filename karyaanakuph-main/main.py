# ================== MATIKAN LOG VOSK ==================
import os
os.environ["VOSK_LOG_LEVEL"] = "-1"

# ================== IMPORT ==================
import sounddevice as sd
import queue, json, threading
import tkinter as tk
from vosk import Model, KaldiRecognizer
from rapidfuzz import fuzz
import numpy as np

# ================== CONFIG ==================
SAMPLE_RATE = 16000
BLOCK_SIZE = 1024
FUZZY_THRESHOLD = 85
VOLUME_THRESHOLD = 300

TARGET_WORDS = [
    "distance", "afraid", "silent", "overwhelm",
    "honestly", "realize", "sorry", "grateful", "message"
]

MODEL_PATH = r"C:\Users\USER\Downloads\karyaanakuph-main\karyaanakuph-main\vosk-model-small-en-us-0.15"

# ================== MODEL ==================
model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, SAMPLE_RATE)
rec.SetWords(False)

# ================== AUDIO ==================
audio_q = queue.Queue()
speaking = False

def callback(indata, frames, time, status):
    global speaking
    if status:
        print(status)

    volume = np.linalg.norm(indata)

    if volume > VOLUME_THRESHOLD:
        speaking = True
        audio_q.put(bytes(indata))
    else:
        speaking = False

# ================== UI ==================
root = tk.Tk()
root.title("🎤 Subtitle Speech Visualizer")
root.geometry("1200x300")
root.configure(bg="#0b0b0b")

text = tk.Text(
    root,
    bg="#0b0b0b",
    fg="#eaeaea",
    font=("Helvetica", 36),
    wrap="word",
    height=3,
    bd=0
)
text.pack(expand=True, fill="both", padx=40, pady=60)

text.tag_config("bold", font=("Helvetica", 36, "bold"))
text.config(state="disabled")

# ================== RENDER TEXT ==================
def render_text(sentence):
    text.config(state="normal")
    text.delete("1.0", "end")

    for word in sentence.split():
        clean = word.lower()
        if any(fuzz.ratio(clean, kw) >= FUZZY_THRESHOLD for kw in TARGET_WORDS):
            text.insert("end", word.upper() + " ", "bold")
        else:
            text.insert("end", word + " ")

    text.config(state="disabled")

# ================== AUDIO LOOP ==================
def audio_loop():
    last_partial = ""

    print("🎧 INPUT DEVICE:", sd.query_devices(kind="input"))

    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="int16",
        channels=1,
        callback=callback
    ):
        print("🎤 MIC LAPTOP AKTIF")

        while True:
            if not speaking:
                continue   # ❗ JANGAN HAPUS TEKS SAAT DIAM

            data = audio_q.get()
            rec.AcceptWaveform(data)

            partial = json.loads(rec.PartialResult()).get("partial", "").strip()

            if partial and partial != last_partial:
                last_partial = partial
                render_text(partial)

# ================== START ==================
threading.Thread(target=audio_loop, daemon=True).start()
root.mainloop()

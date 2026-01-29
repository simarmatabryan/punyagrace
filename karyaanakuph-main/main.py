# ================== MATIKAN LOG VOSK ==================
import os
os.environ["VOSK_LOG_LEVEL"] = "-1"

# ================== IMPORT ==================
import sounddevice as sd
import queue
import json
from vosk import Model, KaldiRecognizer
from pythonosc import udp_client
from rapidfuzz import fuzz

# ================== CONFIG ==================
SAMPLE_RATE = 16000
BLOCK_SIZE = 300
FUZZY_THRESHOLD = 80  # minimal % kemiripan agar dianggap keyword

TARGET_WORDS = [
    "distance",
    "afraid",
    "silent",
    "overwhelm",
    "honestly",
    "realize",
    "sorry",
    "grateful",
    "message"
]

MODEL_PATH = r"C:\Users\USER\Downloads\karyaanakuph-main\karyaanakuph-main\vosk-model-small-en-us-0.15"

# ================== MODEL ==================
model = Model(MODEL_PATH)

def new_recognizer():
    rec = KaldiRecognizer(model, SAMPLE_RATE)
    rec.SetWords(False)
    return rec

rec = new_recognizer()

# ================== OSC ==================
osc = udp_client.SimpleUDPClient("127.0.0.1", 8000)

# ================== AUDIO ==================
q = queue.Queue()

def callback(indata, frames, time_info, status):
    q.put(bytes(indata))

print("🎤 Listening (FUZZY KEYWORDS + FIRST/LAST MODE)")

# ================== MAIN LOOP ==================
try:
    with sd.RawInputStream(
        samplerate=SAMPLE_RATE,
        blocksize=BLOCK_SIZE,
        dtype="int16",
        channels=1,
        callback=callback
    ):
        while True:
            audio = q.get()

            if rec.AcceptWaveform(audio):
                result = json.loads(rec.Result())
                text = result.get("text", "").lower().strip()

                # reset recognizer CEPAT
                rec = new_recognizer()

                if not text:
                    continue

                words = text.split()
                detected_keywords = []

                # ================== FUZZY MATCHING ==================
                for w in words:
                    for kw in TARGET_WORDS:
                        score = fuzz.ratio(w, kw)
                        if score >= FUZZY_THRESHOLD:
                            # simpan urutan tanpa duplikat berurutan
                            if not detected_keywords or detected_keywords[-1] != kw:
                                detected_keywords.append(kw)
                            break  # stop cek keyword lain kalau sudah match

                if not detected_keywords:
                    continue

                # ambil FIRST & LAST
                first_kw = detected_keywords[0]
                last_kw = detected_keywords[-1]

                print(f"🎯 FIRST: {first_kw}")
                osc.send_message("/speech/final", first_kw)

                if last_kw != first_kw:
                    print(f"🎯 LAST: {last_kw}")
                    osc.send_message("/speech/final", last_kw)

except KeyboardInterrupt:
    print("🛑 Stopped")
except Exception as e:
    print("❌ Error:", e)

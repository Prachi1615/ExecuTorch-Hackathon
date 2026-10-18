"""Record a few seconds from the mic and turn it into a short object name, offline."""
import re
import subprocess
import wave

import numpy as np
from faster_whisper import WhisperModel

MIC = "plughw:CARD=B101,DEV=0"   # Brio 101 webcam microphone
SECONDS = 3

_model = None
FILLER = r"^(it'?s|this is|that'?s|a|an|the|my|um|uh)\s+"


def load():
    """Load the speech model once (takes a few seconds the first time)."""
    global _model
    if _model is None:
        _model = WhisperModel("base.en", device="cpu", compute_type="int8")
    return _model


def listen_for_name(seconds=SECONDS):
    wav = "/tmp/name.wav"
    subprocess.run(
        ["arecord", "-q", "-D", MIC, "-f", "S16_LE", "-r", "16000", "-c", "1",
         "-d", str(seconds), wav],
        check=True,
    )
    # Read the WAV ourselves: faster-whisper's own decoder (PyAV) has a
    # version mismatch on this image.
    with wave.open(wav, "rb") as w:
        audio = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768.0
    segments, _ = load().transcribe(
        audio, language="en", beam_size=1, vad_filter=True,
        initial_prompt="The name of an object:",
    )
    text = " ".join(s.text for s in segments).strip().lower()
    text = re.sub(r"[^a-z0-9' ]", "", text)
    prev = None
    while prev != text:                 # strip "it's a", "this is the", etc.
        prev = text
        text = re.sub(FILLER, "", text).strip()
    return " ".join(text.split()[:3])   # keep at most 3 words


if __name__ == "__main__":
    load()
    print("say an object name now...")
    print("heard:", repr(listen_for_name()))

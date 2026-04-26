import math
import struct
import subprocess
import tempfile
import threading
import wave


def _generate_tone(frequency: float, duration: float, sample_rate: int = 44100, volume: float = 0.3) -> str:
    n_samples = int(sample_rate * duration)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        path = f.name
    with wave.open(path, "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        for i in range(n_samples):
            t = i / sample_rate
            envelope = min(1.0, t / 0.01) * min(1.0, (duration - t) / 0.01)
            sample = int(volume * envelope * 32767 * math.sin(2 * math.pi * frequency * t))
            wav.writeframes(struct.pack("<h", sample))
    return path


def _play(path: str):
    try:
        subprocess.Popen(["afplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        try:
            subprocess.Popen(["aplay", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def play_start():
    t1 = _generate_tone(440, 0.12)
    t2 = _generate_tone(550, 0.15)

    def _seq():
        _play(t1)
        __import__("time").sleep(0.15)
        _play(t2)

    threading.Thread(target=_seq, daemon=True).start()


def play_success():
    t = _generate_tone(523, 0.4, volume=0.25)
    threading.Thread(target=_play, args=(t,), daemon=True).start()


def play_complete():
    def _seq():
        for freq, dur in [(440, 0.12), (550, 0.12), (660, 0.25)]:
            tone = _generate_tone(freq, dur)
            _play(tone)
            __import__("time").sleep(dur)

    threading.Thread(target=_seq, daemon=True).start()


def play_failed():
    t = _generate_tone(220, 0.3, volume=0.2)
    threading.Thread(target=_play, args=(t,), daemon=True).start()

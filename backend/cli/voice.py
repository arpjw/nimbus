import threading

from cli.renderer import FAINT, GOLD, console


def record_and_transcribe(max_seconds: int = 15) -> str:
    """Record mic input and transcribe with Whisper. Returns transcribed text."""
    try:
        import numpy as np
        import scipy.io.wavfile as wav
        import sounddevice as sd
        import whisper
        import tempfile
        import os
    except ImportError:
        raise RuntimeError("Voice mode requires: pip install sounddevice numpy openai-whisper scipy")

    console.print(f"  [{GOLD}]●[/{GOLD}] [{FAINT}]recording... speak your task (press Enter to stop)[/{FAINT}]")

    sample_rate = 16000
    frames = []
    stop_event = threading.Event()

    def callback(indata, frame_count, time_info, status):
        frames.append(indata.copy())

    def wait_for_enter():
        input()
        stop_event.set()

    threading.Thread(target=wait_for_enter, daemon=True).start()

    with sd.InputStream(samplerate=sample_rate, channels=1, callback=callback):
        stop_event.wait(timeout=max_seconds)

    if not frames:
        return ""

    import numpy as np
    audio = np.concatenate(frames, axis=0)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        wav.write(f.name, sample_rate, audio)
        tmp_path = f.name

    console.print(f"  [{FAINT}]transcribing...[/{FAINT}]")
    model = whisper.load_model("base")
    result = model.transcribe(tmp_path)
    os.unlink(tmp_path)

    text = result["text"].strip()
    console.print(f"  [{GOLD}]heard:[/{GOLD}] {text}")
    return text

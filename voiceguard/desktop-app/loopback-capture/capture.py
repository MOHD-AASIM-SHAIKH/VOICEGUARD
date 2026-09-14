"""VoiceGuard Desktop Audio Capture — Part 1.4 final spec.
Primary: system audio loopback (decoded call audio from Zoom/Meet/WhatsApp Desktop).
Fallback: default microphone (clearly labeled in UI when used).
Also provides get_file_stream() for deterministic testing without acoustic round-trips.

Generator protocol: first yielded value is the source_label string.
The caller (DetectionEngine) must read this first and display it in the UI.
"""
import soundcard as sc
import numpy as np
import time
import warnings
# Suppress Windows WASAPI buffer discontinuity warnings — these are handled by the VAD gate upstream
warnings.filterwarnings("ignore", category=RuntimeWarning, module="soundcard")
try:
    from soundcard.mediafoundation import SoundcardRuntimeWarning
    warnings.filterwarnings("ignore", category=SoundcardRuntimeWarning)
except ImportError:
    pass


def get_loopback_stream(sample_rate: int = 16000, blocksize: int = 8000):
    """Primary source: system audio loopback.
    Desktop calls (Zoom/Meet/WhatsApp Desktop) output through system audio directly —
    loopback captures incoming call speech.

    Yields source_label string first, then mono float32 numpy arrays indefinitely.
    """
    speaker = sc.default_speaker()
    try:
        mic = sc.get_microphone(speaker.name, include_loopback=True)
        source_label = f"Loopback · {mic.name}"
    except Exception as e:
        print(f"[Capture] Loopback unavailable ({e}), falling back to microphone")
        return get_microphone_stream(sample_rate=sample_rate, blocksize=blocksize)

    yield source_label  # caller reads this first and shows it in the UI

    with mic.recorder(samplerate=sample_rate) as recorder:
        while True:
            data = recorder.record(numframes=blocksize)
            mono = data.mean(axis=1) if data.ndim > 1 else data.ravel()
            yield mono.astype(np.float32)


def get_microphone_stream(sample_rate: int = 16000, blocksize: int = 8000):
    """Microphone source: captures user's voice directly from microphone.
    Ideal for testing with user's own live speech.

    Yields source_label string first, then mono float32 numpy arrays indefinitely.
    """
    try:
        mic = sc.default_microphone()
        source_label = f"Microphone · {mic.name}"
    except Exception as e:
        print(f"[Capture] Microphone unavailable ({e}), using synthetic silence")
        yield "Simulated silence (no mic device)"
        while True:
            time.sleep(blocksize / sample_rate)
            yield np.zeros(blocksize, dtype=np.float32)
        return

    yield source_label

    with mic.recorder(samplerate=sample_rate) as recorder:
        while True:
            data = recorder.record(numframes=blocksize)
            mono = data.mean(axis=1) if data.ndim > 1 else data.ravel()
            yield mono.astype(np.float32)


def get_capture_stream(source: str = "loopback", sample_rate: int = 16000, blocksize: int = 8000):
    """Universal source selector: 'loopback' or 'microphone'."""
    if source == "microphone":
        return get_microphone_stream(sample_rate=sample_rate, blocksize=blocksize)
    else:
        return get_loopback_stream(sample_rate=sample_rate, blocksize=blocksize)


def get_file_stream(file_path: str, sample_rate: int = 16000, blocksize: int = 4000):
    """Test-only source: feeds a file directly into the pipeline.
    Use for debugging instead of a speaker→air→mic round-trip, which introduces
    uncontrolled room/mic acoustics as a confound.

    Yields source_label string first, then audio blocks.
    """
    import soundfile as sf
    audio, sr = sf.read(file_path)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    audio = audio.astype(np.float32)
    if sr != sample_rate:
        try:
            import librosa
            audio = librosa.resample(audio, orig_sr=sr, target_sr=sample_rate)
        except ImportError:
            # Simple nearest-sample resample if librosa unavailable
            ratio = sample_rate / sr
            new_len = int(len(audio) * ratio)
            indices = (np.arange(new_len) / ratio).astype(int)
            audio = audio[np.clip(indices, 0, len(audio) - 1)]

    yield f"file:{file_path}"
    for i in range(0, len(audio), blocksize):
        block = audio[i:i + blocksize]
        if len(block) > 0:
            yield block


# Backwards-compatible alias for any existing callers using the old name
def get_audio_stream(sample_rate: int = 16000, blocksize: int = 4000):
    """Alias for get_loopback_stream() — kept for backwards compatibility."""
    return get_loopback_stream(sample_rate=sample_rate, blocksize=blocksize)

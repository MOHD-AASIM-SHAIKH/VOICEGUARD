"""VoiceGuard Confidence Smoother — Part 1.1 robust spec.
Single source of truth for all silence/state constants.
"""
from collections import deque
import numpy as np

SILENCE_RMS_THRESHOLD  = 0.020   # ambient silence RMS floor
CLONE_ENTER_THRESHOLD  = 0.80   # high-confidence threshold to enter CLONED state
REAL_ENTER_THRESHOLD   = 0.50   # threshold to recover back to REAL state
CONSECUTIVE_FRAMES     = 3      # 3 frames (~3s) window for fast, reliable transitions
VAD_MIN_VOICED_SECONDS = 0.40   # minimum seconds of voiced speech energy in window
VAD_FRAME_LEN          = 320    # VAD sub-frame size (20ms @ 16kHz)
VAD_ENERGY_THRESHOLD   = 0.012  # per-frame RMS to count as voiced


def is_silence(chunk) -> bool:
    """Returns True if chunk is ambient silence or negligible room noise.
    Prevents running inference on digital silence or room floor.
    """
    arr = np.asarray(chunk, dtype=np.float32)
    if len(arr) == 0:
        return True
    rms = float(np.sqrt(np.mean(np.square(arr))))
    max_amp = float(np.max(np.abs(arr)))
    # Silence if RMS is negligible OR both RMS and peak are within ambient floor
    return rms < 0.010 or (rms < SILENCE_RMS_THRESHOLD and max_amp < 0.06)


def has_enough_voiced_speech(chunk) -> bool:
    """VAD check: require at least VAD_MIN_VOICED_SECONDS of actual speech energy
    with speech-like crest factor (dynamic range).
    Prevents background hum or buffer drop artifacts from triggering false detections.
    """
    arr = np.asarray(chunk, dtype=np.float32)
    if len(arr) < VAD_FRAME_LEN:
        return False

    n_frames = len(arr) // VAD_FRAME_LEN
    voiced = 0
    for i in range(n_frames):
        frame = arr[i * VAD_FRAME_LEN:(i + 1) * VAD_FRAME_LEN]
        if float(np.sqrt(np.mean(np.square(frame)))) >= VAD_ENERGY_THRESHOLD:
            voiced += 1

    voiced_seconds = (voiced * VAD_FRAME_LEN) / 16000.0
    if voiced_seconds < VAD_MIN_VOICED_SECONDS:
        return False

    # Check that signal has speech-like dynamic range (not steady-state fan hiss)
    rms = float(np.sqrt(np.mean(np.square(arr))))
    crest_factor = float(np.max(np.abs(arr))) / (rms + 1e-8)
    return crest_factor >= 1.6


class ConfidenceSmoother:
    def __init__(self, consecutive_frames: int = CONSECUTIVE_FRAMES,
                 clone_enter_threshold: float = CLONE_ENTER_THRESHOLD,
                 real_enter_threshold: float = REAL_ENTER_THRESHOLD):
        self.consecutive_frames    = consecutive_frames
        self.clone_enter_threshold = clone_enter_threshold
        self.real_enter_threshold  = real_enter_threshold
        self.window                = deque(maxlen=consecutive_frames)
        self.state                 = "REAL"
        self.state_changed_at      = None

    def update(self, spoof_prob: float, timestamp) -> dict:
        """spoof_prob: P(class == spoof/cloned) in [0, 1]. Single source of truth for state.

        Args:
            spoof_prob:  float 0–1 from DetectorModel.predict()["spoof_prob"]
            timestamp:   float seconds or any comparable value

        Returns dict with:
            state                   — "REAL" | "CLONED"
            changed_at              — timestamp of last state flip, or None
            current_spoof_prob      — raw value, for logging/debugging
            real_confidence_display — 1.0 - spoof_prob (honest confidence for REAL state)
            is_new_prediction       — always True; sentinel so the ring only updates here
        """
        self.window.append(spoof_prob)

        # Multi-frame consensus hysteresis
        if len(self.window) >= 1:
            cloned_votes = sum(1 for p in self.window if p >= self.clone_enter_threshold)
            real_votes   = sum(1 for p in self.window if p < self.real_enter_threshold)

            # Enter CLONED on either 2 consistent clone frames OR a decisive high-confidence frame (>= 0.90)
            if (cloned_votes >= 2 or spoof_prob >= 0.90) and spoof_prob >= self.clone_enter_threshold and self.state != "CLONED":
                self.state            = "CLONED"
                self.state_changed_at = timestamp
            # Recover to REAL on either 2 consistent real frames OR a decisive authentic frame (< 0.20)
            elif (real_votes >= 2 or spoof_prob < 0.20) and spoof_prob < self.real_enter_threshold and self.state != "REAL":
                self.state            = "REAL"
                self.state_changed_at = timestamp

        return {
            "state":                   self.state,
            "changed_at":              self.state_changed_at,
            "current_spoof_prob":      spoof_prob,
            "real_confidence_display": 1.0 - spoof_prob,
            "is_new_prediction":       True,
        }

    def reset(self):
        """Clear all state — call on pause/resume."""
        self.window.clear()
        self.state            = "REAL"
        self.state_changed_at = None


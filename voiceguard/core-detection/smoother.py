"""VoiceGuard Confidence Smoother — Part 1.1 final spec.
Single source of truth for all silence/state constants. No other file may define a
second SILENCE_RMS_THRESHOLD, consecutive-frame constant, or recovery condition.
"""
from collections import deque
import numpy as np

SILENCE_RMS_THRESHOLD  = 0.01
CLONE_TRIGGER_THRESHOLD = 0.70   # spoof_prob >= this, for N consecutive frames → CLONED
CONSECUTIVE_FRAMES      = 3      # same N for entering CLONED and recovering to REAL — symmetric

def is_silence(chunk) -> bool:
    rms = float(np.sqrt(np.mean(np.square(chunk))))
    return rms < SILENCE_RMS_THRESHOLD


class ConfidenceSmoother:
    def __init__(self, consecutive_frames: int = CONSECUTIVE_FRAMES,
                 clone_threshold: float = CLONE_TRIGGER_THRESHOLD):
        self.consecutive_frames = consecutive_frames
        self.clone_threshold    = clone_threshold
        self.window             = deque(maxlen=consecutive_frames)
        self.state              = "REAL"
        self.state_changed_at   = None

    def update(self, spoof_prob: float, timestamp) -> dict:
        """spoof_prob: P(class == spoof/cloned) in [0, 1]. Single source of truth for state.

        Args:
            spoof_prob:  float 0–1 from DetectorModel.predict()["spoof_prob"]
            timestamp:   float seconds or any comparable value

        Returns dict with:
            state                  — "REAL" | "CLONED"
            changed_at             — timestamp of last state flip, or None
            current_spoof_prob     — raw value, for logging/debugging
            real_confidence_display — 1.0 - spoof_prob; this is the ONLY value the UI ring
                                      must display — no flooring, no fudging
            is_new_prediction      — always True; sentinel so the ring only updates here
        """
        self.window.append(spoof_prob)

        if len(self.window) == self.consecutive_frames:
            all_cloned = all(p >= self.clone_threshold for p in self.window)
            all_real   = all(p <  self.clone_threshold for p in self.window)

            if all_cloned and self.state != "CLONED":
                self.state            = "CLONED"
                self.state_changed_at = timestamp
            elif all_real and self.state != "REAL":
                self.state            = "REAL"
                self.state_changed_at = timestamp
            # mixed window → state holds (this IS the hysteresis — no extra condition needed)

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

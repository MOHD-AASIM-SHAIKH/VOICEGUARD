"""VoiceGuard Audio Chunker — Part 1.2 final spec.
Rolling sliding-window buffer. Short utterances ("hello") are never isolated and
repeat-padded — they become part of a 4.04s window of real contiguous audio.
"""
import numpy as np


class AudioChunker:
    def __init__(self, sample_rate=16000, window_len=64600, hop_seconds=1.0):
        self.sample_rate = sample_rate
        self.window_len  = window_len              # exact model input length — 64,600 @ 16kHz ≈ 4.04s
        self.hop_len     = int(sample_rate * hop_seconds)
        self.buffer      = np.zeros(0, dtype=np.float32)

    def push(self, new_audio: np.ndarray):
        """Feed newly captured audio; returns list of window-length chunks ready for inference.

        Short utterances are NOT classified in isolation — they accumulate in the buffer
        alongside real captured audio before/after them, producing a natural contiguous
        window, never a repeated-loop artifact.
        """
        self.buffer = np.concatenate([self.buffer, new_audio.astype(np.float32)])
        chunks = []

        if len(self.buffer) < self.window_len:
            return chunks  # not enough context yet — startup latency, expected

        while len(self.buffer) >= self.window_len:
            chunks.append(self.buffer[:self.window_len].copy())
            if len(self.buffer) <= self.window_len:
                break
            self.buffer = self.buffer[self.hop_len:]

        return chunks

    @property
    def chunk_len(self):
        """Hop length in samples — used for timestamp advancement."""
        return self.hop_len

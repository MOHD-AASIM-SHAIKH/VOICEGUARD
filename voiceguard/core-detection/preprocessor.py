import numpy as np

TARGET_LEN = 64600  # ~4s at 16kHz, matches AASIST-L nb_samp

def pad(audio: np.ndarray, target_len: int = TARGET_LEN) -> np.ndarray:
    x_len = len(audio)
    if x_len >= target_len:
        # center-crop for deterministic eval (not random crop — that's for training augmentation)
        start = (x_len - target_len) // 2
        return audio[start:start + target_len]
    # repeat-pad: tile the audio until it's long enough, then trim
    num_repeats = int(np.ceil(target_len / x_len))
    tiled = np.tile(audio, num_repeats)
    return tiled[:target_len]

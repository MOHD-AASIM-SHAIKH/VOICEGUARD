"""VoiceGuard Core Detector — Part 1.3 final spec.
Normalization happens exactly once, here. No caller-side normalization permitted.
"""
import json, torch, numpy as np
import sys, os, importlib

# Resolve paths relative to THIS file's directory, not CWD
_HERE = os.path.dirname(os.path.abspath(__file__))
_aasist_path = os.path.join(_HERE, "aasist")
if _aasist_path not in sys.path:
    sys.path.insert(0, _aasist_path)

# Use importlib so both runtime and static analysis tools can resolve this.
# models/AASIST.py lives at: core-detection/aasist/models/AASIST.py
_models_spec = importlib.util.spec_from_file_location(
    "AASIST_model",
    os.path.join(_aasist_path, "models", "AASIST.py")
)
_models_mod = importlib.util.module_from_spec(_models_spec)  # type: ignore
_models_spec.loader.exec_module(_models_mod)  # type: ignore
Model = _models_mod.Model


class DetectorModel:
    def __init__(self, config_path=None, weights_path=None):
        if config_path is None:
            config_path = os.path.join(_HERE, "aasist", "config", "AASIST-L.conf")
        if weights_path is None:
            # Use fine-tuned weights if available, else fall back to pretrained
            finetuned  = os.path.join(_HERE, "aasist", "models", "weights", "AASIST-L-finetuned.pth")
            pretrained = os.path.join(_HERE, "aasist", "models", "weights", "AASIST-L.pth")
            weights_path = finetuned if os.path.exists(finetuned) else pretrained

        with open(config_path) as f:
            config = json.load(f)
        self.model = Model(config["model_config"])
        state_dict = torch.load(weights_path, map_location="cpu")
        self.model.load_state_dict(state_dict)
        self.model.eval()

        # Label convention VERIFIED empirically against dev_compressed/fake/ and dev_compressed/real/:
        # index 0 → spoof/cloned (fake), index 1 → bonafide/real
        # Fake files: idx0 ≈ 1.000, idx1 ≈ 0.000  → argmax=0 → "cloned" ✓
        # Real files: idx0 ≈ 0.000, idx1 ≈ 1.000  → argmax=1 → "real"   ✓
        self.LABEL_MAP = {0: "cloned", 1: "real"}

    def predict(self, chunk: np.ndarray) -> dict:
        """Part 1.3 contract: returns {label, confidence, spoof_prob}.
        spoof_prob is the ONLY value the smoother consumes.
        Normalization happens here and NOWHERE else — callers must not re-normalize.
        """
        chunk = chunk.astype(np.float32)

        # ── Gain-limited Speech AGC Normalization ─────────────────────────
        # Avoid amplifying ambient noise / breath pauses into high-amplitude noise walls.
        max_amp = float(np.max(np.abs(chunk))) if len(chunk) > 0 else 0.0
        if max_amp >= 0.015:
            # Scale towards 0.80 peak, but limit gain multiplier to at most 4.0x
            gain = min(4.0, 0.80 / (max_amp + 1e-8))
            chunk = chunk * gain
        elif max_amp > 0.001:
            # Low ambient noise — apply minimal gentle scaling without noise explosion
            chunk = chunk * min(1.5, 0.80 / (max_amp + 1e-8))

        # ── Length guarantee (chunker already provides window_len=64600, this is a safety net) ──
        if len(chunk) > 64600:
            chunk = chunk[:64600]
        elif len(chunk) < 64600:
            if len(chunk) > 0:
                num_repeats = int(np.ceil(64600 / len(chunk)))
                chunk = np.tile(chunk, num_repeats)[:64600]
            else:
                chunk = np.zeros(64600, dtype=np.float32)

        # ── Smooth Edge Taper ─────────────────────────────────────────────
        # Eliminate boundary step discontinuities that create high-frequency SincNet artifacts
        if len(chunk) >= 400:
            w = np.sin(np.linspace(0, np.pi / 2, 200, dtype=np.float32)) ** 2
            chunk[:200] *= w
            chunk[-200:] *= w[::-1]

        x = torch.tensor(chunk, dtype=torch.float32).unsqueeze(0)  # (1, 64600)
        with torch.no_grad():
            _, out = self.model(x)              # returns (graph_embedding, logits)
            probs      = torch.softmax(out, dim=1).squeeze(0)
            spoof_prob = float(probs[0].item()) # index 0 = spoof/cloned — verified mapping
            real_prob  = float(probs[1].item()) # index 1 = bonafide/real
            pred_idx   = int(torch.argmax(probs).item())

        return {
            "label":      self.LABEL_MAP[pred_idx],
            "confidence": max(spoof_prob, real_prob),   # winner's probability
            "spoof_prob": spoof_prob,                   # smoother only uses this
        }

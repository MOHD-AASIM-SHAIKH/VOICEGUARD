"""
VoiceGuard Web API — thin FastAPI wrapper over the shared core-detection pipeline.

Blueprint reference:
  - Part 3.1: AudioChunker → Preprocessor → DetectorModel → ConfidenceSmoother
  - Part 3.4: computeEvidenceHash(incident) — metadata only, never raw audio
  - Part 6.2: Incident schema {incidentId, detectedAt, callType, app, confidenceAtAlert}
  - Part 7:   backend-services/ is the correct location for this module

NO detection logic lives here. This file contains only:
  - FastAPI route definitions
  - Audio decoding (wav bytes → float32 numpy array)
  - Incident object construction and evidence hash/Chakshu delegation
  - Honest model_live / blockchain_status values

All detection is performed by importing from voiceguard/core-detection/.
All hashing is performed by importing from voiceguard/reporting/evidence-hash/.
All Chakshu URL building is performed by importing from voiceguard/reporting/chakshu-link-builder/.
"""

import io
import os
import sys
import time
import uuid
import wave
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# ── Path resolution ───────────────────────────────────────────────────────────
# This file lives at: voiceguard/backend-services/web-api/main.py
# We need:
#   voiceguard/core-detection/    → DetectorModel, AudioChunker, ConfidenceSmoother
#   voiceguard/reporting/evidence-hash/   → compute_evidence_hash
#   voiceguard/reporting/chakshu-link-builder/ → build_chakshu_link
_HERE         = Path(__file__).resolve().parent          # web-api/
_BACKEND_SVCS = _HERE.parent                             # backend-services/
_VOICEGUARD   = _BACKEND_SVCS.parent                     # voiceguard/
_REPO_ROOT    = _VOICEGUARD.parent                       # repo root

_CORE_DET     = _VOICEGUARD / "core-detection"
_EV_HASH      = _VOICEGUARD / "reporting" / "evidence-hash"
_CHAKSHU      = _VOICEGUARD / "reporting" / "chakshu-link-builder"

for _p in [str(_CORE_DET), str(_EV_HASH), str(_CHAKSHU)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ── Shared pipeline imports ───────────────────────────────────────────────────
try:
    from detector import DetectorModel
    from chunker import AudioChunker
    from smoother import ConfidenceSmoother, is_silence
    _model  = DetectorModel()
    MODEL_LOADED = True
except Exception as _model_err:
    print(f"[VoiceGuard] WARNING: DetectorModel failed to load: {_model_err}")
    print("[VoiceGuard] /api/analyze will return model_live=false on all requests.")
    _model  = None
    MODEL_LOADED = False

# ── Reporting imports ─────────────────────────────────────────────────────────
from hash import compute_evidence_hash   # voiceguard/reporting/evidence-hash/hash.py
from link import build_chakshu_link      # voiceguard/reporting/chakshu-link-builder/link.py

# ── Constants ─────────────────────────────────────────────────────────────────
MAX_UPLOAD_BYTES   = 15 * 1024 * 1024   # 15 MB — reject above this
ALLOWED_MIME_PREFIXES = ("audio/",)
SAMPLE_RATE        = 16000
WINDOW_LEN         = 64600              # 4.04s at 16kHz — matches AASIST-L nb_samp

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="VoiceGuard Detection API",
    description=(
        "Thin HTTP wrapper over the shared AASIST-L detection pipeline. "
        "Detection logic lives exclusively in voiceguard/core-detection/."
    ),
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    # NOTE: allow_origins=["*"] is intentionally relaxed for SIH prototype/demo.
    # Scope this down to the deployed domain before any production use.
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (index.html and any future assets) from ./static/
_STATIC_DIR = _HERE / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


# ── Audio helpers ──────────────────────────────────────────────────────────────

def _decode_audio_bytes(raw: bytes) -> np.ndarray:
    """Decode uploaded audio bytes → float32 mono numpy array at 16kHz.

    Tries wave (stdlib, zero extra deps) first. Falls back to soundfile which
    handles MP3/FLAC/M4A via libsndfile. If both fail, raises ValueError.
    Does NOT write raw bytes to disk at any point.
    """
    # --- wave (stdlib) ---
    try:
        with wave.open(io.BytesIO(raw), "rb") as wf:
            n_frames = wf.getnframes()
            frames   = wf.readframes(n_frames)
            sr       = wf.getframerate()
            width    = wf.getsampwidth()
            nchan    = wf.getnchannels()

        if width == 2:
            samples = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
        elif width == 4:
            samples = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
        else:
            samples = np.frombuffer(frames, dtype=np.uint8).astype(np.float32) / 128.0 - 1.0

        if nchan > 1:
            samples = samples.reshape(-1, nchan).mean(axis=1)

        # Simple integer-ratio downsample to 16kHz if needed
        if sr != SAMPLE_RATE and sr > 0:
            ratio = int(round(sr / SAMPLE_RATE))
            if ratio > 1:
                samples = samples[::ratio]

        return samples.astype(np.float32)
    except Exception:
        pass

    # --- soundfile fallback (handles WAV/FLAC/OGG/MP3 via libsndfile) ---
    try:
        import soundfile as sf
        data, sr = sf.read(io.BytesIO(raw), dtype="float32", always_2d=False)
        if data.ndim > 1:
            data = data.mean(axis=1)
        if sr != SAMPLE_RATE and sr > 0:
            ratio = int(round(sr / SAMPLE_RATE))
            if ratio > 1:
                data = data[::ratio]
        return data.astype(np.float32)
    except Exception:
        pass

    raise ValueError("Could not decode audio — unsupported format or corrupt file.")


def _run_pipeline(samples: np.ndarray) -> dict:
    """Run the full core-detection pipeline over a numpy float32 audio array.

    For an uploaded file (non-streaming), we chunk the audio the same way the
    streaming pipeline does: AudioChunker pushes the whole array, returning
    overlapping 64,600-sample windows, each scored by DetectorModel.
    ConfidenceSmoother applies the 3-consecutive-frame hysteresis rule.

    Returns the smoother's final state dict plus the last raw spoof_prob.
    """
    chunker  = AudioChunker(sample_rate=SAMPLE_RATE, window_len=WINDOW_LEN, hop_seconds=1.0)
    smoother = ConfidenceSmoother()

    chunks = chunker.push(samples)

    # If the audio is shorter than one window, detector.py's internal safety net
    # handles padding — feed it directly as one chunk.
    if not chunks:
        chunks = [samples]

    final_pred    = None
    last_smoother = None
    timestamp     = 0.0

    for chunk in chunks:
        if is_silence(chunk):
            continue                      # silence gate — skip, don't score
        pred = _model.predict(chunk)      # {label, confidence, spoof_prob}
        smoother_out = smoother.update(pred["spoof_prob"], timestamp)
        timestamp   += 1.0               # 1s hop between frames
        final_pred    = pred
        last_smoother = smoother_out

    if final_pred is None:
        # All chunks were silence — return the "REAL" smoother default
        return {
            "spoof_prob":   0.0,
            "label":        "real",
            "confidence":   1.0,
            "smoother":     smoother.update(0.0, 0.0),
            "all_silence":  True,
        }

    return {
        "spoof_prob":   final_pred["spoof_prob"],
        "label":        final_pred["label"],
        "confidence":   final_pred["confidence"],
        "smoother":     last_smoother,
        "all_silence":  False,
    }


def _generate_synthetic_audio(sample_type: str = "human",
                               duration_s: float = 4.0,
                               sr: int = SAMPLE_RATE) -> np.ndarray:
    """Synthetic test signals for browser preset buttons.

    These are acoustic simulations only — they run through the real model
    and may or may not be correctly classified (a synthetic sine-wave
    'human' signal is not actual human speech). Presets are a convenience
    for demonstrating the UI pipeline, not a claim of accuracy.
    """
    n  = int(duration_s * sr)
    t  = np.linspace(0, duration_s, n, endpoint=False)

    if sample_type == "human":
        f0    = 140.0 + 15.0 * np.sin(2 * np.pi * 1.5 * t)
        phase = 2 * np.pi * np.cumsum(f0) / sr
        audio = (0.40 * np.sin(phase)
                 + 0.25 * np.sin(2 * phase)
                 + 0.15 * np.sin(3 * phase)
                 + 0.10 * np.sin(4 * phase))
        cadence = np.clip(np.sin(2 * np.pi * 2.2 * t), 0, 1) ** 1.5
        audio   = audio * (0.15 + 0.85 * cadence)
        audio  += 0.02 * np.random.normal(0, 0.05, n)
    else:
        f0       = 175.0 + 3.0 * np.sin(2 * np.pi * 0.4 * t)
        phase    = 2 * np.pi * np.cumsum(f0) / sr
        carrier  = np.sin(phase) + 0.3 * np.sin(3 * phase) + 0.25 * np.sin(5 * phase)
        artifacts = 0.2 * np.sin(2 * np.pi * 3200 * t) * np.sin(2 * np.pi * 12 * t)
        audio    = carrier * 0.7 + artifacts
        audio   += 0.01 * np.random.uniform(-0.05, 0.05, n)

    mx = np.max(np.abs(audio))
    if mx > 1e-5:
        audio = audio / mx * 0.85
    return audio.astype(np.float32)


def _samples_to_wav_bytes(samples: np.ndarray, sr: int = SAMPLE_RATE) -> bytes:
    buf    = io.BytesIO()
    s16    = np.clip(samples * 32767.0, -32768, 32767).astype(np.int16)
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(s16.tobytes())
    return buf.getvalue()


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Returns truthful model_loaded status. Never lie about model state."""
    return {
        "status":       "healthy",
        "service":      "VoiceGuard Detection API v2",
        "model_loaded": MODEL_LOADED,           # true only if DetectorModel() succeeded
        "engine":       "AASIST-L Graph Neural Network",
        "pipeline":     "AudioChunker → DetectorModel → ConfidenceSmoother (shared core-detection)",
    }


@app.get("/api/sample/{sample_type}")
def get_sample_audio(sample_type: str):
    """Return playable synthetic WAV for browser preset audio player."""
    if sample_type not in ("human", "cloned"):
        sample_type = "human"
    wav = _samples_to_wav_bytes(_generate_synthetic_audio(sample_type))
    return Response(content=wav, media_type="audio/wav")


@app.post("/api/analyze")
async def analyze_audio(
    preset: str = Form(None),
    file:   UploadFile = File(None),
):
    """Run the full core-detection pipeline on uploaded audio or a preset.

    Returns:
        label           — "real" | "cloned" (from pipeline)
        classification  — "REAL" | "CLONED"
        is_cloned       — bool
        confidence_pct  — float, winner probability × 100
        spoof_prob      — float 0–1 from DetectorModel
        smoother_state  — "REAL" | "CLONED" after ConfidenceSmoother
        evidence_hash   — 0x<sha256 of Incident metadata object — NOT raw audio>
        blockchain_status — honest status string, never a fake block number
        chakshu_url     — pre-filled Chakshu portal link
        model_live      — bool: false if model failed to load
        latency_ms      — int

    Errors:
        413 if uploaded file > 15 MB
        415 if content-type is not audio/*
        400 if file is corrupt / undecodable
        503 if model not loaded and no fallback is acceptable
    """
    if not MODEL_LOADED:
        # Honest failure — do not substitute fake numbers.
        raise HTTPException(
            status_code=503,
            detail={
                "error":        "model_not_loaded",
                "model_live":   False,
                "message":      (
                    "DetectorModel failed to initialize (weights may be missing or corrupt). "
                    "Cannot produce a real prediction. Check server startup logs."
                ),
            },
        )

    start_time = time.time()
    samples    = None

    # ── Input: uploaded file ─────────────────────────────────────────────────
    if file and file.filename:
        # 1. Content-type guard
        ct = (file.content_type or "").lower()
        if not any(ct.startswith(pfx) for pfx in ALLOWED_MIME_PREFIXES):
            raise HTTPException(
                status_code=415,
                detail={
                    "error":   "unsupported_media_type",
                    "detail":  f"Expected audio/*, got '{ct}'. Upload a WAV, MP3, FLAC, or M4A file.",
                },
            )

        # 2. Size guard — read in streaming fashion to avoid OOM on huge files
        raw_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(raw_bytes) > MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail={
                    "error":  "file_too_large",
                    "detail": f"Upload exceeds {MAX_UPLOAD_BYTES // (1024*1024)} MB limit.",
                },
            )

        # 3. Decode — raw bytes never written to disk, processed in-memory only
        try:
            samples = _decode_audio_bytes(raw_bytes)
        except ValueError as decode_err:
            raise HTTPException(
                status_code=400,
                detail={
                    "error":  "audio_decode_failed",
                    "detail": str(decode_err),
                },
            )

    # ── Input: preset (synthetic audio → real pipeline) ──────────────────────
    if samples is None:
        mode    = "cloned" if preset == "cloned" else "human"
        samples = _generate_synthetic_audio(mode)

    # ── Run the real shared pipeline ─────────────────────────────────────────
    result = _run_pipeline(samples)

    spoof_prob     = result["spoof_prob"]
    is_cloned      = result["smoother"]["state"] == "CLONED"
    confidence     = result["confidence"]
    smoother_state = result["smoother"]["state"]

    elapsed_ms = int((time.time() - start_time) * 1000)

    # ── Evidence hash — metadata-based per blueprint 3.4 / 6.2 ─────────────
    # Hash is derived from the Incident object, NOT from raw audio bytes.
    # This means the same audio submitted at different times gets a different hash
    # (timestamp changes), which is correct — it's an incident record, not an audio fingerprint.
    incident = {
        "incidentId":        str(uuid.uuid4()),
        "detectedAt":        datetime.now(timezone.utc).isoformat(),
        "callType":          "web_upload",
        "app":               "voiceguard_web",
        "confidenceAtAlert": round(spoof_prob, 4),
    }
    evidence_hash = compute_evidence_hash(incident)    # from reporting/evidence-hash/hash.py

    # ── Chakshu URL ───────────────────────────────────────────────────────────
    chakshu_url = build_chakshu_link(incident)         # from reporting/chakshu-link-builder/link.py

    # ── Blockchain status — honest ────────────────────────────────────────────
    # No web3.py, no contract deployed, no funded wallet configured.
    # Returning a fake block number would be a direct lie to judges — blueprint 1.4.
    blockchain_status = "not_connected_to_testnet"

    return JSONResponse({
        "verdict":           "CRITICAL: AI VOICE CLONE DETECTED" if is_cloned else "AUTHENTIC HUMAN VOICE",
        "classification":    smoother_state,
        "is_cloned":         is_cloned,
        "confidence_pct":    round(confidence * 100, 1),
        "spoof_prob":        round(spoof_prob, 4),
        "smoother_state":    smoother_state,
        "evidence_hash":     f"0x{evidence_hash}",
        "evidence_short":    f"0x{evidence_hash[:8]}...{evidence_hash[-6:]}",
        "incident":          incident,
        "blockchain_status": blockchain_status,
        "chakshu_url":       chakshu_url,
        "latency_ms":        elapsed_ms,
        "model_architecture": "AASIST-L (Raw Graph Waveform Network)",
        "model_live":        MODEL_LOADED,
        "all_silence":       result.get("all_silence", False),
    })


@app.get("/", response_class=HTMLResponse)
def index():
    """Serve the UI from the real static file — not an inline Python string."""
    html_path = _STATIC_DIR / "index.html"
    try:
        return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return HTMLResponse(
            content="<h1>VoiceGuard</h1><p>UI not found. Expected static/index.html</p>",
            status_code=500,
        )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

# VoiceGuard 🛡️

**Real-time AI Voice Clone Detector & Defense Platform**

VoiceGuard detects cloned/synthetic voices on live calls (Zoom, WhatsApp Desktop, Meet) and instantly alerts you with a visual signal. It uses an on-device AASIST-L deep learning model — no audio leaves your device.

---

## 🌐 Live Web Prototype (SIH Evaluation)

An interactive web prototype is included for instant evaluation in any web browser without local installation:
- **Test presets:** Authentic human speech vs. AI cloned deepfake voice
- **Live upload:** Test any custom audio clip (`.wav`, `.mp3`)
- **Visual Gauge:** Real-time circular confidence ring & spectrogram verdict
- **Evidence generation:** SHA-256 evidence hashing + direct DoT Chakshu reporting link

Run locally:
```bash
python -m uvicorn app:app --reload
```
Or deploy directly to **Render** with 1-click using the included `render.yaml`.

---

## Architecture

```
voiceguard/
├── core-detection/       # AASIST-L model, chunker, smoother, detector
├── desktop-app/          # PySide6 Windows/macOS desktop app (loopback capture)
├── mobile-app/           # Android (Kotlin) real-time detection app
├── backend-services/     # Intent parser, risk engine, campaign linking
├── reporting/            # Evidence hash, Chakshu link builder
├── blockchain/           # Solidity smart contracts (Polygon Amoy)
└── docs/                 # Diagnostic reports, progress log, audit report
```

**Detection pipeline:**
1. WASAPI loopback captures decoded call audio from system speakers
2. Rolling 4.04s sliding window (64,600 samples @ 16kHz) — no short-clip repeat-padding
3. RMS silence gate (threshold 0.01) skips silence frames — no false positives on pauses
4. AASIST-L inference: returns `spoof_prob` in [0,1]
5. Confidence smoother requires **3 consecutive** high-spoof frames before alerting
6. Auto-dismisses alert when voice returns to REAL

---

## Accuracy

| Test | Result |
|------|--------|
| Clean baseline (ASVspoof2019 LA dev) | **99.2%** (397/400) |
| After 16kbps Opus compression | **98.0%** |
| After harsh degradation + fine-tuning | **75.5%** (+15pp) |
| 43.81s live real speech (8 speakers) | **0 false CLONED events** |
| Clone detection latency | **4.0 seconds** after clone onset |

---

## Setup

### Requirements

- Python 3.12+
- Windows 10/11 (WASAPI loopback) or macOS (loopback via BlackHole)
- CUDA optional (runs on CPU)

### Install

```bash
git clone https://github.com/MOHD-AASIM-SHAIKH/VOICEGUARD.git
cd VOICEGUARD

python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install numpy librosa soundfile scikit-learn scipy soundcard PySide6
```

### Download Dataset (optional, for retraining)

Download ASVspoof2019 LA from [Edinburgh DataShare](https://datashare.ed.ac.uk/handle/10283/3336) and place under `datasets/LA/`.

### Run Desktop App

```bash
python voiceguard/desktop-app/alert-window/main_window.py
```

**Keyboard shortcuts:**
| Key | Action |
|-----|--------|
| `C` | Simulate clone detection |
| `A` | Show guarded transaction screen |
| `H` | Show blockchain evidence history |
| `Esc` | Return to idle |

---

## Blockchain (Polygon Amoy Testnet)

Smart contracts for on-chain evidence logging:

```bash
cd voiceguard/blockchain
npm install
npx hardhat compile
npx hardhat run scripts/deploy.js --network hardhat   # local test
```

For testnet: set `AMOY_RPC_URL` and `PRIVATE_KEY` env vars, then deploy to `--network amoy`.

---

## Mobile App (Android)

Open `voiceguard/mobile-app/` in Android Studio. The on-device model is a 0.7MB TorchScript Lite export (`aasist_mobile.ptl`).

---

## Key Files

| File | Role |
|------|------|
| `core-detection/detector.py` | AASIST-L inference wrapper |
| `core-detection/chunker.py` | Rolling 4.04s sliding window |
| `core-detection/smoother.py` | 3-frame consecutive state machine |
| `desktop-app/loopback-capture/capture.py` | WASAPI loopback capture |
| `desktop-app/alert-window/main_window.py` | PySide6 main window + detection loop |
| `docs/diagnostic-report.md` | Root-cause analysis |
| `docs/audit-report.md` | Blueprint compliance audit |

---

## License

MIT License — see `LICENSE`.

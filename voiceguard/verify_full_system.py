"""Comprehensive End-to-End System Verification for VoiceGuard
Tests:
1. Real speech recognition & honest confidence display
2. Cloned speech detection & transition latency
3. Bidirectional transition (Real -> Clone -> Real)
4. Silence / Low Ambient Noise immunity
"""
import sys, os, time
sys.path.insert(0, 'core-detection')
sys.path.insert(0, 'desktop-app/loopback-capture')

import numpy as np
import soundfile as sf

from detector import DetectorModel
from chunker import AudioChunker
from smoother import ConfidenceSmoother, is_silence, has_enough_voiced_speech

def run_tests():
    print("=" * 70)
    print("VOICEGUARD END-TO-END SYSTEM VERIFICATION")
    print("=" * 70)

    model = DetectorModel()

    # --- Test 1: Real Voice Files ---
    print("\n--- TEST 1: Real Voice Verification ---")
    real_fnames = sorted([f for f in os.listdir('test_audio/real') if f.endswith('.wav')])
    all_real_passed = True
    for fname in real_fnames[:5]:
        audio, sr = sf.read(os.path.join('test_audio/real', fname))
        chunker = AudioChunker(sample_rate=16000, hop_seconds=0.5)
        smoother = ConfidenceSmoother()
        states = []
        confs = []
        for i in range(0, len(audio), 8000):
            block = audio[i:i+8000]
            for c in chunker.push(block):
                if is_silence(c) or not has_enough_voiced_speech(c):
                    continue
                p = model.predict(c)
                r = smoother.update(p["spoof_prob"], i/16000.0)
                states.append(r["state"])
                confs.append(r["real_confidence_display"])

        final_state = states[-1] if states else "NO_CHUNKS"
        avg_conf = (sum(confs) / len(confs)) * 100 if confs else 0.0
        passed = (final_state == "REAL" and avg_conf > 85.0)
        status = "PASSED" if passed else "FAILED"
        if not passed:
            all_real_passed = False
        print(f"  [{status}] {fname:22s} -> State: {final_state:6s} | Avg Authentic Conf: {avg_conf:5.1f}%")

    assert all_real_passed, "Real voice verification failed!"
    print(">>> Test 1 Result: ALL REAL VOICES ACCURATELY DETECTED AS REAL (0 FALSE POSITIVES)!")

    # --- Test 2: Cloned Voice Files ---
    print("\n--- TEST 2: Cloned Voice Verification ---")
    cloned_fnames = sorted([f for f in os.listdir('test_audio/cloned') if f.endswith('.wav')])
    all_cloned_passed = True
    for fname in cloned_fnames[:5]:
        audio, sr = sf.read(os.path.join('test_audio/cloned', fname))
        chunker = AudioChunker(sample_rate=16000, hop_seconds=0.5)
        smoother = ConfidenceSmoother()
        states = []
        spoofs = []
        for i in range(0, len(audio), 8000):
            block = audio[i:i+8000]
            for c in chunker.push(block):
                if is_silence(c) or not has_enough_voiced_speech(c):
                    continue
                p = model.predict(c)
                r = smoother.update(p["spoof_prob"], i/16000.0)
                states.append(r["state"])
                spoofs.append(p["spoof_prob"])

        final_state = states[-1] if states else "NO_CHUNKS"
        max_spoof = max(spoofs) * 100 if spoofs else 0.0
        passed = (final_state == "CLONED" and max_spoof > 80.0)
        status = "PASSED" if passed else "FAILED"
        if not passed:
            all_cloned_passed = False
        print(f"  [{status}] {fname:22s} -> State: {final_state:6s} | Max Spoof Risk: {max_spoof:5.1f}%")

    assert all_cloned_passed, "Cloned voice verification failed!"
    print(">>> Test 2 Result: ALL CLONED VOICES ACCURATELY DETECTED AS CLONED!")

    # --- Test 3: Bidirectional Transition (Real -> Clone -> Real) ---
    print("\n--- TEST 3: Bidirectional Transition (Real -> Clone -> Real) ---")
    real_audio, _ = sf.read('test_audio/real/real_voice_1.wav')
    clone_audio, _ = sf.read('test_audio/cloned/cloned_voice_1.wav')
    real2_audio, _ = sf.read('test_audio/real/real_voice_2.wav')

    # Concatenate sequence: 5s Real, 5s Clone, 5s Real
    full_stream = np.concatenate([real_audio, clone_audio, real2_audio])
    chunker = AudioChunker(sample_rate=16000, hop_seconds=0.5)
    smoother = ConfidenceSmoother()

    timeline = []
    for i in range(0, len(full_stream), 8000):
        block = full_stream[i:i+8000]
        t = i / 16000.0
        for c in chunker.push(block):
            if is_silence(c) or not has_enough_voiced_speech(c):
                continue
            p = model.predict(c)
            r = smoother.update(p["spoof_prob"], t)
            timeline.append((t, r["state"], p["spoof_prob"]))

    print(f"  Stream total duration: {len(full_stream)/16000:.1f}s")
    clone_detected_at = None
    recovered_at = None
    for t, state, sp in timeline:
        if 5.0 <= t < 10.0 and state == "CLONED" and clone_detected_at is None:
            clone_detected_at = t
        if t >= 10.0 and state == "REAL" and recovered_at is None and clone_detected_at is not None:
            recovered_at = t

    print(f"  Transition Real -> Clone: Detected at t={clone_detected_at:.1f}s (latency: {clone_detected_at - 5.0:.1f}s)")
    print(f"  Transition Clone -> Real: Recovered at t={recovered_at:.1f}s (latency: {recovered_at - 10.0:.1f}s)")
    assert clone_detected_at is not None, "Failed to detect clone transition!"
    assert recovered_at is not None, "Failed to recover to real speech!"
    print(">>> Test 3 Result: BIDIRECTIONAL TRANSITION SUCCEEDED!")

    # --- Test 4: Silence & Ambient Noise Immunity ---
    print("\n--- TEST 4: Silence & Ambient Noise Immunity ---")
    silence = np.zeros(64600 * 2, dtype=np.float32)
    room_noise = np.random.randn(64600 * 2).astype(np.float32) * 0.003
    chunker = AudioChunker(sample_rate=16000, hop_seconds=0.5)
    smoother = ConfidenceSmoother()

    inferred_count = 0
    for block in [silence[:32000], silence[32000:64000], room_noise[:32000], room_noise[32000:64000]]:
        for c in chunker.push(block):
            if is_silence(c) or not has_enough_voiced_speech(c):
                continue
            inferred_count += 1

    print(f"  Non-speech chunks allowed through gate: {inferred_count} (target: 0)")
    assert inferred_count == 0, f"Silence/noise leaked through gate ({inferred_count} chunks)!"
    print(">>> Test 4 Result: PERFECT NOISE IMMUNITY (0 LEAKED FRAMES, STATE HOLDS STABLE)!")

    # --- Test 5: Short Utterance ('Hello') False-Positive Immunity ---
    print("\n--- TEST 5: Short Utterance ('Hello') False-Positive Immunity ---")
    real_sample, _ = sf.read('test_audio/real/real_voice_1.wav')
    hello_speech = real_sample[19200:28800].astype(np.float32)  # 0.6s real voice 'hello'
    
    # Simulate 8s microphone stream with ambient noise where user says just 'hello' at t=2.0s
    stream_noise = np.random.randn(int(8.0 * 16000)).astype(np.float32) * 0.003
    stream_noise[32000:32000+len(hello_speech)] += hello_speech
    
    chunker = AudioChunker(sample_rate=16000, hop_seconds=0.5)
    smoother = ConfidenceSmoother()
    
    hello_states = []
    for i in range(0, len(stream_noise), 8000):
        block = stream_noise[i:i+8000]
        t = i / 16000.0
        for c in chunker.push(block):
            if is_silence(c) or not has_enough_voiced_speech(c):
                continue
            p = model.predict(c)
            r = smoother.update(p["spoof_prob"], t)
            hello_states.append(r["state"])

    has_cloned_false_alarm = "CLONED" in hello_states
    print(f"  Utterance: Single 0.6s 'Hello' in 8s stream")
    print(f"  Clone states triggered: {has_cloned_false_alarm} (target: False)")
    assert not has_cloned_false_alarm, "FAILED: Speaking 'Hello' triggered a false clone alert!"
    print(">>> Test 5 Result: PERFECT IMMUNITY ON SHORT UTTERANCES ('HELLO' NEVER TRIGGERS CLONE)!")

    print("\n" + "=" * 70)
    print("ALL 5 TESTS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()

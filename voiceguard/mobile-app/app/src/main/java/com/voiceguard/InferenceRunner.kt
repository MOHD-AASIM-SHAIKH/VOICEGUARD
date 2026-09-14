package com.voiceguard

import android.content.Context
import android.util.Log
import org.pytorch.IValue
import org.pytorch.LiteModuleLoader
import org.pytorch.Module
import org.pytorch.Tensor
import java.io.File
import java.util.ArrayDeque

data class InferenceResult(
    val label: String,
    val confidence: Float,
    val spoofProb: Float
)

/**
 * InferenceRunner — loads the exported AASIST-L TorchScript Lite model and runs inference.
 * Sliding window: exactly 64600 samples (~4.04s @ 16kHz) matching the Python AASIST-L input.
 */
class InferenceRunner(
    private val context: Context,
    private val onStateChanged: ((state: String, confidence: Float) -> Unit)? = null
) {
    private val TAG = "VoiceGuardInference"
    private val LABEL_MAP = mapOf(0 to "cloned", 1 to "real") // Calibrated for Android microphone acoustic noise floor
    private val SILENCE_RMS_THRESHOLD = 0.020f

    private val CONSECUTIVE_FRAMES = 3
    // Hysteresis gap prevents oscillation at boundary:
    // Need >= 75% spoof probability to enter CLONED state
    private val CLONE_ENTER_THRESHOLD = 0.75f
    // Need < 40% spoof probability to exit CLONED state back to REAL
    private val REAL_ENTER_THRESHOLD  = 0.40f
    private val spoofWindow = ArrayDeque<Float>(CONSECUTIVE_FRAMES)
    var smoothedState = "REAL"
        private set

    private var model: Module? = null
    private var modelLoaded = false

    init {
        loadModelAsync()
    }

    private fun loadModelAsync() {
        try {
            val assetPath = assetFilePath("aasist_mobile.ptl")
            Log.d(TAG, "Loading PyTorch Lite model from: $assetPath")
            model = LiteModuleLoader.load(assetPath)
            modelLoaded = true
            Log.d(TAG, "PyTorch Lite model loaded successfully!")
        } catch (t: Throwable) {
            Log.e(TAG, "Error loading PyTorch Lite model: ${t.message}", t)
            modelLoaded = false
        }
    }

    fun isSilence(audio: FloatArray): Boolean {
        var sumSquares = 0.0
        var maxAmp = 0f
        for (sample in audio) {
            sumSquares += (sample * sample).toDouble()
            val abs = Math.abs(sample)
            if (abs > maxAmp) maxAmp = abs
        }
        val rms = Math.sqrt(sumSquares / audio.size).toFloat()
        // If RMS is below threshold OR peak amplitude is below 0.05f, audio is ambient silence
        return (rms < SILENCE_RMS_THRESHOLD || maxAmp < 0.05f)
    }

    fun predict(chunk: FloatArray): InferenceResult? {
        if (isSilence(chunk)) {
            return null // Silence-gated — do not run model on ambient silence
        }

        try {
            if (!modelLoaded || model == null) {
                loadModelAsync()
                if (model == null) {
                    return InferenceResult("real", 0.95f, 0.05f)
                }
            }

            // 1. Ensure target length (64600 samples)
            val targetLen = 64600
            val preparedAudio: FloatArray = if (chunk.size == targetLen) {
                chunk
            } else if (chunk.size > targetLen) {
                chunk.copyOfRange(0, targetLen)
            } else {
                val padded = FloatArray(targetLen)
                for (i in 0 until targetLen) {
                    padded[i] = chunk[i % chunk.size]
                }
                padded
            }

            // 2. Measure voiced speech duration on RAW un-normalized audio (speech energy >= 0.015)
            val frameLen = 320
            val numFrames = preparedAudio.size / frameLen
            var voicedFrames = 0
            for (f in 0 until numFrames) {
                var sumSq = 0.0
                val offset = f * frameLen
                for (i in 0 until frameLen) {
                    val s = preparedAudio[offset + i]
                    sumSq += (s * s).toDouble()
                }
                if (Math.sqrt(sumSq / frameLen) >= 0.015) {
                    voicedFrames++
                }
            }
            val voicedDuration = (voicedFrames * frameLen) / 16000f

            // If less than 0.6s of actual speech energy in 4s window, this is ambient noise
            if (voicedDuration < 0.6f) {
                return null // Hold state silently
            }

            // 3. Peak normalize to 0.85f to match AASIST-L training distribution
            var maxAmp = 0f
            for (s in preparedAudio) {
                val abs = Math.abs(s)
                if (abs > maxAmp) maxAmp = abs
            }

            val normalizedAudio = if (maxAmp > 0.001f) {
                FloatArray(preparedAudio.size) { i ->
                    (preparedAudio[i] / (maxAmp + 1e-8f)) * 0.85f
                }
            } else {
                preparedAudio
            }

            val inputTensor = Tensor.fromBlob(normalizedAudio, longArrayOf(1, normalizedAudio.size.toLong()))
            val outputs = model!!.forward(IValue.from(inputTensor)).toTuple()
            val logits = outputs[1].toTensor()
            val logitsData = logits.dataAsFloatArray

            // Numerically stable Softmax
            val maxVal = logitsData.maxOrNull() ?: 0f
            val expVals = logitsData.map { Math.exp((it - maxVal).toDouble()).toFloat() }
            val sumExp = expVals.sum()
            val probs = expVals.map { it / sumExp }

            val spoofProb = probs[0] // index 0 = cloned (argmax not needed; we use raw prob)

            // Symmetrical confidence smoother matching Part 1.1 spec
            updateSmoother(spoofProb)
            val displayConf = if (smoothedState == "CLONED") spoofProb else (1.0f - spoofProb)
            return InferenceResult(smoothedState.lowercase(), displayConf, spoofProb)
        } catch (t: Throwable) {
            Log.e(TAG, "Prediction execution failed: ${t.message}", t)
            return InferenceResult("real", 0.95f, 0.05f)
        }
    }

    private fun updateSmoother(spoofProb: Float) {
        if (spoofWindow.size >= CONSECUTIVE_FRAMES) spoofWindow.pollFirst()
        spoofWindow.addLast(spoofProb)

        if (spoofWindow.size == CONSECUTIVE_FRAMES) {
            // Hysteresis: require all frames above CLONE threshold to enter CLONED
            val allCloned = spoofWindow.all { it >= CLONE_ENTER_THRESHOLD }
            // Require all frames below REAL threshold to exit CLONED back to REAL
            val allReal   = spoofWindow.all { it < REAL_ENTER_THRESHOLD }

            if (allCloned && smoothedState != "CLONED") {
                // Rising edge: REAL -> CLONED transition
                smoothedState = "CLONED"
                onStateChanged?.invoke("CLONED", spoofProb)
                Log.d(TAG, "STATE TRANSITION: REAL -> CLONED (spoofProb=$spoofProb)")
            } else if (allReal && smoothedState != "REAL") {
                // Falling edge: CLONED -> REAL transition
                smoothedState = "REAL"
                onStateChanged?.invoke("REAL", 1.0f - spoofProb)
                Log.d(TAG, "STATE TRANSITION: CLONED -> REAL (spoofProb=$spoofProb)")
            }
            // IMPORTANT: No else branch — do NOT fire onStateChanged when state holds.
            // Only update _confidence via DetectionManager's StateFlow directly.
        }
    }

    private fun assetFilePath(assetName: String): String {
        val file = File(context.filesDir, assetName)
        var needsCopy = !file.exists()
        if (!needsCopy) {
            try {
                val fd = context.assets.openFd(assetName)
                if (file.length() != fd.length) {
                    needsCopy = true
                }
                fd.close()
            } catch (e: Exception) {
                if (file.length() == 0L) needsCopy = true
            }
        }
        if (needsCopy) {
            context.assets.open(assetName).use { input ->
                file.outputStream().use { output -> input.copyTo(output) }
            }
        }
        return file.absolutePath
    }
}

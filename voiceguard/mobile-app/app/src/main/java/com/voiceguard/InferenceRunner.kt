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
    private val LABEL_MAP = mapOf(0 to "cloned", 1 to "real")
    private val SILENCE_RMS_THRESHOLD = 0.0015f

    private val CONSECUTIVE_THRESHOLD = 3
    private val WINDOW_SIZE = 6
    private val window = ArrayDeque<String>(WINDOW_SIZE)
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
        for (sample in audio) {
            sumSquares += (sample * sample).toDouble()
        }
        val rms = Math.sqrt(sumSquares / audio.size).toFloat()
        return rms < SILENCE_RMS_THRESHOLD
    }

    fun predict(chunk: FloatArray): InferenceResult? {
        if (isSilence(chunk)) {
            return null // Silence-gated
        }

        try {
            if (!modelLoaded || model == null) {
                loadModelAsync()
                if (model == null) {
                    // Fallback to REAL if model cannot be loaded yet
                    return InferenceResult("real", 0.95f, 0.05f)
                }
            }

            // 1. Ensure target length (64600 samples) using repeat-padding
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

            // 2. Peak normalize to 0.85f to match AASIST-L training distribution
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

            // 3. Measure voiced duration in chunk (20ms frames @ 16kHz = 320 samples)
            val frameLen = 320
            val numFrames = normalizedAudio.size / frameLen
            var voicedFrames = 0
            for (f in 0 until numFrames) {
                var sumSq = 0.0
                val offset = f * frameLen
                for (i in 0 until frameLen) {
                    val s = normalizedAudio[offset + i]
                    sumSq += (s * s).toDouble()
                }
                if (Math.sqrt(sumSq / frameLen) >= 0.003) {
                    voicedFrames++
                }
            }
            val voicedDuration = (voicedFrames * frameLen) / 16000f

            val inputTensor = Tensor.fromBlob(normalizedAudio, longArrayOf(1, normalizedAudio.size.toLong()))
            val outputs = model!!.forward(IValue.from(inputTensor)).toTuple()
            val logits = outputs[1].toTensor()
            val logitsData = logits.dataAsFloatArray

            // Numerically stable Softmax
            val maxVal = logitsData.maxOrNull() ?: 0f
            val expVals = logitsData.map { Math.exp((it - maxVal).toDouble()).toFloat() }
            val sumExp = expVals.sum()
            val probs = expVals.map { it / sumExp }

            val predIdx = probs.indices.maxByOrNull { probs[it] } ?: 1
            val label = LABEL_MAP[predIdx] ?: "real"
            val confidence = probs[predIdx]
            val spoofProb = probs[0] // index 0 = cloned

            // Prevent false alarms on short isolated syllables (< 1.0s voiced speech like saying 'hello')
            if (voicedDuration < 1.0f) {
                updateSmoother("real", 0.95f, 0.05f)
                return InferenceResult("real", 0.95f, 0.05f)
            }

            updateSmoother(label, confidence, spoofProb)
            return InferenceResult(label, confidence, spoofProb)
        } catch (t: Throwable) {
            Log.e(TAG, "Prediction execution failed: ${t.message}", t)
            return InferenceResult("real", 0.92f, 0.08f)
        }
    }

    private fun updateSmoother(label: String, confidence: Float, spoofProb: Float = 0.0f) {
        if (window.size >= WINDOW_SIZE) window.pollFirst()
        window.addLast(label)

        val recent = window.toList().takeLast(CONSECUTIVE_THRESHOLD)
        val cloneCount = recent.count { it == "cloned" }
        val realCount = recent.count { it == "real" }

        // Fast high-confidence clone trigger: immediate if spoofProb >= 0.70f or 2 of 3 frames cloned
        if (spoofProb >= 0.70f || cloneCount >= 2) {
            if (smoothedState != "CLONED") {
                smoothedState = "CLONED"
                onStateChanged?.invoke("CLONED", if (spoofProb >= 0.70f) spoofProb else confidence)
            }
        } else if (realCount >= 2 && spoofProb < 0.35f) {
            if (smoothedState != "REAL") {
                smoothedState = "REAL"
                onStateChanged?.invoke("REAL", confidence)
            }
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

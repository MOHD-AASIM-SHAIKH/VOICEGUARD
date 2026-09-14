package com.voiceguard

import android.content.Context
import org.pytorch.IValue
import org.pytorch.Module
import org.pytorch.Tensor
import java.util.ArrayDeque

/**
 * InferenceRunner — loads the exported AASIST-L TorchScript model and runs inference.
 *
 * Chunking: 2.5s @ 16kHz = 40000 samples (matches Python AudioChunker)
 * Smoothing: 3 consecutive "cloned" chunks before state flips (matches Python ConfidenceSmoother)
 * Parameters MUST match the Python core-detection module exactly — do not change independently.
 *
 * Model file: assets/aasist_mobile.ptl (exported from core-detection via torch.jit.trace)
 */
class InferenceRunner(private val context: Context) {

    // Label convention matches Python detector.py: index 0 = cloned, index 1 = real
    private val LABEL_MAP = mapOf(0 to "cloned", 1 to "real")

    // Silence RMS threshold — matches Python smoother.SILENCE_RMS_THRESHOLD
    private val SILENCE_RMS_THRESHOLD = 0.01f

    // Smoothing parameters — identical to Python ConfidenceSmoother
    private val CONSECUTIVE_THRESHOLD = 3
    private val WINDOW_SIZE = 6
    private val window = ArrayDeque<String>(WINDOW_SIZE)
    private var smoothedState = "REAL"

    private val model: Module by lazy {
        Module.load(assetFilePath("aasist_mobile.ptl"))
    }

    private fun isSilence(audio: FloatArray): Boolean {
        var sumSquares = 0.0
        for (sample in audio) {
            sumSquares += (sample * sample).toDouble()
        }
        val rms = Math.sqrt(sumSquares / audio.size).toFloat()
        return rms < SILENCE_RMS_THRESHOLD
    }

    fun process(audioBlock: FloatArray) {
        if (isSilence(audioBlock)) {
            return // Skip inference and hold smoother state on silence
        }
        val inputTensor = Tensor.fromBlob(audioBlock, longArrayOf(1, audioBlock.size.toLong()))
        val outputs = model.forward(IValue.from(inputTensor)).toTuple()

        // Model returns (last_hidden, logits) — same as Python: _, out = model(x)
        val logits = outputs[1].toTensor()
        val logitsData = logits.dataAsFloatArray

        // Softmax
        val maxVal = logitsData.max()!!
        val expVals = logitsData.map { Math.exp((it - maxVal).toDouble()).toFloat() }
        val sumExp = expVals.sum()
        val probs = expVals.map { it / sumExp }

        val predIdx = probs.indices.maxByOrNull { probs[it] }!!
        val label = LABEL_MAP[predIdx] ?: "unknown"

        updateSmoother(label)
    }

    private fun updateSmoother(label: String) {
        if (window.size >= WINDOW_SIZE) window.pollFirst()
        window.addLast(label)

        val recent = window.toList().takeLast(CONSECUTIVE_THRESHOLD)
        if (recent.size == CONSECUTIVE_THRESHOLD && recent.all { it == "cloned" }) {
            if (smoothedState != "CLONED") {
                smoothedState = "CLONED"
                AlertUI.setState("CLONED")
            }
        } else if (recent.all { it == "real" }) {
            if (smoothedState != "REAL") {
                smoothedState = "REAL"
                AlertUI.setState("REAL")
            }
        }
    }

    private fun assetFilePath(assetName: String): String {
        val file = context.filesDir.resolve(assetName)
        if (!file.exists()) {
            context.assets.open(assetName).use { input ->
                file.outputStream().use { output -> input.copyTo(output) }
            }
        }
        return file.absolutePath
    }
}

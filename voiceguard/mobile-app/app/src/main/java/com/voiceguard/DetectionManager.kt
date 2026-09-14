package com.voiceguard

import android.Manifest
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.util.Log
import androidx.core.content.ContextCompat
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.concurrent.atomic.AtomicBoolean

object DetectionManager {

    private const val TAG = "VoiceGuardDetection"
    private const val SAMPLE_RATE = 16000
    private const val WINDOW_LEN = 64600  // Exact AASIST-L input (~4.04s @ 16kHz)
    private const val HOP_LEN = 16000     // 1.0s hop between sliding inferences

    private val _isProtectionActive = MutableStateFlow(true)
    val isProtectionActive: StateFlow<Boolean> = _isProtectionActive.asStateFlow()

    private val _detectionState = MutableStateFlow("REAL") // "REAL" or "CLONED"
    val detectionState: StateFlow<String> = _detectionState.asStateFlow()

    private val _confidence = MutableStateFlow(0.93f)
    val confidence: StateFlow<Float> = _confidence.asStateFlow()

    private val _elapsedSeconds = MutableStateFlow(0L)
    val elapsedSeconds: StateFlow<Long> = _elapsedSeconds.asStateFlow()

    private val _callChannel = MutableStateFlow(CallChannel.NONE)
    val callChannel: StateFlow<CallChannel> = _callChannel.asStateFlow()

    private val _callContextDescription = MutableStateFlow(
        "WhatsApp Voice Call · Protected by VoiceGuard on-device model + On-Chain Interceptor"
    )
    val callContextDescription: StateFlow<String> = _callContextDescription.asStateFlow()

    private var inferenceRunner: InferenceRunner? = null
    private var appContext: Context? = null
    private var callDetector: CallDetector? = null

    private val isRecording = AtomicBoolean(false)
    private var recordJob: Job? = null
    private var timerJob: Job? = null

    private val coroutineExceptionHandler = CoroutineExceptionHandler { _, throwable ->
        Log.e(TAG, "Uncaught Coroutine Error: ${throwable.message}", throwable)
    }

    private val scope = CoroutineScope(Dispatchers.Default + SupervisorJob() + coroutineExceptionHandler)

    fun init(context: Context) {
        if (appContext != null) {
            if (!_isProtectionActive.value) {
                toggleProtection()
            }
            return
        }
        appContext = context.applicationContext
        val ctx = appContext ?: return

        try {
            inferenceRunner = InferenceRunner(ctx) { newState, conf ->
                _detectionState.value = newState
                _confidence.value = conf
                if (newState == "CLONED") {
                    triggerVibration()
                }
            }
        } catch (t: Throwable) {
            Log.e(TAG, "InferenceRunner init failed: ${t.message}", t)
        }

        // Initialize and start native CallDetector
        try {
            callDetector = CallDetector(ctx) { channel, isActive, description ->
                _callChannel.value = channel
                if (isActive) {
                    _callContextDescription.value = "$description\nProtected by VoiceGuard on-device model + On-Chain Interceptor"
                    if (!_isProtectionActive.value) {
                        startListening()
                    }
                } else {
                    _callContextDescription.value = "Active · Ready to protect calls (Cellular / WhatsApp / VoIP)\nProtected by VoiceGuard on-device model + On-Chain Interceptor"
                }
            }
            callDetector?.startMonitoring()
        } catch (t: Throwable) {
            Log.w(TAG, "CallDetector initialization error: ${t.message}")
        }

        startListening()
    }

    fun startListening() {
        if (recordJob?.isActive == true) return
        _isProtectionActive.value = true

        // Elevate process via Foreground Service with FOREGROUND_SERVICE_TYPE_MICROPHONE
        appContext?.let { ctx ->
            try {
                val serviceIntent = Intent(ctx, MicCaptureService::class.java).apply {
                    action = MicCaptureService.ACTION_START
                }
                ContextCompat.startForegroundService(ctx, serviceIntent)
            } catch (t: Throwable) {
                Log.w(TAG, "Failed to start MicCaptureService foreground service: ${t.message}")
            }
        }

        // Timer job
        timerJob?.cancel()
        timerJob = scope.launch {
            while (isActive) {
                delay(1000)
                if (_isProtectionActive.value) {
                    _elapsedSeconds.value += 1
                }
            }
        }

        // Audio recording loop
        recordJob = scope.launch(Dispatchers.IO) {
            isRecording.set(true)
            val ctx = appContext
            if (ctx != null) {
                val hasPerm = ContextCompat.checkSelfPermission(
                    ctx,
                    Manifest.permission.RECORD_AUDIO
                ) == PackageManager.PERMISSION_GRANTED
                if (!hasPerm) {
                    Log.w(TAG, "RECORD_AUDIO permission not yet granted. Waiting...")
                    isRecording.set(false)
                    return@launch
                }
            }

            val minBufSize = AudioRecord.getMinBufferSize(
                SAMPLE_RATE,
                AudioFormat.CHANNEL_IN_MONO,
                AudioFormat.ENCODING_PCM_16BIT
            )

            var recorder: AudioRecord? = null
            try {
                recorder = try {
                    AudioRecord(
                        MediaRecorder.AudioSource.VOICE_RECOGNITION,
                        SAMPLE_RATE,
                        AudioFormat.CHANNEL_IN_MONO,
                        AudioFormat.ENCODING_PCM_16BIT,
                        maxOf(minBufSize, HOP_LEN * 4)
                    )
                } catch (t: Throwable) {
                    Log.w(TAG, "VOICE_RECOGNITION failed, fallback to MIC: ${t.message}")
                    null
                }

                if (recorder == null || recorder.state != AudioRecord.STATE_INITIALIZED) {
                    recorder?.release()
                    recorder = AudioRecord(
                        MediaRecorder.AudioSource.MIC,
                        SAMPLE_RATE,
                        AudioFormat.CHANNEL_IN_MONO,
                        AudioFormat.ENCODING_PCM_16BIT,
                        maxOf(minBufSize, HOP_LEN * 4)
                    )
                }

                if (recorder.state != AudioRecord.STATE_INITIALIZED) {
                    Log.e(TAG, "AudioRecord failed to initialize.")
                    return@launch
                }

                val readBuffer = ShortArray(4000) // 0.25s blocks
                var sampleBuffer = FloatArray(0)

                recorder.startRecording()
                Log.i(TAG, "Audio recording started successfully.")

                while (isActive && isRecording.get()) {
                    if (!_isProtectionActive.value) {
                        sampleBuffer = FloatArray(0)
                        delay(300)
                        continue
                    }

                    val read = recorder.read(readBuffer, 0, readBuffer.size)
                    if (read > 0) {
                        val newFloats = FloatArray(read) { readBuffer[it] / 32768f }
                        sampleBuffer = sampleBuffer + newFloats

                        // Cap buffer to prevent unbounded memory growth
                        if (sampleBuffer.size > WINDOW_LEN * 3) {
                            sampleBuffer = sampleBuffer.copyOfRange(sampleBuffer.size - WINDOW_LEN * 2, sampleBuffer.size)
                        }

                        // Part 1.2: Short utterances are not isolated & repeat-padded.
                        // They accumulate in the rolling 4.04s buffer of contiguous real audio.
                        while (sampleBuffer.size >= WINDOW_LEN) {
                            val window = sampleBuffer.copyOfRange(0, WINDOW_LEN)
                            sampleBuffer = sampleBuffer.copyOfRange(HOP_LEN, sampleBuffer.size)

                            val res = inferenceRunner?.predict(window)
                            if (res != null) {
                                _confidence.value = res.confidence
                            }
                        }
                    } else if (read < 0) {
                        Log.w(TAG, "AudioRecord read returned error code: $read")
                        delay(100)
                    }
                }
            } catch (t: Throwable) {
                Log.e(TAG, "Audio recording loop error: ${t.message}", t)
            } finally {
                try {
                    recorder?.stop()
                    recorder?.release()
                } catch (ignored: Throwable) {}
                Log.i(TAG, "Audio recording stopped.")
            }
        }
    }

    fun stopListening() {
        _isProtectionActive.value = false
        isRecording.set(false)
        recordJob?.cancel()
        recordJob = null

        // Stop foreground service
        appContext?.let { ctx ->
            try {
                val serviceIntent = Intent(ctx, MicCaptureService::class.java).apply {
                    action = MicCaptureService.ACTION_STOP
                }
                ctx.startService(serviceIntent)
            } catch (t: Throwable) {
                Log.w(TAG, "Failed to stop MicCaptureService: ${t.message}")
            }
        }
    }

    fun toggleProtection() {
        if (_isProtectionActive.value) {
            Log.d(TAG, "Protection paused by user.")
            stopListening()
        } else {
            Log.d(TAG, "Protection resumed by user.")
            startListening()
        }
    }

    fun triggerVibration() {
        appContext?.let { ctx ->
            try {
                if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                    val vibratorManager = ctx.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
                    vibratorManager?.defaultVibrator?.vibrate(
                        VibrationEffect.createWaveform(longArrayOf(0, 300, 150, 300), -1)
                    )
                } else {
                    @Suppress("DEPRECATION")
                    val vibrator = ctx.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
                    vibrator?.vibrate(
                        VibrationEffect.createWaveform(longArrayOf(0, 300, 150, 300), -1)
                    )
                }
            } catch (ignored: Throwable) {}
        }
    }

    // Demo / Simulation triggers
    fun simulateClone(conf: Float = 0.94f) {
        _confidence.value = conf
        _detectionState.value = "CLONED"
        triggerVibration()
    }

    fun simulateReal() {
        _detectionState.value = "REAL"
    }
}

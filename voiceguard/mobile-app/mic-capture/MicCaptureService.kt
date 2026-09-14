package com.voiceguard

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.Service
import android.content.Intent
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import android.os.IBinder
import kotlin.concurrent.thread

/**
 * MicCaptureService — Foreground Service using AudioRecord with RECORD_AUDIO permission.
 *
 * Android has blocked third-party raw call audio via Accessibility API since May 2022.
 * The only Play-Store-compliant approach is speakerphone + microphone capture via RECORD_AUDIO.
 *
 * Audio config:
 * - Sample rate: 16000 Hz (matches AASIST-L input)
 * - Channel: MONO
 * - Encoding: 16-bit PCM
 * - Block size: 40000 samples (2.5s @ 16kHz — matches AudioChunker's chunk_len)
 */
class MicCaptureService : Service() {

    private val SAMPLE_RATE = 16000
    private val CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO
    private val AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT
    private val BLOCK_SIZE = 40000  // 2.5s * 16000Hz — matches Python AudioChunker chunk_len

    private var isRunning = false
    private lateinit var inferenceRunner: InferenceRunner

    override fun onCreate() {
        super.onCreate()
        inferenceRunner = InferenceRunner(this)
        startForeground(1, buildNotification())
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        isRunning = true
        thread { captureLoop() }
        return START_STICKY
    }

    private fun captureLoop() {
        val minBufSize = AudioRecord.getMinBufferSize(SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT)
        val recorder = AudioRecord(
            MediaRecorder.AudioSource.MIC,
            SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT,
            maxOf(minBufSize, BLOCK_SIZE * 2)
        )
        val buffer = ShortArray(BLOCK_SIZE)
        recorder.startRecording()
        while (isRunning) {
            val read = recorder.read(buffer, 0, BLOCK_SIZE)
            if (read > 0) {
                // Convert to float[-1, 1] and pass to inference
                val floatBuffer = FloatArray(read) { buffer[it] / 32768f }
                inferenceRunner.process(floatBuffer)
            }
        }
        recorder.stop()
        recorder.release()
    }

    private fun buildNotification(): Notification {
        val channelId = "voiceguard_protection"
        val channel = NotificationChannel(channelId, "VoiceGuard Protection", NotificationManager.IMPORTANCE_LOW)
        getSystemService(NotificationManager::class.java)?.createNotificationChannel(channel)
        return Notification.Builder(this, channelId)
            .setContentTitle("VoiceGuard Active")
            .setContentText("Monitoring for voice cloning...")
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .build()
    }

    override fun onDestroy() {
        isRunning = false
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}

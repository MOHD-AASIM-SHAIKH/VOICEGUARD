package com.voiceguard

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat

/**
 * MicCaptureService — Foreground Service with microphone type.
 *
 * Android strictly throttles or cuts off background microphone access when an app loses focus
 * unless an explicit Foreground Service with FOREGROUND_SERVICE_TYPE_MICROPHONE is active.
 *
 * This service provides:
 * 1. An ongoing persistent notification informing the user that VoiceGuard clone monitoring is active.
 * 2. Foreground process elevation so on-device audio inference continues during cellular or VoIP calls.
 * 3. Clean lifecycle controls (ACTION_START / ACTION_STOP).
 */
class MicCaptureService : Service() {

    companion object {
        const val CHANNEL_ID = "voiceguard_protection"
        const val NOTIFICATION_ID = 1001
        const val ACTION_START = "com.voiceguard.action.START"
        const val ACTION_STOP = "com.voiceguard.action.STOP"
        private const val TAG = "VoiceGuardMicService"
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            Log.i(TAG, "Received ACTION_STOP. Removing foreground notification.")
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
            return START_NOT_STICKY
        }

        try {
            val notification = buildNotification()
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val serviceType = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
                    ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
                } else {
                    0
                }
                startForeground(NOTIFICATION_ID, notification, serviceType)
            } else {
                startForeground(NOTIFICATION_ID, notification)
            }
            Log.i(TAG, "MicCaptureService started as Foreground Service (MICROPHONE).")
        } catch (t: Throwable) {
            Log.e(TAG, "Failed to start foreground service: ${t.message}", t)
        }

        return START_STICKY
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "VoiceGuard Protection Service",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Real-time voice clone monitoring and fraud prevention"
                setShowBadge(false)
            }
            val manager = getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager
            manager?.createNotificationChannel(channel)
        }
    }

    private fun buildNotification(): Notification {
        val launchIntent = Intent(this, MainActivity::class.java).apply {
            this.flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            launchIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, CHANNEL_ID)
            .setContentTitle("VoiceGuard Protection Active")
            .setContentText("Monitoring live calls for synthetic voice clones...")
            .setSmallIcon(android.R.drawable.ic_lock_lock)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .setCategory(NotificationCompat.CATEGORY_SERVICE)
            .build()
    }

    override fun onDestroy() {
        Log.i(TAG, "MicCaptureService destroyed.")
        super.onDestroy()
    }

    override fun onBind(intent: Intent?): IBinder? = null
}

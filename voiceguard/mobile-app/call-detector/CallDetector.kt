package com.voiceguard

import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.telephony.PhoneStateListener
import android.telephony.TelephonyCallback
import android.telephony.TelephonyManager
import android.util.Log
import androidx.core.content.ContextCompat

/**
 * Supported call channels for VoiceGuard monitoring.
 */
enum class CallChannel {
    NONE,
    CELLULAR,
    VOIP
}

/**
 * CallDetector — Native phone call and VoIP state detection.
 *
 * - Native cellular calls: registers TelephonyCallback (API 31+) or PhoneStateListener (API < 31)
 *   to detect CALL_STATE_OFFHOOK (call answered/active) and CALL_STATE_IDLE (call ended).
 * - VoIP calls (WhatsApp / Zoom / Google Meet): provides manual or intent-based triggers
 *   since Android does not expose a unified public VoIP interception API.
 *
 * Both pathways seamlessly drive DetectionManager and MicCaptureService.
 */
class CallDetector(
    private val context: Context,
    private val onCallStateChanged: (channel: CallChannel, isActive: Boolean, description: String) -> Unit
) {

    // Secondary constructor for single-callback convenience
    constructor(context: Context, onCallActive: () -> Unit) : this(
        context,
        { _, isActive, _ -> if (isActive) onCallActive() }
    )

    private val TAG = "VoiceGuardCallDetector"
    private val telephonyManager = context.getSystemService(Context.TELEPHONY_SERVICE) as? TelephonyManager
    private var telephonyCallback: Any? = null
    @Suppress("DEPRECATION")
    private var phoneStateListener: PhoneStateListener? = null
    private var isMonitoring = false

    fun startMonitoring() {
        if (isMonitoring || telephonyManager == null) return

        val hasPermission = ContextCompat.checkSelfPermission(
            context,
            android.Manifest.permission.READ_PHONE_STATE
        ) == PackageManager.PERMISSION_GRANTED

        if (!hasPermission) {
            Log.w(TAG, "READ_PHONE_STATE permission not granted. Native cellular monitoring disabled.")
            return
        }

        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                val callback = object : TelephonyCallback(), TelephonyCallback.CallStateListener {
                    override fun onCallStateChanged(state: Int) {
                        handleState(state)
                    }
                }
                telephonyManager.registerTelephonyCallback(context.mainExecutor, callback)
                telephonyCallback = callback
            } else {
                @Suppress("DEPRECATION")
                val listener = object : PhoneStateListener() {
                    @Deprecated("Deprecated in Java")
                    override fun onCallStateChanged(state: Int, phoneNumber: String?) {
                        handleState(state)
                    }
                }
                @Suppress("DEPRECATION")
                telephonyManager.listen(listener, PhoneStateListener.LISTEN_CALL_STATE)
                phoneStateListener = listener
            }
            isMonitoring = true
            Log.i(TAG, "CallDetector registered successfully.")
        } catch (e: SecurityException) {
            Log.w(TAG, "SecurityException registering CallDetector: ${e.message}")
        } catch (t: Throwable) {
            Log.e(TAG, "Unexpected error registering CallDetector: ${t.message}", t)
        }
    }

    private fun handleState(state: Int) {
        when (state) {
            TelephonyManager.CALL_STATE_OFFHOOK -> {
                Log.i(TAG, "Call State: OFFHOOK (Active Cellular Call)")
                onCallStateChanged(
                    CallChannel.CELLULAR,
                    true,
                    "Cellular Phone Call Active"
                )
            }
            TelephonyManager.CALL_STATE_RINGING -> {
                Log.i(TAG, "Call State: RINGING")
                onCallStateChanged(
                    CallChannel.CELLULAR,
                    false,
                    "Incoming Cellular Call Ringing"
                )
            }
            TelephonyManager.CALL_STATE_IDLE -> {
                Log.i(TAG, "Call State: IDLE")
                onCallStateChanged(
                    CallChannel.NONE,
                    false,
                    "Standby · Monitoring enabled"
                )
            }
        }
    }

    /**
     * Called when a VoIP call (WhatsApp, Meet, Zoom) is active or initiated manually.
     */
    fun startProtectionManually(serviceName: String = "WhatsApp Voice Call") {
        Log.i(TAG, "Manual Protection Triggered: $serviceName")
        onCallStateChanged(
            CallChannel.VOIP,
            true,
            "$serviceName Active"
        )
    }

    fun stopMonitoring() {
        if (!isMonitoring || telephonyManager == null) return
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
                (telephonyCallback as? TelephonyCallback)?.let {
                    telephonyManager.unregisterTelephonyCallback(it)
                }
                telephonyCallback = null
            } else {
                @Suppress("DEPRECATION")
                phoneStateListener?.let {
                    telephonyManager.listen(it, PhoneStateListener.LISTEN_NONE)
                }
                phoneStateListener = null
            }
            isMonitoring = false
            Log.i(TAG, "CallDetector unregistered.")
        } catch (t: Throwable) {
            Log.e(TAG, "Error stopping CallDetector: ${t.message}", t)
        }
    }
}

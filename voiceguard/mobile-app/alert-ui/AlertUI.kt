package com.voiceguard

import android.animation.ValueAnimator
import android.app.Activity
import android.content.Intent
import android.graphics.Color
import android.net.Uri
import android.os.Bundle
import android.os.VibrationEffect
import android.os.Vibrator
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.view.animation.AccelerateDecelerateInterpolator
import android.widget.Button
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView
import java.net.URLEncoder
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/**
 * AlertUI — VoiceGuard detection screen.
 *
 * Design spec (from UI prompt):
 *   - White background (#FFFFFF), black text (#111111), gray secondary (#888888)
 *   - ONE accent only: green (#2E7D4F) for REAL, red (#C0392B) for CLONE DETECTED
 *   - Flat design — no gradients, no shadows, no decorative elements
 *   - Rounded corners 8dp, generous whitespace
 *   - Large bold state word centered, waveform below, one primary + one secondary button
 *   - State transition: smooth fade/alpha animation only — no bounce or flash
 */
class AlertUI : Activity() {

    // ── Design tokens ─────────────────────────────────────────────────────────
    private val colorBg          = Color.parseColor("#FFFFFF")
    private val colorTextPrimary = Color.parseColor("#111111")
    private val colorTextGray    = Color.parseColor("#888888")
    private val colorTextLight   = Color.parseColor("#BBBBBB")
    private val colorBorder      = Color.parseColor("#DDDDDD")
    private val colorGreen       = Color.parseColor("#2E7D4F")   // REAL
    private val colorRed         = Color.parseColor("#C0392B")   // CLONE DETECTED

    // ── Views ─────────────────────────────────────────────────────────────────
    private lateinit var stateLabel:    TextView
    private lateinit var confLabel:     TextView
    private lateinit var statusLabel:   TextView
    private lateinit var hangUpBtn:     Button
    private lateinit var reportBtn:     Button
    private lateinit var hangUpWrapper: View

    private var lastState      = "REAL"
    private var lastConfidence = 0f

    companion object {
        var currentActivity: AlertUI? = null
        fun setState(state: String, confidence: Float = 0f) {
            currentActivity?.runOnUiThread {
                currentActivity?.updateState(state, confidence)
            }
        }
    }

    // ── Lifecycle ──────────────────────────────────────────────────────────────
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        currentActivity = this

        // Keep screen on during monitoring
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        buildUI()
    }

    override fun onDestroy() {
        currentActivity = null
        super.onDestroy()
    }

    // ── UI construction ────────────────────────────────────────────────────────
    private fun buildUI() {
        val dp = resources.displayMetrics.density

        fun Int.dp() = (this * dp).toInt()

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor(colorBg)
            setPadding(32.dp(), 0, 32.dp(), 0)
        }

        // ── Top bar ───────────────────────────────────────────────────────────
        val topBar = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, 24.dp(), 0, 0)
        }

        val titleLabel = TextView(this).apply {
            text = "Voice Guard"
            textSize = 15f
            setTextColor(colorTextPrimary)
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)
        }

        statusLabel = TextView(this).apply {
            text = "Loading…"
            textSize = 12f
            setTextColor(colorTextGray)
        }

        topBar.addView(titleLabel)
        topBar.addView(statusLabel)
        root.addView(topBar)

        // ── Divider ───────────────────────────────────────────────────────────
        root.addView(View(this).apply {
            setBackgroundColor(colorBorder)
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 1.dp()
            ).apply { setMargins(0, 16.dp(), 0, 0) }
        })

        // ── State label ───────────────────────────────────────────────────────
        stateLabel = TextView(this).apply {
            text = "REAL"
            textSize = 52f
            setTextColor(colorGreen)
            gravity = Gravity.CENTER
            typeface = android.graphics.Typeface.DEFAULT_BOLD
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { topMargin = 60.dp() }
        }
        root.addView(stateLabel)

        // ── Confidence label ──────────────────────────────────────────────────
        confLabel = TextView(this).apply {
            text = "Confidence: —"
            textSize = 14f
            setTextColor(colorTextGray)
            gravity = Gravity.CENTER
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { topMargin = 6.dp() }
        }
        root.addView(confLabel)

        // ── Spacer ────────────────────────────────────────────────────────────
        root.addView(View(this).apply {
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f)
        })

        // ── Monitoring status ─────────────────────────────────────────────────
        val monitorLabel = TextView(this).apply {
            text = "Monitoring active"
            textSize = 12f
            setTextColor(colorTextLight)
            gravity = Gravity.CENTER
        }
        root.addView(monitorLabel)

        // ── Divider ───────────────────────────────────────────────────────────
        root.addView(View(this).apply {
            setBackgroundColor(colorBorder)
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT, 1.dp()
            ).apply { setMargins(0, 20.dp(), 0, 0) }
        })

        // ── Buttons row ───────────────────────────────────────────────────────
        val btnRow = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            setPadding(0, 16.dp(), 0, 28.dp())
        }

        // Hang Up — solid black, shown only when CLONED
        hangUpBtn = Button(this).apply {
            text = "Hang Up"
            textSize = 13f
            setTextColor(colorBg)
            setBackgroundColor(colorTextPrimary)
            // 8dp rounded corners via background drawable set below
            stateListAnimator = null
            elevation = 0f
            layoutParams = LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f
            ).apply { setMargins(0, 0, 8.dp(), 0) }
            setOnClickListener { onHangUp() }
        }
        hangUpWrapper = hangUpBtn
        hangUpBtn.visibility = View.GONE

        // Report — outlined black
        reportBtn = Button(this).apply {
            text = "Report to Chakshu"
            textSize = 13f
            setTextColor(colorTextPrimary)
            setBackgroundColor(colorBg)
            stateListAnimator = null
            elevation = 0f
            layoutParams = LinearLayout.LayoutParams(
                0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f
            )
            setOnClickListener { onReport() }
        }

        btnRow.addView(hangUpBtn)
        btnRow.addView(reportBtn)
        root.addView(btnRow)

        setContentView(root)
    }

    // ── State update with fade animation ──────────────────────────────────────
    fun updateState(state: String, confidence: Float = 0f) {
        lastState      = state
        lastConfidence = confidence

        // Smooth fade transition on state word only
        val targetColor = if (state == "CLONED") colorRed else colorGreen
        val targetText  = if (state == "CLONED") "CLONE DETECTED" else "REAL"

        ValueAnimator.ofFloat(1f, 0f, 1f).apply {
            duration     = 300
            interpolator = AccelerateDecelerateInterpolator()
            addUpdateListener { anim ->
                val alpha = anim.animatedValue as Float
                stateLabel.alpha = alpha
                if (alpha < 0.05f) {
                    stateLabel.text = targetText
                    stateLabel.setTextColor(targetColor)
                }
            }
            start()
        }

        confLabel.text = "Confidence: ${(confidence * 100).toInt()}%"

        if (state == "CLONED") {
            hangUpBtn.visibility = View.VISIBLE
            statusLabel.text = "Clone voice detected"
            vibrate()
        } else {
            hangUpBtn.visibility = View.GONE
            statusLabel.text = "Monitoring"
        }
    }

    // ── Actions ───────────────────────────────────────────────────────────────
    private fun onHangUp() {
        statusLabel.text = "Hang up now"
    }

    private fun onReport() {
        val ts   = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).format(Date())
        val conf = String.format(Locale.US, "%.2f", lastConfidence)
        val url  = "https://sancharsaathi.gov.in/sfc/?" +
                   "reportedAt=${URLEncoder.encode(ts, "UTF-8")}" +
                   "&callType=voip" +
                   "&confidence=$conf"
        startActivity(Intent(Intent.ACTION_VIEW, Uri.parse(url)))
        statusLabel.text = "Report opened"
    }

    private fun vibrate() {
        val vib = getSystemService(Vibrator::class.java)
        vib?.vibrate(VibrationEffect.createOneShot(400, VibrationEffect.DEFAULT_AMPLITUDE))
    }
}

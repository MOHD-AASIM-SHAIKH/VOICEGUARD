package com.voiceguard.ui.screens

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.voiceguard.ui.components.ButtonVariant
import com.voiceguard.ui.components.DetectionState
import com.voiceguard.ui.components.StatusIndicator
import com.voiceguard.ui.components.VoiceGuardButton
import com.voiceguard.ui.theme.VoiceGuardMotion
import com.voiceguard.ui.theme.VoiceGuardTheme

/**
 * Screen 2 — Clone Detected (Alert)
 * Layout:
 * - Full-bleed background tint: --color-state-clone-bg
 * - StatusIndicator: state = CLONE, "CLONE DETECTED", caption "Detected just now"
 * - space-6 spacing
 * - Button: Hang Up (primary, full-width)
 * - space-3 spacing
 * - Button: Report (secondary/outlined, full-width)
 * - Motion: 180ms ease-out cross-fade
 */
@Composable
fun Screen2CloneAlert(
    onHangUp: () -> Unit,
    onReport: () -> Unit,
    modifier: Modifier = Modifier
) {
    // 180ms cross-fade into state-clone-bg
    val animatedBgColor by animateColorAsState(
        targetValue = VoiceGuardTheme.colors.stateCloneBg,
        animationSpec = tween(
            durationMillis = VoiceGuardMotion.TRANSITION_DURATION_MS,
            easing = FastOutSlowInEasing
        ),
        label = "AlertBgCrossFade"
    )

    Box(
        modifier = modifier
            .fillMaxSize()
            .background(animatedBgColor),
        contentAlignment = Alignment.Center
    ) {
        Column(
            modifier = Modifier
                .widthIn(max = 480.dp)
                .fillMaxSize()
                .padding(
                    start = VoiceGuardTheme.spacing.space5,
                    end = VoiceGuardTheme.spacing.space5,
                    top = VoiceGuardTheme.spacing.space7,
                    bottom = VoiceGuardTheme.spacing.space6
                ),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // StatusIndicator (CLONE state)
            StatusIndicator(
                state = DetectionState.CLONE,
                caption = "Detected just now"
            )

            Spacer(modifier = Modifier.weight(1f))

            // Button: Hang Up (primary, full-width)
            VoiceGuardButton(
                text = "Hang Up",
                variant = ButtonVariant.PRIMARY,
                onClick = onHangUp,
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space3))

            // Button: Report (secondary/outlined, full-width)
            VoiceGuardButton(
                text = "Report",
                variant = ButtonVariant.SECONDARY,
                onClick = onReport,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

package com.voiceguard.ui.screens

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.FastOutSlowInEasing
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.voiceguard.ui.components.ButtonVariant
import com.voiceguard.ui.components.CircularConfidenceMeter
import com.voiceguard.ui.components.DetectionState
import com.voiceguard.ui.components.VoiceGuardButton
import com.voiceguard.ui.components.VoiceGuardCard
import com.voiceguard.ui.theme.VoiceGuardMotion
import com.voiceguard.ui.theme.VoiceGuardTheme

/**
 * Screen 2 — Clone Detected (Alert)
 * Features Circular Radial Confidence Meter in alarm red,
 * on-chain transaction lock context card, and actions to Hang Up or Notarize.
 */
@Composable
fun Screen2CloneAlert(
    onHangUp: () -> Unit,
    onReport: () -> Unit,
    confidence: Float = 0.94f,
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
                    top = VoiceGuardTheme.spacing.space6,
                    bottom = VoiceGuardTheme.spacing.space5
                ),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Circular Radial Confidence Meter (CLONE state - Red)
            CircularConfidenceMeter(
                state = DetectionState.CLONE,
                confidence = confidence,
                caption = "High-Risk AI Audio"
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space5))

            // Blockchain Interceptor Context
            VoiceGuardCard {
                Text(
                    text = "Smart Contract Interceptor",
                    style = VoiceGuardTheme.typography.subtitle.copy(color = VoiceGuardTheme.colors.stateClone)
                )
                Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space1))
                Text(
                    text = "TransactionAuthorizer.sol activated:\nPending banking transfers and high-value approvals automatically locked on-chain.",
                    style = VoiceGuardTheme.typography.body.copy(color = VoiceGuardTheme.colors.textSecondary)
                )
            }

            Spacer(modifier = Modifier.weight(1f))

            // Button: Hang Up (primary, full-width)
            VoiceGuardButton(
                text = "Hang Up Immediately",
                variant = ButtonVariant.PRIMARY,
                onClick = onHangUp,
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space3))

            // Button: Report & Notarize (secondary/outlined, full-width)
            VoiceGuardButton(
                text = "Report & Notarize on Blockchain",
                variant = ButtonVariant.SECONDARY,
                onClick = onReport,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

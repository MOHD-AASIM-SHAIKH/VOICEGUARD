package com.voiceguard.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.voiceguard.ui.components.ButtonVariant
import com.voiceguard.ui.components.DetectionState
import com.voiceguard.ui.components.StatusIndicator
import com.voiceguard.ui.components.VoiceGuardButton
import com.voiceguard.ui.components.VoiceGuardCard
import com.voiceguard.ui.theme.VoiceGuardTheme

/**
 * Screen 1 — Idle / Listening
 * Layout:
 * - space-7 top padding
 * - StatusIndicator: state = REAL, caption "Listening…"
 * - space-6 spacing
 * - Card: call context
 * - flex-grow spacer
 * - Button: Stop Protection (secondary/outlined, bottom, space-6 margin)
 */
@Composable
fun Screen1Listening(
    onStopProtection: () -> Unit,
    modifier: Modifier = Modifier
) {
    Box(
        modifier = modifier
            .fillMaxSize()
            .background(VoiceGuardTheme.colors.bg),
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
            // 1. StatusIndicator (state = REAL, caption "Listening…")
            StatusIndicator(
                state = DetectionState.REAL,
                caption = "Listening…"
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space6))

            // 2. Card: call context
            VoiceGuardCard {
                Text(
                    text = "Call Context",
                    style = VoiceGuardTheme.typography.subtitle.copy(color = VoiceGuardTheme.colors.textPrimary)
                )
                Text(
                    text = "WhatsApp Voice Call · 02:41\nProtected by VoiceGuard on-device model",
                    style = VoiceGuardTheme.typography.body.copy(color = VoiceGuardTheme.colors.textSecondary)
                )
            }

            // Flex-grow spacer
            Spacer(modifier = Modifier.weight(1f))

            // 3. Button: Stop Protection (secondary/outlined, bottom)
            VoiceGuardButton(
                text = "Stop Protection",
                variant = ButtonVariant.SECONDARY,
                onClick = onStopProtection,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

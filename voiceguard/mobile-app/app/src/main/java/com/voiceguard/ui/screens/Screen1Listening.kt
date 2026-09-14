package com.voiceguard.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.voiceguard.ui.components.BlockchainBadge
import com.voiceguard.ui.components.ButtonVariant
import com.voiceguard.ui.components.CircularConfidenceMeter
import com.voiceguard.ui.components.DetectionState
import com.voiceguard.ui.components.VoiceGuardButton
import com.voiceguard.ui.components.VoiceGuardCard
import com.voiceguard.ui.theme.VoiceGuardTheme

/**
 * Screen 1 — Idle / Active Listening
 * Features Circular Radial Confidence Meter, On-Chain Blockchain Notary badge,
 * Call Context card, Novelty Feature Tray (Guarded Tx & Evidence Ledger),
 * and dynamic Stop/Resume Protection toggle.
 */
@Composable
fun Screen1Listening(
    isProtectionActive: Boolean = true,
    confidence: Float = 0.94f,
    elapsedSeconds: Long = 0L,
    callContextDescription: String = "WhatsApp Voice Call · Protected by VoiceGuard on-device model + On-Chain Interceptor",
    onToggleProtection: () -> Unit,
    onSimulateClone: () -> Unit,
    onOpenApproval: () -> Unit,
    onOpenHistory: () -> Unit,
    modifier: Modifier = Modifier
) {
    val mins = elapsedSeconds / 60
    val secs = elapsedSeconds % 60
    val timeFormatted = String.format("%02d:%02d", mins, secs)

    val indicatorState = if (isProtectionActive) DetectionState.REAL else DetectionState.PAUSED
    val captionText = if (isProtectionActive) "Active · $timeFormatted" else "Protection paused"
    val callContextSub = if (isProtectionActive) {
        if (callContextDescription.contains("\n")) {
            val parts = callContextDescription.split("\n", limit = 2)
            "${parts[0]} · $timeFormatted\n${parts[1]}"
        } else {
            "$callContextDescription · $timeFormatted"
        }
    } else {
        "Protection is currently paused\nTap Resume Protection below to activate on-device monitoring"
    }

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
                    top = VoiceGuardTheme.spacing.space6,
                    bottom = VoiceGuardTheme.spacing.space5
                ),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            // Blockchain Trust Badge
            BlockchainBadge(text = "⛓️ Polygon Amoy Notary Active")

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space4))

            // 1. Circular Radial Confidence Meter
            CircularConfidenceMeter(
                state = indicatorState,
                confidence = confidence,
                caption = captionText
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space5))

            // 2. Card: Call Context
            VoiceGuardCard {
                Text(
                    text = "Call Context",
                    style = VoiceGuardTheme.typography.subtitle.copy(color = VoiceGuardTheme.colors.textPrimary)
                )
                Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space1))
                Text(
                    text = callContextSub,
                    style = VoiceGuardTheme.typography.body.copy(color = VoiceGuardTheme.colors.textSecondary)
                )
            }

            // Flex-grow spacer
            Spacer(modifier = Modifier.weight(1f))

            // Novelty Features Action Tray
            Text(
                text = "Novelty Features & Simulation",
                style = VoiceGuardTheme.typography.caption.copy(color = VoiceGuardTheme.colors.textSecondary),
                modifier = Modifier.align(Alignment.Start)
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space1))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                TextButton(onClick = onSimulateClone) {
                    Text(
                        text = "Simulate Clone",
                        style = VoiceGuardTheme.typography.caption.copy(color = VoiceGuardTheme.colors.stateClone)
                    )
                }
                TextButton(onClick = onOpenApproval) {
                    Text(
                        text = "Guarded Tx",
                        style = VoiceGuardTheme.typography.caption.copy(color = VoiceGuardTheme.colors.textPrimary)
                    )
                }
                TextButton(onClick = onOpenHistory) {
                    Text(
                        text = "Blockchain Ledger",
                        style = VoiceGuardTheme.typography.caption.copy(color = VoiceGuardTheme.colors.textSecondary)
                    )
                }
            }

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space2))

            // 3. Button: Stop/Resume Protection (toggles state)
            VoiceGuardButton(
                text = if (isProtectionActive) "Stop Protection" else "Resume Protection",
                variant = if (isProtectionActive) ButtonVariant.SECONDARY else ButtonVariant.PRIMARY,
                onClick = onToggleProtection,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

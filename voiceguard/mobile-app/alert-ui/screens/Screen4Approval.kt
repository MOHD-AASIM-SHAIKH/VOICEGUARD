package com.voiceguard.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.voiceguard.ui.components.ButtonVariant
import com.voiceguard.ui.components.VoiceGuardButton
import com.voiceguard.ui.components.VoiceGuardCard
import com.voiceguard.ui.theme.VoiceGuardTheme

/**
 * Screen 4 — Trusted-Device Transaction Approval (Tier 2)
 * Layout:
 * - Label: "Approval requested" (text-label, color-text-secondary)
 * - space-3 (12dp)
 * - Amount: "₹50,00,000" (text-display: 40sp, 700)
 * - To: "ABC Industries" (text-subtitle: 18sp, 600)
 * - space-7 (48dp) — more generous whitespace
 * - Card: risk context ("New recipient · Step-up approval required")
 * - space-7 (48dp)
 * - Biometric prompt (system-native style)
 * - space-7 (48dp)
 * - Button: Approve (primary, full-width)
 * - space-3 (12dp)
 * - Button: Reject (secondary/outlined, full-width)
 * Unhurried, no countdown timers, no red urgency cues.
 */
@Composable
fun Screen4Approval(
    onApprove: () -> Unit,
    onReject: () -> Unit,
    amountStr: String = "₹50,00,000",
    toStr: String = "ABC Industries",
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
            horizontalAlignment = Alignment.Start
        ) {
            // Label
            Text(
                text = "Approval requested",
                style = VoiceGuardTheme.typography.label.copy(color = VoiceGuardTheme.colors.textSecondary)
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space3))

            // Amount (text-display: 40sp)
            Text(
                text = amountStr,
                style = VoiceGuardTheme.typography.display.copy(color = VoiceGuardTheme.colors.textPrimary)
            )

            // Recipient (text-subtitle: 18sp)
            Text(
                text = "To: $toStr",
                style = VoiceGuardTheme.typography.subtitle.copy(color = VoiceGuardTheme.colors.textPrimary)
            )

            // Major block separation: space-7 (48dp)
            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space7))

            // Card: risk context
            VoiceGuardCard {
                Text(
                    text = "Security Context",
                    style = VoiceGuardTheme.typography.subtitle.copy(color = VoiceGuardTheme.colors.textPrimary)
                )
                Text(
                    text = "New recipient · Step-up approval required\nVoice verification flagged potential clone activity on associated call.",
                    style = VoiceGuardTheme.typography.body.copy(color = VoiceGuardTheme.colors.textSecondary)
                )
            }

            // Major block separation: space-7 (48dp)
            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space7))

            // Biometric prompt
            VoiceGuardCard {
                Text(
                    text = "Biometric Confirmation",
                    style = VoiceGuardTheme.typography.label.copy(color = VoiceGuardTheme.colors.textPrimary)
                )
                Text(
                    text = "Confirm with fingerprint or device PIN to verify transaction.",
                    style = VoiceGuardTheme.typography.caption.copy(color = VoiceGuardTheme.colors.textSecondary)
                )
            }

            // Major block separation: space-7 (48dp)
            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space7))

            Spacer(modifier = Modifier.weight(1f))

            // Primary Button: Approve
            VoiceGuardButton(
                text = "Approve",
                variant = ButtonVariant.PRIMARY,
                onClick = onApprove,
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space3))

            // Secondary Button: Reject (neutral, NOT red)
            VoiceGuardButton(
                text = "Reject",
                variant = ButtonVariant.SECONDARY,
                onClick = onReject,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

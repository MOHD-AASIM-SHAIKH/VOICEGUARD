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
 * Screen 3 — Report Confirmation
 * Layout:
 * - Title: "Report this call?" (text-title)
 * - space-5 (24dp)
 * - Card: Time, Confidence, Call type (text-body)
 * - space-6 (32dp)
 * - Button: Confirm & Report (primary, full-width)
 * - space-3 (12dp)
 * - Button: Cancel (secondary, full-width)
 * Neutral palette only — calm tone, no red/green.
 */
@Composable
fun Screen3Report(
    onConfirmReport: () -> Unit,
    onCancel: () -> Unit,
    timeStr: String = "13:42, Sept 14",
    confidenceStr: String = "93%",
    callTypeStr: String = "WhatsApp",
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
            // Title
            Text(
                text = "Report this call?",
                style = VoiceGuardTheme.typography.title.copy(color = VoiceGuardTheme.colors.textPrimary)
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space5))

            // Card: label/value pairs
            VoiceGuardCard {
                ReportDetailRow(label = "Time:", value = timeStr)
                ReportDetailRow(label = "Confidence:", value = confidenceStr)
                ReportDetailRow(label = "Call type:", value = callTypeStr)
            }

            Spacer(modifier = Modifier.weight(1f))

            // Primary Button: Confirm & Report
            VoiceGuardButton(
                text = "Confirm & Report",
                variant = ButtonVariant.PRIMARY,
                onClick = onConfirmReport,
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space3))

            // Secondary Button: Cancel
            VoiceGuardButton(
                text = "Cancel",
                variant = ButtonVariant.SECONDARY,
                onClick = onCancel,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

@Composable
private fun ReportDetailRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(
            text = label,
            style = VoiceGuardTheme.typography.body.copy(color = VoiceGuardTheme.colors.textSecondary)
        )
        Text(
            text = value,
            style = VoiceGuardTheme.typography.body.copy(color = VoiceGuardTheme.colors.textPrimary)
        )
    }
}

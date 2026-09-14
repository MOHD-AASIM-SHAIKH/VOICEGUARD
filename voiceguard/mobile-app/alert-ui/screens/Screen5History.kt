package com.voiceguard.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.voiceguard.ui.components.ButtonVariant
import com.voiceguard.ui.components.ListRow
import com.voiceguard.ui.components.VoiceGuardButton
import com.voiceguard.ui.theme.VoiceGuardTheme

data class ReportItem(
    val primaryText: String,
    val secondaryText: String
)

/**
 * Screen 5 — Evidence / Report History
 * Layout:
 * - Title: "Reports" (text-title, space-5 top)
 * - Flat list of ListRow items (no cards)
 * - Empty state: centered text-body in color-text-secondary, one sentence, no illustration
 * - Button: Back (secondary/outlined)
 */
@Composable
fun Screen5History(
    reports: List<ReportItem>,
    onBack: () -> Unit,
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
                    top = VoiceGuardTheme.spacing.space5,
                    bottom = VoiceGuardTheme.spacing.space6
                ),
            horizontalAlignment = Alignment.Start
        ) {
            // Title: "Reports"
            Text(
                text = "Reports",
                style = VoiceGuardTheme.typography.title.copy(color = VoiceGuardTheme.colors.textPrimary)
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space5))

            if (reports.isEmpty()) {
                // Empty state: centered text-body in color-text-secondary, one sentence, no illustration
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = VoiceGuardTheme.spacing.space8),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "No reports yet. Detected calls will appear here.",
                        style = VoiceGuardTheme.typography.body.copy(color = VoiceGuardTheme.colors.textSecondary),
                        textAlign = TextAlign.Center
                    )
                }
            } else {
                // Flat list, no cards
                Column(modifier = Modifier.fillMaxWidth()) {
                    reports.forEachIndexed { index, item ->
                        ListRow(
                            primaryText = item.primaryText,
                            secondaryText = item.secondaryText,
                            isLast = index == reports.size - 1
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.weight(1f))

            // Back button
            VoiceGuardButton(
                text = "Back",
                variant = ButtonVariant.SECONDARY,
                onClick = onBack,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

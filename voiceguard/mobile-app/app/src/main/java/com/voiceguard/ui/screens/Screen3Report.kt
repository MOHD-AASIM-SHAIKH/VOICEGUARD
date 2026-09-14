package com.voiceguard.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.voiceguard.BlockchainLedger
import com.voiceguard.ui.components.BlockchainBadge
import com.voiceguard.ui.components.ButtonVariant
import com.voiceguard.ui.components.VoiceGuardButton
import com.voiceguard.ui.components.VoiceGuardCard
import com.voiceguard.ui.theme.VoiceGuardTheme

/**
 * Screen 3 — Report & Blockchain Notarization
 * Displays call details, computed SHA-256 canonical hash,
 * target smart contract on Polygon, and Chakshu government portal link.
 */
@Composable
fun Screen3Report(
    onConfirmReport: () -> Unit,
    onCancel: () -> Unit,
    timeStr: String = "Just now · 12:45",
    confidenceStr: String = "94%",
    callTypeStr: String = "WhatsApp Call",
    modifier: Modifier = Modifier
) {
    val sha256Digest = remember(timeStr) {
        val raw = BlockchainLedger.computeEvidenceHash("VG-LIVE", timeStr, "WhatsApp", 0.94f)
        "0x" + raw.take(12) + "..." + raw.takeLast(8)
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
            horizontalAlignment = Alignment.Start
        ) {
            BlockchainBadge(text = "EvidenceLog.sol · Polygon Amoy")

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space3))

            // Title
            Text(
                text = "Report & Notarize Incident",
                style = VoiceGuardTheme.typography.title.copy(color = VoiceGuardTheme.colors.textPrimary)
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space4))

            // Card: label/value pairs including SHA-256 hash
            VoiceGuardCard {
                ReportDetailRow(label = "Call Timestamp:", value = timeStr)
                ReportDetailRow(label = "AI Confidence:", value = confidenceStr)
                ReportDetailRow(label = "Channel:", value = callTypeStr)
                ReportDetailRow(label = "Evidence Hash:", value = sha256Digest)
                ReportDetailRow(label = "Ledger:", value = "Polygon Amoy Testnet")
                ReportDetailRow(label = "Gov Portal:", value = "Chakshu (Sanchar Saathi)")
            }

            Spacer(modifier = Modifier.weight(1f))

            val context = androidx.compose.ui.platform.LocalContext.current
            val chakshuUrl = remember(timeStr, confidenceStr) {
                BlockchainLedger.buildChakshuLink(timeStr, "voip", 0.94f)
            }

            // Primary Button: Confirm & Notarize on Blockchain
            VoiceGuardButton(
                text = "Confirm & Notarize on Blockchain",
                variant = ButtonVariant.PRIMARY,
                onClick = onConfirmReport,
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space2))

            // Chakshu Portal Deep-Link Button
            VoiceGuardButton(
                text = "Report on Chakshu (DoT Portal)",
                variant = ButtonVariant.SECONDARY,
                onClick = {
                    try {
                        val intent = android.content.Intent(android.content.Intent.ACTION_VIEW, android.net.Uri.parse(chakshuUrl))
                        context.startActivity(intent)
                    } catch (e: Exception) {
                        android.widget.Toast.makeText(context, "Opening Chakshu portal: $chakshuUrl", android.widget.Toast.LENGTH_SHORT).show()
                    }
                },
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space2))

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

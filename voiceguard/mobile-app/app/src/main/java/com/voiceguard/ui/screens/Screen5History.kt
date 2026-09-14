package com.voiceguard.ui.screens

import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.voiceguard.BlockchainIncident
import com.voiceguard.BlockchainLedger
import com.voiceguard.ui.components.BlockchainBadge
import com.voiceguard.ui.components.ButtonVariant
import com.voiceguard.ui.components.VoiceGuardButton
import com.voiceguard.ui.theme.VoiceGuardTheme

data class ReportItem(
    val primaryText: String,
    val secondaryText: String
)

/**
 * Screen 5 — Evidence & Blockchain History
 * Shows immutable on-chain incident logs with SHA-256 hashes,
 * Polygon transaction links, and Chakshu DoT fraud reporting.
 */
@Composable
fun Screen5History(
    incidents: List<BlockchainIncident>,
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
                    bottom = VoiceGuardTheme.spacing.space5
                ),
            horizontalAlignment = Alignment.Start
        ) {
            BlockchainBadge(text = "EvidenceLog.sol · Polygon Amoy")

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space3))

            // Title
            Text(
                text = "On-Chain Evidence Ledger",
                style = VoiceGuardTheme.typography.title.copy(color = VoiceGuardTheme.colors.textPrimary)
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space2))

            Text(
                text = "Tamper-proof cryptographic hashes notarized to EVM smart contracts for forensic admissibility.",
                style = VoiceGuardTheme.typography.caption.copy(color = VoiceGuardTheme.colors.textSecondary)
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space4))

            if (incidents.isEmpty()) {
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = VoiceGuardTheme.spacing.space8),
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        text = "No incidents logged yet. Detected calls will appear here.",
                        style = VoiceGuardTheme.typography.body.copy(color = VoiceGuardTheme.colors.textSecondary),
                        textAlign = TextAlign.Center
                    )
                }
            } else {
                LazyColumn(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(VoiceGuardTheme.spacing.space3)
                ) {
                    items(incidents) { item ->
                        BlockchainIncidentCard(incident = item)
                    }
                }
            }

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space3))

            // Back button
            VoiceGuardButton(
                text = "Back to Protection Dashboard",
                variant = ButtonVariant.SECONDARY,
                onClick = onBack,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

@Composable
private fun BlockchainIncidentCard(incident: BlockchainIncident) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(VoiceGuardTheme.spacing.radius))
            .background(VoiceGuardTheme.colors.surface)
            .border(
                width = VoiceGuardTheme.spacing.borderWidth,
                color = VoiceGuardTheme.colors.border,
                shape = RoundedCornerShape(VoiceGuardTheme.spacing.radius)
            )
            .padding(VoiceGuardTheme.spacing.space4)
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(VoiceGuardTheme.spacing.space1)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = incident.timestamp,
                    style = VoiceGuardTheme.typography.subtitle.copy(color = VoiceGuardTheme.colors.textPrimary)
                )
                Text(
                    text = incident.status,
                    style = VoiceGuardTheme.typography.caption.copy(
                        color = Color(0xFF15803D),
                        fontWeight = FontWeight.Bold
                    )
                )
            }

            Spacer(modifier = Modifier.height(2.dp))

            Text(
                text = "SHA-256: ${incident.sha256Hash}",
                style = VoiceGuardTheme.typography.caption.copy(color = VoiceGuardTheme.colors.textSecondary)
            )

            Text(
                text = "Polygon Amoy · Block #${incident.blockNumber} · Tx: ${incident.txHash.take(12)}...",
                style = VoiceGuardTheme.typography.caption.copy(color = VoiceGuardTheme.colors.textSecondary)
            )

            val context = LocalContext.current
            val chakshuUrl = remember(incident) {
                BlockchainLedger.buildChakshuLink(incident.timestamp, incident.callType, incident.confidence)
            }

            Spacer(modifier = Modifier.height(4.dp))

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(8.dp))
                    .background(Color(0xFFEEF2FF))
                    .clickable {
                        try {
                            val intent = Intent(Intent.ACTION_VIEW, Uri.parse(chakshuUrl))
                            context.startActivity(intent)
                        } catch (e: Exception) {
                            Toast.makeText(context, "Opening: $chakshuUrl", Toast.LENGTH_SHORT).show()
                        }
                    }
                    .padding(horizontal = 10.dp, vertical = 8.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    text = "🔗 File Fraud Report on Chakshu",
                    style = VoiceGuardTheme.typography.caption.copy(
                        color = Color(0xFF4338CA),
                        fontWeight = FontWeight.SemiBold
                    )
                )
                Text(
                    text = "DoT Portal ↗",
                    style = VoiceGuardTheme.typography.caption.copy(
                        color = Color(0xFF4338CA),
                        fontWeight = FontWeight.Bold
                    )
                )
            }
        }
    }
}

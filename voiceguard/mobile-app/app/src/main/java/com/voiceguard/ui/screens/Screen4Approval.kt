package com.voiceguard.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.voiceguard.ui.components.BlockchainBadge
import com.voiceguard.ui.components.ButtonVariant
import com.voiceguard.ui.components.VoiceGuardButton
import com.voiceguard.ui.components.VoiceGuardCard
import com.voiceguard.ui.theme.VoiceGuardTheme

/**
 * Screen 4 — Trusted-Device Transaction Approval (Tier 2 Smart Contract Guard)
 * Demonstrates VoiceGuard's novelty banking protection:
 * When an AI clone attack is flagged, pending financial transfers are
 * locked on-chain via TransactionAuthorizer.sol and require biometric step-up verification.
 */
@Composable
fun Screen4Approval(
    onApprove: () -> Unit,
    onReject: () -> Unit,
    amountStr: String = "₹50,00,000",
    toStr: String = "ABC Industries Pvt Ltd",
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
                    top = VoiceGuardTheme.spacing.space6,
                    bottom = VoiceGuardTheme.spacing.space5
                ),
            horizontalAlignment = Alignment.Start
        ) {
            BlockchainBadge(text = "⛓️ TransactionAuthorizer.sol · Polygon")

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space3))

            // Label
            Text(
                text = "Guarded Transaction Intercepted",
                style = VoiceGuardTheme.typography.label.copy(color = VoiceGuardTheme.colors.stateClone)
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space2))

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

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space5))

            // Card: risk context
            VoiceGuardCard {
                Text(
                    text = "On-Chain Interceptor Context",
                    style = VoiceGuardTheme.typography.subtitle.copy(color = VoiceGuardTheme.colors.textPrimary)
                )
                Text(
                    text = "Status: PENDING_STEP_UP\nReason: VoiceGuard AI detected clone activity on active WhatsApp call.\nSmart Contract: 0x89205A...c43e7\nMulti-sig consensus locked pending device biometric authorization.",
                    style = VoiceGuardTheme.typography.body.copy(color = VoiceGuardTheme.colors.textSecondary)
                )
            }

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space4))

            // Biometric prompt
            VoiceGuardCard {
                Text(
                    text = "Biometric Step-Up Authorization",
                    style = VoiceGuardTheme.typography.label.copy(color = VoiceGuardTheme.colors.textPrimary)
                )
                Text(
                    text = "Touch device fingerprint sensor to sign and unfreeze transaction on Polygon ledger.",
                    style = VoiceGuardTheme.typography.caption.copy(color = VoiceGuardTheme.colors.textSecondary)
                )
            }

            Spacer(modifier = Modifier.weight(1f))

            // Primary Button: Approve
            VoiceGuardButton(
                text = "Approve & Sign Transaction",
                variant = ButtonVariant.PRIMARY,
                onClick = onApprove,
                modifier = Modifier.fillMaxWidth()
            )

            Spacer(modifier = Modifier.height(VoiceGuardTheme.spacing.space3))

            // Secondary Button: Reject (neutral)
            VoiceGuardButton(
                text = "Reject & Maintain On-Chain Lock",
                variant = ButtonVariant.SECONDARY,
                onClick = onReject,
                modifier = Modifier.fillMaxWidth()
            )
        }
    }
}

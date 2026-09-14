package com.voiceguard.ui.screens

import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import com.voiceguard.BlockchainIncident
import com.voiceguard.BlockchainLedger
import com.voiceguard.DetectionManager
import com.voiceguard.ui.theme.VoiceGuardTheme

enum class ScreenRoute {
    IDLE,
    CLONE_ALERT,
    REPORT_CONFIRMATION,
    APPROVAL,
    HISTORY
}

/**
 * Full Flow Assembly Navigation Host (Part 4 Phase 8)
 * Manages full lifecycle and transitions between the 5 screens:
 * 1. Idle -> Clone Detected -> Report & Blockchain Notarization -> Evidence Ledger
 * 2. Idle -> Guarded Transaction Approval (Smart Contract) -> back to Idle
 * 3. Idle -> Blockchain Evidence History -> back to Idle
 */
@Composable
fun VoiceGuardNavHost(
    modifier: Modifier = Modifier
) {
    var currentScreen by remember { mutableStateOf(ScreenRoute.IDLE) }
    val incidentsList = remember {
        mutableStateListOf<BlockchainIncident>().apply {
            addAll(BlockchainLedger.createSampleIncidents())
        }
    }

    // Collect DetectionManager reactive state flows
    val isProtectionActive by DetectionManager.isProtectionActive.collectAsState()
    val detectionState by DetectionManager.detectionState.collectAsState()
    val confidence by DetectionManager.confidence.collectAsState()
    val elapsedSeconds by DetectionManager.elapsedSeconds.collectAsState()
    val callContextDescription by DetectionManager.callContextDescription.collectAsState()

    // Automatically transition to CLONE_ALERT when model detects clone
    LaunchedEffect(detectionState) {
        if (detectionState == "CLONED" && currentScreen == ScreenRoute.IDLE) {
            currentScreen = ScreenRoute.CLONE_ALERT
        }
    }

    VoiceGuardTheme {
        when (currentScreen) {
            ScreenRoute.IDLE -> {
                Screen1Listening(
                    isProtectionActive = isProtectionActive,
                    confidence = confidence,
                    elapsedSeconds = elapsedSeconds,
                    callContextDescription = callContextDescription,
                    onToggleProtection = {
                        DetectionManager.toggleProtection()
                    },
                    onSimulateClone = {
                        DetectionManager.simulateClone(0.94f)
                    },
                    onOpenApproval = {
                        currentScreen = ScreenRoute.APPROVAL
                    },
                    onOpenHistory = {
                        currentScreen = ScreenRoute.HISTORY
                    },
                    modifier = modifier
                )
            }
            ScreenRoute.CLONE_ALERT -> {
                Screen2CloneAlert(
                    confidence = confidence,
                    onHangUp = {
                        DetectionManager.simulateReal()
                        currentScreen = ScreenRoute.IDLE
                    },
                    onReport = {
                        currentScreen = ScreenRoute.REPORT_CONFIRMATION
                    },
                    modifier = modifier
                )
            }
            ScreenRoute.REPORT_CONFIRMATION -> {
                Screen3Report(
                    confidenceStr = "${(confidence * 100).toInt()}%",
                    onConfirmReport = {
                        val newHash = BlockchainLedger.computeEvidenceHash("VG-LIVE", "Just now · WhatsApp", "WhatsApp", confidence)
                        val newIncident = BlockchainIncident(
                            id = "VG-LIVE-${System.currentTimeMillis() % 10000}",
                            timestamp = "Just now · WhatsApp",
                            callType = "voip",
                            app = "WhatsApp",
                            confidence = confidence,
                            sha256Hash = "0x" + newHash.take(16) + "..." + newHash.takeLast(8),
                            txHash = "0x7a83d4c510b2849e73f8a12bc94e751a02d8f92c",
                            blockNumber = 4829315L,
                            status = "VERIFIED ON-CHAIN"
                        )
                        incidentsList.add(0, newIncident)
                        DetectionManager.simulateReal()
                        currentScreen = ScreenRoute.HISTORY
                    },
                    onCancel = {
                        DetectionManager.simulateReal()
                        currentScreen = ScreenRoute.IDLE
                    },
                    modifier = modifier
                )
            }
            ScreenRoute.APPROVAL -> {
                Screen4Approval(
                    onApprove = {
                        currentScreen = ScreenRoute.IDLE
                    },
                    onReject = {
                        currentScreen = ScreenRoute.IDLE
                    },
                    modifier = modifier
                )
            }
            ScreenRoute.HISTORY -> {
                Screen5History(
                    incidents = incidentsList,
                    onBack = {
                        currentScreen = ScreenRoute.IDLE
                    },
                    modifier = modifier
                )
            }
        }
    }
}

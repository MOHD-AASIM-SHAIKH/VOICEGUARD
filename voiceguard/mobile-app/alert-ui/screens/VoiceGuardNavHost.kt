package com.voiceguard.ui.screens

import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
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
 * 1. Idle -> Clone Detected -> Report Confirmation -> back to Idle
 * 2. Idle -> Trusted-Device Approval -> back to Idle
 * 3. Idle -> Evidence History -> back to Idle
 */
@Composable
fun VoiceGuardNavHost(
    modifier: Modifier = Modifier
) {
    var currentScreen by remember { mutableStateOf(ScreenRoute.IDLE) }
    val reportsHistory = remember {
        mutableStateListOf(
            ReportItem("13:42 · WhatsApp", "Reported"),
            ReportItem("Yesterday · Call", "Reported"),
            ReportItem("Sept 10 · WhatsApp", "Reported")
        )
    }

    VoiceGuardTheme {
        when (currentScreen) {
            ScreenRoute.IDLE -> {
                Screen1Listening(
                    onStopProtection = {
                        // Toggle or navigate
                    },
                    modifier = modifier
                )
            }
            ScreenRoute.CLONE_ALERT -> {
                Screen2CloneAlert(
                    onHangUp = {
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
                    onConfirmReport = {
                        reportsHistory.add(0, ReportItem("Just now · WhatsApp", "Reported"))
                        currentScreen = ScreenRoute.IDLE
                    },
                    onCancel = {
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
                    reports = reportsHistory,
                    onBack = {
                        currentScreen = ScreenRoute.IDLE
                    },
                    modifier = modifier
                )
            }
        }
    }
}

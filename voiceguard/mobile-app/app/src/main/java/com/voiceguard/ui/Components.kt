package com.voiceguard.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.voiceguard.ui.theme.VoiceGuardTheme

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.runtime.getValue
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.TextUnit
import androidx.compose.ui.unit.TextUnitType

enum class DetectionState {
    REAL,
    CLONE,
    PAUSED
}

enum class ButtonVariant {
    PRIMARY,
    SECONDARY
}

/**
 * 2.0 CircularConfidenceMeter
 * Circular radial progress ring with grey track background and dynamic
 * green (REAL) or red (CLONED) confidence stroke fill + center details.
 */
@Composable
fun CircularConfidenceMeter(
    state: DetectionState,
    confidence: Float,
    caption: String,
    modifier: Modifier = Modifier
) {
    val targetProgress = when (state) {
        DetectionState.REAL -> confidence.coerceIn(0f, 1f)
        DetectionState.CLONE -> confidence.coerceIn(0f, 1f)
        DetectionState.PAUSED -> 0f
    }

    val animatedProgress by animateFloatAsState(
        targetValue = targetProgress,
        animationSpec = tween(durationMillis = 400),
        label = "ConfidenceProgress"
    )

    val activeColor = when (state) {
        DetectionState.REAL -> VoiceGuardTheme.colors.stateReal
        DetectionState.CLONE -> VoiceGuardTheme.colors.stateClone
        DetectionState.PAUSED -> Color(0xFF9CA3AF)
    }

    val trackColor = Color(0xFFE5E7EB)

    val stateText = when (state) {
        DetectionState.REAL -> "REAL"
        DetectionState.CLONE -> "CLONE"
        DetectionState.PAUSED -> "PAUSED"
    }

    val percentageText = when (state) {
        DetectionState.REAL -> "${(confidence * 100).toInt()}% Authentic"
        DetectionState.CLONE -> "${(confidence * 100).toInt()}% AI Spoof"
        DetectionState.PAUSED -> "Monitoring Off"
    }

    Box(
        modifier = modifier.size(230.dp),
        contentAlignment = Alignment.Center
    ) {
        Canvas(modifier = Modifier.fillMaxSize().padding(14.dp)) {
            val strokeWidth = 14.dp.toPx()
            // 1. Background grey ring
            drawArc(
                color = trackColor,
                startAngle = -90f,
                sweepAngle = 360f,
                useCenter = false,
                style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
            )

            // 2. Active confidence arc
            if (animatedProgress > 0.01f) {
                drawArc(
                    color = activeColor,
                    startAngle = -90f,
                    sweepAngle = 360f * animatedProgress,
                    useCenter = false,
                    style = Stroke(width = strokeWidth, cap = StrokeCap.Round)
                )
            }
        }

        // Inside center details
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = stateText,
                style = VoiceGuardTheme.typography.display.copy(
                    color = activeColor,
                    fontSize = TextUnit(34f, TextUnitType.Sp)
                ),
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = percentageText,
                style = VoiceGuardTheme.typography.subtitle.copy(
                    color = VoiceGuardTheme.colors.textPrimary,
                    fontSize = TextUnit(15f, TextUnitType.Sp),
                    fontWeight = FontWeight.SemiBold
                ),
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = caption,
                style = VoiceGuardTheme.typography.caption.copy(color = VoiceGuardTheme.colors.textSecondary),
                textAlign = TextAlign.Center
            )
        }
    }
}

/**
 * 2.05 BlockchainBadge
 * Visual trust badge indicating on-chain smart contract verification
 */
@Composable
fun BlockchainBadge(
    text: String = "Polygon Amoy Verified",
    modifier: Modifier = Modifier
) {
    Row(
        modifier = modifier
            .clip(RoundedCornerShape(16.dp))
            .background(Color(0xFFEDE9FE))
            .border(1.dp, Color(0xFF8B5CF6).copy(alpha = 0.4f), RoundedCornerShape(16.dp))
            .padding(horizontal = 12.dp, vertical = 6.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Box(
            modifier = Modifier
                .size(8.dp)
                .clip(RoundedCornerShape(4.dp))
                .background(Color(0xFF8B5CF6))
        )
        Text(
            text = text,
            style = VoiceGuardTheme.typography.caption.copy(
                color = Color(0xFF6D28D9),
                fontWeight = FontWeight.SemiBold
            )
        )
    }
}

/**
 * 2.1 StatusIndicator
 * Full-width block, radius 8dp, padding 32dp vertical / 24dp horizontal.
 * State word in text-display, colored state-real, state-clone, or text-secondary.
 * Caption in text-caption colored text-secondary.
 */
@Composable
fun StatusIndicator(
    state: DetectionState,
    caption: String,
    modifier: Modifier = Modifier
) {
    val bgColor = when (state) {
        DetectionState.REAL -> VoiceGuardTheme.colors.stateRealBg
        DetectionState.CLONE -> VoiceGuardTheme.colors.stateCloneBg
        DetectionState.PAUSED -> Color(0xFFF3F4F6)
    }
    val stateColor = when (state) {
        DetectionState.REAL -> VoiceGuardTheme.colors.stateReal
        DetectionState.CLONE -> VoiceGuardTheme.colors.stateClone
        DetectionState.PAUSED -> VoiceGuardTheme.colors.textSecondary
    }
    val stateText = when (state) {
        DetectionState.REAL -> "REAL"
        DetectionState.CLONE -> "CLONE DETECTED"
        DetectionState.PAUSED -> "PAUSED"
    }

    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(VoiceGuardTheme.spacing.radius))
            .background(bgColor)
            .padding(
                horizontal = VoiceGuardTheme.spacing.space5,
                vertical = VoiceGuardTheme.spacing.space6
            ),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.spacedBy(VoiceGuardTheme.spacing.space2)
        ) {
            Text(
                text = stateText,
                style = VoiceGuardTheme.typography.display.copy(color = stateColor),
                textAlign = TextAlign.Center
            )
            Text(
                text = caption,
                style = VoiceGuardTheme.typography.caption.copy(color = VoiceGuardTheme.colors.textSecondary),
                textAlign = TextAlign.Center
            )
        }
    }
}

/**
 * 2.2 Button
 * Primary: bg text-primary, text white, text-label, padding 12dp v / 24dp h, radius 8dp.
 * Secondary: bg transparent, border 1dp solid border, text text-primary, radius 8dp.
 */
@Composable
fun VoiceGuardButton(
    text: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier,
    variant: ButtonVariant = ButtonVariant.PRIMARY
) {
    val isPrimary = variant == ButtonVariant.PRIMARY
    val bgColor = if (isPrimary) VoiceGuardTheme.colors.textPrimary else Color.Transparent
    val textColor = if (isPrimary) Color.White else VoiceGuardTheme.colors.textPrimary
    val borderModifier = if (!isPrimary) {
        Modifier.border(
            width = VoiceGuardTheme.spacing.borderWidth,
            color = VoiceGuardTheme.colors.border,
            shape = RoundedCornerShape(VoiceGuardTheme.spacing.radius)
        )
    } else Modifier

    Box(
        modifier = modifier
            .clip(RoundedCornerShape(VoiceGuardTheme.spacing.radius))
            .then(borderModifier)
            .background(bgColor)
            .clickable(onClick = onClick)
            .padding(
                horizontal = VoiceGuardTheme.spacing.space5,
                vertical = VoiceGuardTheme.spacing.space3
            ),
        contentAlignment = Alignment.Center
    ) {
        Text(
            text = text,
            style = VoiceGuardTheme.typography.label.copy(color = textColor),
            textAlign = TextAlign.Center
        )
    }
}

/**
 * 2.3 Card
 * Background surface, 1dp border, radius 8dp, padding 24dp. No shadow.
 */
@Composable
fun VoiceGuardCard(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit
) {
    Box(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(VoiceGuardTheme.spacing.radius))
            .background(VoiceGuardTheme.colors.surface)
            .border(
                width = VoiceGuardTheme.spacing.borderWidth,
                color = VoiceGuardTheme.colors.border,
                shape = RoundedCornerShape(VoiceGuardTheme.spacing.radius)
            )
            .padding(VoiceGuardTheme.spacing.space5)
    ) {
        Column(
            modifier = Modifier.fillMaxWidth(),
            verticalArrangement = Arrangement.spacedBy(VoiceGuardTheme.spacing.space3),
            content = content
        )
    }
}

/**
 * 2.4 ListRow
 * Padding 16dp v / 24dp h, 1dp bottom border. Left: text-body, Right: text-caption.
 */
@Composable
fun ListRow(
    primaryText: String,
    secondaryText: String,
    isLast: Boolean = false,
    onClick: (() -> Unit)? = null,
    modifier: Modifier = Modifier
) {
    val clickableModifier = if (onClick != null) Modifier.clickable(onClick = onClick) else Modifier

    Column(
        modifier = modifier
            .fillMaxWidth()
            .then(clickableModifier)
    ) {
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(
                    horizontal = VoiceGuardTheme.spacing.space5,
                    vertical = VoiceGuardTheme.spacing.space4
                ),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = primaryText,
                style = VoiceGuardTheme.typography.body.copy(color = VoiceGuardTheme.colors.textPrimary)
            )
            Text(
                text = secondaryText,
                style = VoiceGuardTheme.typography.caption.copy(color = VoiceGuardTheme.colors.textSecondary)
            )
        }
        if (!isLast) {
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(VoiceGuardTheme.spacing.borderWidth)
                    .background(VoiceGuardTheme.colors.border)
            )
        }
    }
}

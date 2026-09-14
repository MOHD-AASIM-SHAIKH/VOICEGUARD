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

enum class DetectionState {
    REAL,
    CLONE
}

enum class ButtonVariant {
    PRIMARY,
    SECONDARY
}

/**
 * 2.1 StatusIndicator
 * Full-width block, radius 8dp, padding 32dp vertical / 24dp horizontal.
 * State word in text-display, colored state-real or state-clone.
 * Caption in text-caption colored text-secondary.
 */
@Composable
fun StatusIndicator(
    state: DetectionState,
    caption: String,
    modifier: Modifier = Modifier
) {
    val isReal = state == DetectionState.REAL
    val bgColor = if (isReal) VoiceGuardTheme.colors.stateRealBg else VoiceGuardTheme.colors.stateCloneBg
    val stateColor = if (isReal) VoiceGuardTheme.colors.stateReal else VoiceGuardTheme.colors.stateClone
    val stateText = if (isReal) "REAL" else "CLONE DETECTED"

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

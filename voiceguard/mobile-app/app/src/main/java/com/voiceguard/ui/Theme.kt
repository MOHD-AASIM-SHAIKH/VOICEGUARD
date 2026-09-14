package com.voiceguard.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.Immutable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

/**
 * VoiceGuard Design Tokens — Part 1 of UI Spec (Fixed).
 * Strictly defines colors, typography, spacing, radius, elevation, motion.
 */

@Immutable
data class VoiceGuardColors(
    val bg: Color = Color(0xFFFFFFFF),
    val surface: Color = Color(0xFFF7F7F5),
    val border: Color = Color(0xFFE3E3E0),
    val textPrimary: Color = Color(0xFF1A1A1A),
    val textSecondary: Color = Color(0xFF6B6B68),
    val textTertiary: Color = Color(0xFF9A9A96),
    val stateReal: Color = Color(0xFF3F7D5C),
    val stateRealBg: Color = Color(0xFFEAF2EC),
    val stateClone: Color = Color(0xFFA8453F),
    val stateCloneBg: Color = Color(0xFFF7EAE9)
)

@Immutable
data class VoiceGuardTypography(
    val fontFamily: FontFamily = FontFamily.SansSerif,
    val display: TextStyle = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.W700,
        fontSize = 40.sp,
        lineHeight = 44.sp
    ),
    val title: TextStyle = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.W600,
        fontSize = 24.sp,
        lineHeight = 30.sp
    ),
    val subtitle: TextStyle = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.W600,
        fontSize = 18.sp,
        lineHeight = 24.sp
    ),
    val body: TextStyle = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.W400,
        fontSize = 16.sp,
        lineHeight = 24.sp
    ),
    val label: TextStyle = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.W500,
        fontSize = 14.sp,
        lineHeight = 20.sp
    ),
    val caption: TextStyle = TextStyle(
        fontFamily = FontFamily.SansSerif,
        fontWeight = FontWeight.W400,
        fontSize = 13.sp,
        lineHeight = 18.sp
    )
)

@Immutable
data class VoiceGuardSpacing(
    val space1: Dp = 4.dp,
    val space2: Dp = 8.dp,
    val space3: Dp = 12.dp,
    val space4: Dp = 16.dp,
    val space5: Dp = 24.dp,
    val space6: Dp = 32.dp,
    val space7: Dp = 48.dp,
    val space8: Dp = 64.dp,
    val radius: Dp = 8.dp,
    val borderWidth: Dp = 1.dp
)

object VoiceGuardMotion {
    const val TRANSITION_DURATION_MS: Int = 180
}

val LocalVoiceGuardColors = staticCompositionLocalOf { VoiceGuardColors() }
val LocalVoiceGuardTypography = staticCompositionLocalOf { VoiceGuardTypography() }
val LocalVoiceGuardSpacing = staticCompositionLocalOf { VoiceGuardSpacing() }

object VoiceGuardTheme {
    val colors: VoiceGuardColors
        @Composable
        get() = LocalVoiceGuardColors.current

    val typography: VoiceGuardTypography
        @Composable
        get() = LocalVoiceGuardTypography.current

    val spacing: VoiceGuardSpacing
        @Composable
        get() = LocalVoiceGuardSpacing.current
}

@Composable
fun VoiceGuardTheme(
    content: @Composable () -> Unit
) {
    val colors = VoiceGuardColors()
    val typography = VoiceGuardTypography()
    val spacing = VoiceGuardSpacing()

    CompositionLocalProvider(
        LocalVoiceGuardColors provides colors,
        LocalVoiceGuardTypography provides typography,
        LocalVoiceGuardSpacing provides spacing,
        content = content
    )
}

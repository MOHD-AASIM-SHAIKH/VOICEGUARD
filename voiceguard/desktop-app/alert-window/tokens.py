"""VoiceGuard Design Tokens — Part 1 of UI Spec (Fixed).

All design values are strictly defined here. No colors outside this set are permitted.
"""

# 1.1 Color Tokens
COLOR_BG = "#FFFFFF"            # App background
COLOR_SURFACE = "#F7F7F5"       # Cards, elevated panels — barely off-white
COLOR_BORDER = "#E3E3E0"        # Hairline borders, replaces shadows
COLOR_TEXT_PRIMARY = "#1A1A1A"  # Headings, primary text — near-black, not pure #000
COLOR_TEXT_SECONDARY = "#6B6B68"# Labels, timestamps, secondary text
COLOR_TEXT_TERTIARY = "#9A9A96" # Placeholder, disabled text

COLOR_STATE_REAL = "#3F7D5C"    # Muted sage green — ONLY for "real/safe" state
COLOR_STATE_REAL_BG = "#EAF2EC" # Pale tint of state-real, for backgrounds behind green state
COLOR_STATE_CLONE = "#A8453F"   # Muted brick red — ONLY for "cloned/alert" state
COLOR_STATE_CLONE_BG = "#F7EAE9"# Pale tint of state-clone, for backgrounds behind red state

# 1.2 Typography Tokens
FONT_FAMILY = "Inter, -apple-system, system-ui, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"

TEXT_DISPLAY = {
    "size": 40,
    "weight": 700,
    "line_height": 1.1,
}
TEXT_TITLE = {
    "size": 24,
    "weight": 600,
    "line_height": 1.25,
}
TEXT_SUBTITLE = {
    "size": 18,
    "weight": 600,
    "line_height": 1.35,
}
TEXT_BODY = {
    "size": 16,
    "weight": 400,
    "line_height": 1.5,
}
TEXT_LABEL = {
    "size": 14,
    "weight": 500,
    "line_height": 1.4,
}
TEXT_CAPTION = {
    "size": 13,
    "weight": 400,
    "line_height": 1.4,
}

# 1.3 Spacing Tokens (8pt grid)
SPACE_1 = 4
SPACE_2 = 8
SPACE_3 = 12
SPACE_4 = 16
SPACE_5 = 24
SPACE_6 = 32
SPACE_7 = 48
SPACE_8 = 64

# 1.4 Radius & Elevation Tokens
RADIUS = 8        # Every card, button, input — one value, no exceptions
BORDER_WIDTH = 1  # Replaces shadows

# 1.5 Motion
TRANSITION_DURATION_MS = 180

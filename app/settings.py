"""
settings.py — Global UI constants and color palette.
"""

# Base Window
DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 800

# Thumbnails
THUMB_SLIDING_WINDOW = 5 # ±2 around current

# Dark Theme Palette
COLORS = {
    "Background": "#141414",
    "Surface": "#1c1c1c",
    "Surface2": "#242424",
    "Border": "#2e2e2e",
    "TextPrimary": "#e8e8e6",
    "TextSecondary": "#888780",
    "TextMuted": "#555552",
    "AccentGreen": "#5dcaa5",
    "AccentGreenDim": "#0f6e56",
    "Amber": "#ef9f27",
    "Blue": "#378add",
    "Coral": "#d85a30",
}

# Subfolder Button Colors (ordered 1 to 9)
SUBFOLDER_COLORS = [
    "#5dcaa5", # Teal
    "#378add", # Blue
    "#ef9f27", # Amber
    "#d85a30", # Coral
    "#a78bfa", # Purple
    "#f472b6", # Pink
    "#34d399", # Emerald
    "#fb923c", # Orange
    "#60a5fa", # Sky
]

# Global StyleSheet applied to QApplication
GLOBAL_STYLESHEET = f"""
QWidget {{
    background-color: {COLORS['Background']};
    color: {COLORS['TextPrimary']};
    font-family: "Segoe UI", system-ui, sans-serif;
}}

/* Standard text inputs */
QLineEdit {{
    background-color: {COLORS['Surface']};
    border: 1px solid {COLORS['Border']};
    padding: 8px;
    border-radius: 4px;
}}
QLineEdit:focus {{
    border: 1px solid {COLORS['AccentGreen']};
}}

/* Standard push buttons */
QPushButton {{
    background-color: {COLORS['Surface']};
    border: 1px solid {COLORS['Border']};
    padding: 8px 16px;
    border-radius: 4px;
}}
QPushButton:hover {{
    background-color: {COLORS['Surface2']};
}}
QPushButton:pressed {{
    background-color: {COLORS['Border']};
}}

/* CTA buttons */
QPushButton#ctaButton {{
    background-color: {COLORS['AccentGreen']};
    color: {COLORS['Background']};
    font-weight: bold;
    border: none;
}}
QPushButton#ctaButton:hover {{
    background-color: #6edcb6;
}}
QPushButton#ctaButton:disabled {{
    background-color: {COLORS['Surface']};
    color: {COLORS['TextMuted']};
}}

/* Scroll Area */
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:horizontal {{
    border: none;
    background: {COLORS['Background']};
    height: 10px;
    margin: 0px 0px 0px 0px;
}}
QScrollBar::handle:horizontal {{
    background: {COLORS['Border']};
    min-width: 20px;
    border-radius: 5px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {COLORS['TextMuted']};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}
"""

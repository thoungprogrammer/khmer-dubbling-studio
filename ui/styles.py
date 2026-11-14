"""
UI Styles - Modern dark theme for Khmer Dubbing Studio
"""

KHMER_FONT_PRIMARY = "Noto Sans Khmer"
KHMER_FONT_FALLBACK = "Khmer OS"
KHMER_FONT_SYSTEM  = "Khmer UI"
UI_FONT            = "Segoe UI"
KHMER_FONT_SIZE    = "15px"
UI_FONT_SIZE       = "13px"
FONT_STACK = f"'{KHMER_FONT_PRIMARY}', '{KHMER_FONT_FALLBACK}', '{KHMER_FONT_SYSTEM}', '{UI_FONT}', Arial, sans-serif"

# Colour palette
C_BG        = "#0d1117"   # main background  — deep navy/black
C_SURFACE   = "#161b22"   # card/panel surface
C_SURFACE2  = "#21262d"   # slightly lighter surface
C_BORDER    = "#30363d"   # subtle border
C_ACCENT    = "#58a6ff"   # blue accent (links, highlights)
C_ACCENT2   = "#f78166"   # coral accent (primary actions)
C_SUCCESS   = "#3fb950"   # green
C_TEXT      = "#e6edf3"   # primary text
C_TEXT_DIM  = "#7d8590"   # secondary / muted text
C_GOLD      = "#ffa657"   # Khmer text colour

DARK_THEME = f"""
/* ── Root ───────────────────────────────────────────── */
QMainWindow, QDialog {{
    background-color: {C_BG};
}}

QWidget {{
    background-color: {C_BG};
    color: {C_TEXT};
    font-family: {FONT_STACK};
    font-size: {UI_FONT_SIZE};
}}

/* ── Scroll areas ────────────────────────────────────── */
QScrollArea {{
    border: none;
    background: transparent;
}}
QScrollArea > QWidget > QWidget {{
    background: transparent;
}}

/* ── Panels / cards ──────────────────────────────────── */
QFrame#card {{
    background-color: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 10px;
}}

QFrame#headerCard {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #161b22, stop:0.5 #1c2333, stop:1 #161b22);
    border: 1px solid {C_BORDER};
    border-radius: 10px;
}}

QFrame#dropCard {{
    background-color: {C_SURFACE};
    border: 2px dashed {C_BORDER};
    border-radius: 12px;
}}
QFrame#dropCard:hover {{
    border-color: {C_ACCENT};
    background-color: {C_SURFACE2};
}}

/* ── GroupBox ────────────────────────────────────────── */
QGroupBox {{
    background-color: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 10px;
    margin-top: 14px;
    padding: 10px 8px 8px 8px;
    font-family: '{UI_FONT}', sans-serif;
    font-size: 12px;
    font-weight: bold;
    color: {C_TEXT_DIM};
    text-transform: uppercase;
    letter-spacing: 1px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    color: {C_ACCENT};
    background: {C_SURFACE};
    border-radius: 4px;
}}

/* ── Buttons ─────────────────────────────────────────── */
QPushButton {{
    background-color: {C_SURFACE2};
    color: {C_TEXT};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 7px 18px;
    font-family: '{UI_FONT}', sans-serif;
    font-size: 13px;
    min-height: 34px;
}}
QPushButton:hover {{
    background-color: #2d333b;
    border-color: {C_ACCENT};
    color: {C_ACCENT};
}}
QPushButton:pressed {{
    background-color: #1c2128;
}}
QPushButton:disabled {{
    background-color: {C_SURFACE};
    color: {C_TEXT_DIM};
    border-color: {C_BORDER};
}}

QPushButton#primaryButton {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #e05a3a, stop:1 #f78166);
    color: white;
    font-weight: bold;
    font-size: 14px;
    min-height: 44px;
    border-radius: 10px;
    border: none;
    letter-spacing: 0.5px;
}}
QPushButton#primaryButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #f06040, stop:1 #ff9070);
}}
QPushButton#primaryButton:pressed {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #c04020, stop:1 #e06050);
}}
QPushButton#primaryButton:disabled {{
    background: #2d333b;
    color: {C_TEXT_DIM};
}}

QPushButton#successButton {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #2ea043, stop:1 #3fb950);
    color: white;
    font-weight: bold;
    border: none;
    border-radius: 8px;
}}
QPushButton#successButton:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #3fb950, stop:1 #56d364);
}}

QPushButton#cancelButton {{
    background-color: {C_SURFACE2};
    color: #f85149;
    border: 1px solid #f85149;
    border-radius: 8px;
}}
QPushButton#cancelButton:hover {{
    background-color: rgba(248,81,73,0.15);
}}

/* ── Input fields ────────────────────────────────────── */
QLineEdit, QPlainTextEdit {{
    background-color: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 7px 10px;
    color: {C_TEXT};
    font-family: {FONT_STACK};
    font-size: {UI_FONT_SIZE};
    selection-background-color: {C_ACCENT};
}}
QLineEdit:focus, QPlainTextEdit:focus {{
    border-color: {C_ACCENT};
    background-color: {C_SURFACE2};
}}

QTextEdit {{
    background-color: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 8px;
    color: {C_TEXT};
    font-family: {FONT_STACK};
    font-size: {UI_FONT_SIZE};
    selection-background-color: {C_ACCENT};
}}

/* ── ComboBox ────────────────────────────────────────── */
QComboBox {{
    background-color: {C_SURFACE2};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 6px 12px;
    color: {C_TEXT};
    font-family: {FONT_STACK};
    font-size: {UI_FONT_SIZE};
    min-height: 32px;
}}
QComboBox:hover {{
    border-color: {C_ACCENT};
}}
QComboBox:on {{
    border-color: {C_ACCENT};
    background-color: {C_SURFACE};
}}
QComboBox::drop-down {{
    border: none;
    width: 24px;
    padding-right: 6px;
}}
QComboBox::down-arrow {{
    width: 10px;
    height: 10px;
    border: 2px solid {C_TEXT_DIM};
    border-top: none;
    border-left: none;
    transform: rotate(45deg);
    margin-top: -4px;
}}
QComboBox QAbstractItemView {{
    background-color: {C_SURFACE2};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    padding: 4px;
    outline: none;
    selection-background-color: rgba(88,166,255,0.2);
    selection-color: {C_TEXT};
    font-family: {FONT_STACK};
    font-size: {UI_FONT_SIZE};
}}
QComboBox QAbstractItemView::item {{
    padding: 6px 10px;
    border-radius: 4px;
    min-height: 28px;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: rgba(88,166,255,0.15);
}}

/* ── Sliders ─────────────────────────────────────────── */
QSlider::groove:horizontal {{
    height: 4px;
    background: {C_SURFACE2};
    border-radius: 2px;
    margin: 0 2px;
}}
QSlider::handle:horizontal {{
    background: {C_ACCENT};
    border: 2px solid {C_BG};
    width: 16px;
    height: 16px;
    border-radius: 8px;
    margin: -6px -2px;
}}
QSlider::handle:horizontal:hover {{
    background: #79bfff;
    width: 18px;
    height: 18px;
    border-radius: 9px;
    margin: -7px -3px;
}}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C_ACCENT2}, stop:1 {C_ACCENT});
    border-radius: 2px;
}}

/* ── Progress bar ────────────────────────────────────── */
QProgressBar {{
    background-color: {C_SURFACE2};
    border: none;
    border-radius: 6px;
    text-align: center;
    color: {C_TEXT};
    font-weight: bold;
    font-size: 11px;
    min-height: 12px;
    max-height: 12px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 {C_ACCENT2}, stop:0.5 {C_ACCENT}, stop:1 #a371f7);
    border-radius: 6px;
}}

/* ── Tables ──────────────────────────────────────────── */
QTableWidget {{
    background-color: {C_SURFACE};
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    gridline-color: {C_SURFACE2};
    outline: none;
    font-family: {FONT_STACK};
    font-size: {KHMER_FONT_SIZE};
}}
QTableWidget::item {{
    padding: 6px 10px;
    border-bottom: 1px solid {C_SURFACE2};
}}
QTableWidget::item:selected {{
    background-color: rgba(88,166,255,0.2);
    color: {C_TEXT};
}}
QTableWidget::item:hover {{
    background-color: rgba(88,166,255,0.08);
}}
QHeaderView::section {{
    background-color: {C_SURFACE2};
    color: {C_TEXT_DIM};
    padding: 8px 10px;
    border: none;
    border-right: 1px solid {C_BORDER};
    border-bottom: 1px solid {C_BORDER};
    font-family: '{UI_FONT}', sans-serif;
    font-size: 12px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
QHeaderView::section:first {{
    border-top-left-radius: 8px;
}}
QHeaderView::section:last {{
    border-top-right-radius: 8px;
    border-right: none;
}}
QTableCornerButton::section {{
    background-color: {C_SURFACE2};
    border: none;
}}

/* ── Scrollbars ──────────────────────────────────────── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C_BORDER};
    border-radius: 3px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
    background: {C_TEXT_DIM};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: transparent;
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
}}
QScrollBar::handle:horizontal {{
    background: {C_BORDER};
    border-radius: 3px;
    min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
    background: {C_TEXT_DIM};
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
    background: transparent;
    width: 0;
}}

/* ── Tabs ────────────────────────────────────────────── */
QTabWidget::pane {{
    border: 1px solid {C_BORDER};
    border-radius: 0 10px 10px 10px;
    background: {C_SURFACE};
    top: -1px;
}}
QTabBar {{
    background: transparent;
}}
QTabBar::tab {{
    background: transparent;
    color: {C_TEXT_DIM};
    padding: 9px 20px;
    border: 1px solid transparent;
    border-bottom: none;
    border-radius: 8px 8px 0 0;
    margin-right: 3px;
    font-family: '{UI_FONT}', sans-serif;
    font-size: 13px;
    min-width: 100px;
}}
QTabBar::tab:selected {{
    background: {C_SURFACE};
    color: {C_TEXT};
    border-color: {C_BORDER};
    font-weight: bold;
}}
QTabBar::tab:hover:!selected {{
    background: {C_SURFACE2};
    color: {C_TEXT};
    border-color: {C_BORDER};
}}

/* ── Labels ──────────────────────────────────────────── */
QLabel#appTitle {{
    font-size: 20px;
    font-weight: bold;
    color: {C_TEXT};
    font-family: '{UI_FONT}', sans-serif;
}}
QLabel#appSubtitle {{
    font-size: 12px;
    color: {C_TEXT_DIM};
    font-family: '{UI_FONT}', sans-serif;
    letter-spacing: 0.3px;
}}
QLabel#statusLabel {{
    color: {C_TEXT_DIM};
    font-size: 12px;
}}
QLabel#accentLabel {{
    color: {C_ACCENT};
    font-size: 12px;
    font-weight: bold;
}}
QLabel#videoInfoLabel {{
    color: {C_ACCENT};
    font-size: 12px;
    font-weight: bold;
    padding: 3px 8px;
    background: rgba(88,166,255,0.1);
    border: 1px solid rgba(88,166,255,0.3);
    border-radius: 6px;
}}
QLabel#progressLabel {{
    color: {C_TEXT_DIM};
    font-size: 12px;
    padding-left: 2px;
}}
QLabel#sectionTitle {{
    font-size: 11px;
    font-weight: bold;
    color: {C_TEXT_DIM};
    font-family: '{UI_FONT}', sans-serif;
    letter-spacing: 1px;
    text-transform: uppercase;
}}

/* ── Checkboxes ──────────────────────────────────────── */
QCheckBox {{
    spacing: 8px;
    color: {C_TEXT};
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1.5px solid {C_BORDER};
    background: {C_SURFACE2};
}}
QCheckBox::indicator:hover {{
    border-color: {C_ACCENT};
}}
QCheckBox::indicator:checked {{
    background: {C_ACCENT};
    border-color: {C_ACCENT};
}}

/* ── Tooltip ─────────────────────────────────────────── */
QToolTip {{
    background-color: {C_SURFACE2};
    color: {C_TEXT};
    border: 1px solid {C_BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}}

/* ── Splitter ────────────────────────────────────────── */
QSplitter::handle {{
    background: {C_BORDER};
    width: 1px;
    margin: 4px 0;
}}
QSplitter::handle:hover {{
    background: {C_ACCENT};
}}

/* ── Status bar ──────────────────────────────────────── */
QStatusBar {{
    background: {C_SURFACE};
    color: {C_TEXT_DIM};
    border-top: 1px solid {C_BORDER};
    font-size: 12px;
    padding: 2px 8px;
}}

/* ── Message boxes ───────────────────────────────────── */
QMessageBox {{
    background-color: {C_SURFACE};
}}
QMessageBox QLabel {{
    color: {C_TEXT};
    font-size: 13px;
}}
"""

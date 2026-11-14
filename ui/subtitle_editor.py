"""
Subtitle Editor Widget - Editable table showing all segments with timestamps,
original text, and Khmer translation side by side.
Khmer column uses Noto Sans Khmer font for correct rendering.
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QAbstractItemView, QComboBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from ui.styles import KHMER_FONT_PRIMARY, KHMER_FONT_FALLBACK, KHMER_FONT_SYSTEM, UI_FONT


def khmer_font(size: int = 15) -> QFont:
    """Return the best available Khmer font."""
    from PyQt6.QtGui import QFontDatabase
    available = QFontDatabase.families()
    for name in [KHMER_FONT_PRIMARY, KHMER_FONT_FALLBACK, KHMER_FONT_SYSTEM, "Khmer UI", "Khmer"]:
        if name in available:
            f = QFont(name, size)
            return f
    return QFont("Arial", size)


# Available Khmer font choices for the font selector
KHMER_FONT_CHOICES = [
    "Noto Sans Khmer",
    "Khmer OS",
    "Khmer OS Content",
    "Khmer OS Siemreap",
    "Kantumruy",
    "Battambang",
    "Hanuman",
    "Siemreap",
    "Khmer UI",
    "Bayon",
    "Moul",
]


class SubtitleEditorWidget(QWidget):
    """Editable table of transcription/translation segments with Khmer font support."""

    segments_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.segments = []
        self._khmer_font = khmer_font(15)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ── Header ────────────────────────────────────────────────
        header_layout = QHBoxLayout()

        title = QLabel("Subtitle Editor")
        title.setObjectName("titleLabel")
        title_font = QFont(UI_FONT, 13)
        title_font.setBold(True)
        title.setFont(title_font)

        self.segment_count_label = QLabel("0 segments")
        self.segment_count_label.setObjectName("statusLabel")

        # Khmer font selector
        font_label = QLabel("Khmer Font:")
        font_label.setObjectName("statusLabel")

        self.font_combo = QComboBox()
        self.font_combo.setMaximumWidth(200)
        from PyQt6.QtGui import QFontDatabase
        available = QFontDatabase.families()
        for fname in KHMER_FONT_CHOICES:
            if fname in available:
                self.font_combo.addItem(fname)
        # Add all other installed Khmer fonts not in the preset list
        for fname in sorted(available):
            if "Khmer" in fname and fname not in KHMER_FONT_CHOICES:
                self.font_combo.addItem(fname)

        self.font_combo.currentTextChanged.connect(self._on_font_changed)

        # Font size selector
        size_label = QLabel("Size:")
        size_label.setObjectName("statusLabel")
        self.size_combo = QComboBox()
        self.size_combo.setMaximumWidth(65)
        for sz in ["12", "13", "14", "15", "16", "18", "20", "22"]:
            self.size_combo.addItem(sz)
        self.size_combo.setCurrentText("15")
        self.size_combo.currentTextChanged.connect(self._on_font_size_changed)

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.segment_count_label)
        header_layout.addSpacing(16)
        header_layout.addWidget(font_label)
        header_layout.addWidget(self.font_combo)
        header_layout.addWidget(size_label)
        header_layout.addWidget(self.size_combo)
        layout.addLayout(header_layout)

        # ── Table ─────────────────────────────────────────────────
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Start", "End", "Original Text", "ភាសាខ្មែរ (Khmer)"
        ])

        # Set Khmer font on the last header label
        header_font = QFont(UI_FONT, 10)
        header_font.setBold(True)
        self.table.horizontalHeader().setFont(header_font)

        # Column sizing
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(55)
        self.table.itemChanged.connect(self._on_item_changed)

        layout.addWidget(self.table)

        # ── Buttons ───────────────────────────────────────────────
        btn_layout = QHBoxLayout()
        self.add_row_btn = QPushButton("+ Add Row")
        self.del_row_btn = QPushButton("Delete Row")
        self.add_row_btn.clicked.connect(self._add_row)
        self.del_row_btn.clicked.connect(self._delete_row)
        btn_layout.addWidget(self.add_row_btn)
        btn_layout.addWidget(self.del_row_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    # ── Font handling ─────────────────────────────────────────────

    def _on_font_changed(self, font_name: str):
        """Update Khmer font when user picks a different one."""
        size = int(self.size_combo.currentText())
        self._khmer_font = QFont(font_name, size)
        self._refresh_khmer_column_font()

    def _on_font_size_changed(self, size_str: str):
        """Update font size."""
        try:
            size = int(size_str)
            self._khmer_font.setPointSize(size)
            self._refresh_khmer_column_font()
            self.table.verticalHeader().setDefaultSectionSize(max(50, size + 38))
        except ValueError:
            pass

    def _refresh_khmer_column_font(self):
        """Re-apply the Khmer font to every cell in column 3."""
        self.table.blockSignals(True)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 3)
            if item:
                item.setFont(self._khmer_font)
        self.table.blockSignals(False)

    # ── Data loading ──────────────────────────────────────────────

    def load_segments(self, segments):
        """Populate table from TranscriptionSegment list."""
        self.segments = segments
        self.table.blockSignals(True)
        self.table.setRowCount(len(segments))

        orig_font = QFont(UI_FONT, 13)

        for i, seg in enumerate(segments):
            # Start
            start_item = QTableWidgetItem(f"{seg.start:.2f}s")
            start_item.setFlags(start_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            start_item.setForeground(QColor("#4fc3f7"))
            start_item.setFont(QFont(UI_FONT, 11))
            self.table.setItem(i, 0, start_item)

            # End
            end_item = QTableWidgetItem(f"{seg.end:.2f}s")
            end_item.setFlags(end_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            end_item.setForeground(QColor("#4fc3f7"))
            end_item.setFont(QFont(UI_FONT, 11))
            self.table.setItem(i, 1, end_item)

            # Original text
            orig_item = QTableWidgetItem(seg.text)
            orig_item.setFont(orig_font)
            orig_item.setForeground(QColor("#e0e0e0"))
            self.table.setItem(i, 2, orig_item)

            # Khmer text — Khmer font + gold colour
            khmer_item = QTableWidgetItem(seg.khmer_text or "")
            khmer_item.setFont(self._khmer_font)
            khmer_item.setForeground(QColor("#ffd700"))
            self.table.setItem(i, 3, khmer_item)

        self.table.blockSignals(False)
        self.segment_count_label.setText(f"{len(segments)} segments")

    def get_segments(self):
        """Read back edited data from the table into the segments list."""
        for i, seg in enumerate(self.segments):
            orig_item = self.table.item(i, 2)
            khmer_item = self.table.item(i, 3)
            if orig_item:
                seg.text = orig_item.text()
            if khmer_item:
                seg.khmer_text = khmer_item.text()
        return self.segments

    def _on_item_changed(self, item):
        row = item.row()
        col = item.column()
        if row < len(self.segments):
            if col == 2:
                self.segments[row].text = item.text()
            elif col == 3:
                self.segments[row].khmer_text = item.text()
                item.setFont(self._khmer_font)
                item.setForeground(QColor("#ffd700"))
        self.segments_changed.emit()

    def _add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem("0.00s"))
        self.table.setItem(row, 1, QTableWidgetItem("0.00s"))
        self.table.setItem(row, 2, QTableWidgetItem(""))
        khmer_item = QTableWidgetItem("")
        khmer_item.setFont(self._khmer_font)
        khmer_item.setForeground(QColor("#ffd700"))
        self.table.setItem(row, 3, khmer_item)

    def _delete_row(self):
        selected_rows = sorted(
            set(item.row() for item in self.table.selectedItems()),
            reverse=True,
        )
        for row in selected_rows:
            self.table.removeRow(row)
            if row < len(self.segments):
                self.segments.pop(row)
        self.segment_count_label.setText(f"{len(self.segments)} segments")

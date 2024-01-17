from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QValidator
from PyQt6.QtWidgets import QLabel, QLineEdit, QVBoxLayout, QWidget


class Note(QWidget):
    value_changed = pyqtSignal()

    def __init__(
        self, text: str, note: str, editable: bool = False, validator: QValidator = None, parent: QWidget = None
    ) -> None:
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setMinimumWidth(40)
        self.setMaximumWidth(80)

        layout = QVBoxLayout()
        self.setLayout(layout)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 5, 0, 5)

        self.value = QLineEdit(text)
        self.value.setEnabled(editable)
        if validator is not None:
            self.value.setValidator(validator)
        self.value.setStyleSheet("background-color: transparent; border: none; color: #dc7e23")
        self.value.setFont(QFont("Times New Roman", 14))
        self.value.setAlignment(Qt.AlignmentFlag.AlignCenter)

        note: QLabel = QLabel(note)
        note.setStyleSheet("background-color: transparent; color: #000000;")
        note.setFont(QFont("Times New Roman", 10))
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.value)
        layout.addWidget(note)

        self.value.editingFinished.connect(self.change_value)

    @property
    def text(self):
        return self.value.text()

    def set_value(self, t: str):
        self.value.setText(t)

    def change_value(self):
        self.value_changed.emit()

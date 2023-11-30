from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QLabel, QPushButton, QWidget


class FoldedItem(QPushButton):
    def __init__(parent: QWidget = None):
        super().__init__(parent)

    def setIcon(self, pixmap: QPixmap):
        pass

    # def setTe

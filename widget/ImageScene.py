from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import QGraphicsScene, QWidget


class ImageScene(QGraphicsScene):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        # 默认黑色背景
        self.setBackgroundBrush(QBrush(QColor("#000000")))

    def setBackGroudColor(self, color: QColor):
        self.setBackgroundBrush(QBrush(color))

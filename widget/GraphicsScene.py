from PyQt6.QtGui import QBrush, QColor
from PyQt6.QtWidgets import QGraphicsScene, QWidget


class GraphicsScene(QGraphicsScene):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        # 设置背景为黑色
        self.setBackgroundBrush(QBrush(QColor("#000000")))

    def setBackGroudColor(self, color: QColor):
        self.setBackgroundBrush(QBrush(color))

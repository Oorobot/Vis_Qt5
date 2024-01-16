from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtWidgets import QApplication, QGraphicsView, QWidget


class MyWidget(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.clickPosition = None  # 用于存储点击位置

    def mousePressEvent(self, event):
        self.clickPosition = event.position()  # 保存鼠标点击位置
        self.update()  # 触发重绘

    def drawForeground(self, painter, rect):
        if self.clickPosition:
            # 设置画笔
            pen = QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.SolidLine)
            painter.setPen(pen)

            # 绘制十字线
            x = self.clickPosition.x()
            y = self.clickPosition.y()
            painter.drawLine(QPointF(x, 0), QPointF(x, self.height()))
            painter.drawLine(QPointF(0, y), QPointF(self.width(), y))


# PyQt 应用程序
app = QApplication([])
window = MyWidget()
window.show()
app.exec()

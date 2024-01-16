import math
from typing import Union

import numpy as np
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QImage, QPainter, QPixmap
from PyQt6.QtWidgets import QGraphicsPixmapItem, QStyleOptionGraphicsItem, QWidget


class ImageItem(QGraphicsPixmapItem):
    def __init__(self, array: np.ndarray) -> None:
        # 初始化
        image = QImage(
            array.data.tobytes(),
            array.shape[1],
            array.shape[0],
            array.shape[1] * 3,
            QImage.Format.Format_RGB888,
        )
        pixmap = QPixmap.fromImage(image)
        super(ImageItem, self).__init__(pixmap)

        # 属性
        self.w, self.h = self.pixmap().width(), self.pixmap().height()
        self.left, self.top = math.ceil(-self.w / 2.0), math.ceil(-self.h / 2.0)

    def boundingRect(self) -> QRectF:
        return QRectF(self.left, self.top, self.w, self.h)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Union[QWidget, None]) -> None:
        painter.drawPixmap(self.left, self.top, self.pixmap())

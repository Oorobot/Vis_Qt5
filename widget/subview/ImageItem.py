from typing import Union

import numpy as np
from matplotlib.colors import Colormap
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QImage, QPainter, QPixmap
from PyQt6.QtWidgets import QGraphicsPixmapItem, QStyleOptionGraphicsItem, QWidget

from utility.common import float_01_to_uint8_0255


class ImageItem(QGraphicsPixmapItem):
    def __init__(self, array: np.ndarray, colorMap: Colormap = None) -> None:
        if colorMap is not None:
            array = float_01_to_uint8_0255(colorMap(array))
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
        self.left, self.top = round(-self.w / 2), round(-self.h / 2)

    def boundingRect(self) -> QRectF:
        return QRectF(self.left, self.top, self.w, self.h)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Union[QWidget, None]) -> None:
        painter.drawPixmap(self.left, self.top, self.pixmap())

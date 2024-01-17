import cv2
import numpy as np
from PyQt6.QtCore import QPointF, QRectF
from PyQt6.QtGui import QColor, QPainter, QPainterPath, QPolygonF
from PyQt6.QtWidgets import QGraphicsPixmapItem, QStyleOptionGraphicsItem, QWidget

from utility.common import get_colors


class ImageItem2(QGraphicsPixmapItem):
    def __init__(self, array: np.ndarray, opacity: float = 0.5) -> None:
        # 初始化
        super(ImageItem2, self).__init__()

        # 属性
        self.setOpacity(opacity)
        self.w, self.h = array.shape[1], array.shape[0]
        self.left, self.top = -self.w / 2.0, -self.h / 2.0

        # 找到需要标注的位置及其颜色
        num_color = array.max()
        self.paths = []

        if num_color == 0:
            return

        colors = get_colors(num_color)

        for i in range(1, num_color + 1):
            arr = np.where(array == i, 1, 0).astype(np.uint8)
            contours, _ = cv2.findContours(arr, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            path = QPainterPath()
            for contour in contours:
                path.addPolygon(QPolygonF([QPointF(c[0] + self.left, c[1] + self.top) for c in contour[:, 0, :]]))
            self.paths.append([path, colors[i - 1]])

    def boundingRect(self) -> QRectF:
        return QRectF(self.left, self.top, self.w, self.h)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget) -> None:
        for path in self.paths:
            painter.fillPath(path[0], QColor(*[int(p * 255) for p in path[1]]))

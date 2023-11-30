from typing import Union

from PyQt6 import QtGui
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import QGraphicsPixmapItem, QStyleOptionGraphicsItem, QWidget


class ImageItem(QGraphicsPixmapItem):
    _left, _top, _w, _h = -1.0, -1.0, 1.0, 1.0
    _view_w, _view_h = 1.0, 1.0

    def __init__(self, pixmap: QPixmap) -> None:
        super(ImageItem, self).__init__(pixmap)

        # 属性
        self._w, self._h = self.pixmap().width(), self.pixmap().height()
        self._left, self._top = -self._w / 2, -self._h / 2

    def boundingRect(self) -> QRectF:
        return QRectF(self._left, self._top, self._w, self._h)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Union[QWidget, None]) -> None:
        self.setOffset(self._left, self._top)
        painter.drawPixmap(self._left, self._top, self.pixmap())

    def setQGraphicsViewWH(self, w: float, h: float):
        self._view_w, self._view_h = w, h
        scale_factor = min(self._view_w * 1.0 / self._w, self._view_h * 1.0 / self._h)
        self.setScale(scale_factor)

    def reset(self):
        scale_factor = min(self._view_w * 1.0 / self._w, self._view_h * 1.0 / self._h)
        self.setScale(scale_factor)

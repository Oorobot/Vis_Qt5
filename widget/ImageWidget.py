from typing import Union

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsSceneMouseEvent,
    QGraphicsSceneWheelEvent,
    QStyleOptionGraphicsItem,
    QWidget,
)


class ImageWidget(QGraphicsPixmapItem):
    w_offset, h_offset = 0, 0
    w_offset_mouse, h_offset_mouse = 0, 0
    w_graphics_view, h_graphics_view = 0, 0

    def __init__(self, pixmap: QPixmap) -> None:
        super(ImageWidget, self).__init__(pixmap)
        self.acceptDrops()
        self.setAcceptHoverEvents(True)
        self.scale_default = 1
        self.scale_value = 1
        self.is_move = False
        self.start_pos = None

    def boundingRect(self) -> QRectF:
        self.w_offset = self.pixmap().width() / 2
        self.h_offset = self.pixmap().height() / 2
        return QRectF(
            -self.w_offset,
            -self.h_offset,
            self.pixmap().width(),
            self.pixmap().height(),
        )

    def paint(
        self,
        painter: QPainter,
        option: QStyleOptionGraphicsItem,
        widget: Union[QWidget, None],
    ) -> None:
        self.setOffset(-self.w_offset, -self.h_offset)
        painter.drawPixmap(-self.w_offset, -self.h_offset, self.pixmap())

    def setQGraphicsViewWH(self, w: int, h: int):
        self.w_graphics_view, self.h_graphics_view = w, h
        self.scale_default = min(w * 1.0 / self.pixmap().width(), h * 1.0 / self.pixmap().height())
        self.scale_value = self.scale_default
        self.setScale(self.scale_value)

    def resetItemPos(self):
        self.scale_value = self.scale_default
        self.setScale(self.scale_value)
        self.setPos(0, 0)

    def mousePressEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_move = True
            self.start_pos = event.pos()

    def mouseMoveEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        if self.is_move:
            point: QPointF = (event.pos() - self.start_pos) * self.scale_value
            self.moveBy(point.x(), point.y())
            print("bounding rect:", self.boundingRect())
            print("pos:", self.pos())

    def mouseReleaseEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        self.is_move = False

    def wheelEvent(self, event: QGraphicsSceneWheelEvent) -> None:
        if event.delta() > 0:
            self.scale_value = self.scale_value + 0.1
            if self.scale_value >= self.scale_default * 10:
                self.scale_value = self.scale_default * 10
        if event.delta() < 0:
            self.scale_value = self.scale_value - 0.1
            if self.scale_value <= self.scale_default * 0.1:
                self.scale_value = self.scale_default * 0.1
        self.setScale(self.scale_value)
        print("delta: ", event.delta(), ", scale_value: ", self.scale_value, ", scale_default: ", self.scale_default)

    def mouseDoubleClickEvent(self, event: QGraphicsSceneMouseEvent) -> None:
        print("bounding rect:", self.boundingRect())
        print("pos:", self.pos())
        self.resetItemPos()

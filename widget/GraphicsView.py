from typing import Union

import numpy as np
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QImage, QPainter, QPixmap, QResizeEvent, QWheelEvent
from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsScene, QGraphicsView, QStyleOptionGraphicsItem, QWidget

from entity import MedicalImage


class ImageItem(QGraphicsPixmapItem):
    def __init__(self, pixmap: QPixmap) -> None:
        # 定义成员属性
        self._left, self._top, self._w, self._h = -1.0, -1.0, 1.0, 1.0
        self._view_w, self._view_h = 1.0, 1.0

        # 初始化
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


class GraphicsScene(QGraphicsScene):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        # 设置背景为黑色
        self.setBackgroundBrush(QBrush(QColor("#000000")))

    def setBackGroudColor(self, color: QColor):
        self.setBackgroundBrush(QBrush(color))


class GraphicsView(QGraphicsView):
    def __init__(self, scene: GraphicsScene, parent: QWidget = None):
        # 定义成员属性
        self._image, self._label = None, None
        self._view = "t"

        # 初始化
        super().__init__(parent)

        self.setScene(scene)

        # 抗锯齿
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        # 更新模式
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # 隐藏滚动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 设置拖动
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        # 设置缩放中心
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        # 缩放
        self._scale_factor = 1.05
        self._scale_default = (1.0, 1.0)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.angleDelta().y() > 0:
            scale_factor = self._scale_factor
        else:
            scale_factor = 1 / self._scale_factor
        self.scale(scale_factor, scale_factor)

    def setScaleDefault(self, sx, sy):
        self._scale_default = (sx, sy)
        self.scale(sx, sy)

    def reset(self) -> None:
        # 恢复初始状态
        self.resetTransform()
        self.scale(self._scale_default[0], self._scale_default[1])
        self.centerOn(0, 0)

    def resizeEvent(self, event: QResizeEvent) -> None:
        # scene 的大小随着 view 变化
        super().resizeEvent(event)
        w, h = event.size().width(), event.size().height()
        self.scene().setSceneRect(-w * 3 / 2, -h * 3 / 2, w * 3, h * 3)

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        return super().drawForeground(painter, rect)

    def setView(self, view: str):
        self._view = view

    def setImageItem(self, image2D: np.ndarray):
        # 清空 scene
        self.scene().clear()

        # 创建 ImageItem
        imageQ = QImage(
            image2D.data.tobytes(),
            image2D.shape[1],
            image2D.shape[0],
            image2D.shape[1] * self._image.channel,
            QImage.Format.Format_Grayscale8 if self._image.channel == 1 else QImage.Format.Format_RGB888,
        )
        pixmap = QPixmap.fromImage(imageQ)
        imageItem = ImageItem(pixmap)
        # 缩放至填满 view
        imageItem.setQGraphicsViewWH(self.width(), self.height())
        self.scene().addItem(imageItem)

    def setImage(self, image: MedicalImage):
        self._image = image
        self.setImageItem(self._image.plane(self._view))

    def changeSliceOfImage(self, value: int):
        if self._image is not None:
            self._image.position[self._view] = value
            self.setImageItem(self._image.plane(self._view))

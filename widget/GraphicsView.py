from PyQt6 import QtCore, QtGui
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QPainter, QResizeEvent, QWheelEvent
from PyQt6.QtWidgets import QGraphicsView, QWidget

from entity import ReadImage
from widget.GraphicsScene import GraphicsScene
from widget.ImageItem import ImageItem


class GraphicsView(QGraphicsView):
    _image, _label = None, None

    def __init__(self, scene: GraphicsScene, parent: QWidget = None):
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

    def setImageItem(self, fileName: str):
        pass

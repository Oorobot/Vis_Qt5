from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QWheelEvent
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget

from widget.ImageItem import ImageItem


class GraphicsView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, parent: QWidget = None):
        super().__init__(parent)

        self._scene = scene
        self.setScene(self._scene)

        self.setRenderHints(
            QPainter.RenderHint.Antialiasing
            | QPainter.RenderHint.TextAntialiasing
            | QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)

        # 隐藏滚动条
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # 设置缩放中心
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        # 缩放
        self._scale_default_factor = 1.05
        self._scale_default = (1.0, 1.0)
        self._scale_value = (1.0, 1.0)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if event.angleDelta().y() > 0:
            scale_factor = self._scale_default_factor
        else:
            scale_factor = 1 / self._scale_default_factor
        self._scale_value = (s * scale_factor for s in self._scale_value)
        self.scale(scale_factor, scale_factor)

    def reset(self) -> None:
        self.resetTransform()
        for item in self.scene().items():
            if isinstance(item, ImageItem):
                item.reset()

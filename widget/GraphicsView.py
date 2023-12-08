from typing import Union

import numpy as np
from PyQt6 import QtCore
from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QAction, QBrush, QColor, QIcon, QImage, QPainter, QPen, QPixmap, QResizeEvent, QWheelEvent
from PyQt6.QtWidgets import *

from entity import MedicalImage, ReadNIFTI


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
        painter.drawPixmap(round(self._left), round(self._top), self.pixmap())

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
    def __init__(self, scene: GraphicsScene, view: str, parent: QWidget = None):
        # 定义成员属性
        self._image, self._label = None, None
        self._view = view
        self._imageItem, self_labelItem = None, None

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
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.resizeOrSlide = False
        # 设置缩放中心
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        # 缩放
        self._scale_factor = 1.05
        self._scale_default = (1.0, 1.0)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.resizeOrSlide:
            if event.angleDelta().y() > 0:
                scale_factor = self._scale_factor
            else:
                scale_factor = 1 / self._scale_factor
            self.scale(scale_factor, scale_factor)
        else:
            if self._image is not None:
                if event.angleDelta().y() > 0:
                    self._image.positionSub(self._view)
                else:
                    self._image.positionAdd(self._view)
                self.setImageItem(self._image.plane(self._view))
                self.parent().slideInfo.setText(
                    "{:0>4d}|{:0>4d}".format(self._image.position[self._view], self._image.size[self._view])
                )

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
        w, h = event.size().width(), event.size().height()
        self.scene().setSceneRect(-w * 10, -h * 10, w * 20, h * 20)

    # 切换视图
    def setView(self, view: str):
        self._view = view
        self.setImageItem(self._image.plane(self._view))
        self.parent().slideInfo.setText(
            "{:0>4d}|{:0>4d}".format(self._image.position[self._view], self._image.size[self._view])
        )

    # 设置ImageItem
    def setImageItem(self, image2D: np.ndarray):
        # 清除图像
        if self._imageItem is not None:
            self.scene().removeItem(self._imageItem)

        # 创建 ImageItem
        imageQ = QImage(
            image2D.data.tobytes(),
            image2D.shape[1],
            image2D.shape[0],
            image2D.shape[1] * self._image.channel,
            QImage.Format.Format_Grayscale8 if self._image.channel == 1 else QImage.Format.Format_RGB888,
        )
        pixmap = QPixmap.fromImage(imageQ)
        self._imageItem = ImageItem(pixmap)
        # 缩放至填满 view
        self._imageItem.setQGraphicsViewWH(self.width(), self.height())
        self.scene().addItem(self._imageItem)

    # 切换图像
    def setImage(self, image: MedicalImage):
        self._image = image
        self.setImageItem(self._image.plane(self._view))

    def setLabelItem(self, label2D: np.ndarray):
        pass

    def setLabel(self, label: MedicalImage):
        self._label = label
        self.setLabelItem(self._label.plane(self._view))


class ImageDisplayer(QWidget):
    VIEW_NAME = {"s": "矢状面", "c": "冠状面", "t": "横截面"}

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        toolbar = QToolBar(self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        resetBtn = QToolButton()
        resetBtn.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        resetBtn.setIcon(QIcon("resource/reset.png"))
        resetBtn.setText("复原")
        toolbar.addWidget(resetBtn)
        toolbar.addSeparator()

        arrowBtn = QToolButton()
        arrowBtn.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        arrowIcon = QIcon("resource/arrow.png")
        arrowBtn.setIcon(arrowIcon)
        arrowBtn.setText("普通")
        dragBtn = QToolButton()
        dragIcon = QIcon("resource/drag.png")
        dragBtn.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        dragBtn.setText("拖动")
        dragBtn.setIcon(dragIcon)

        toolbar.addWidget(arrowBtn)
        toolbar.addWidget(dragBtn)
        toolbar.addSeparator()

        resizeBtn = QToolButton()
        resizeIcon = QIcon("resource/resize.png")
        resizeBtn.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        resizeBtn.setIcon(resizeIcon)
        resizeBtn.setText("缩放")
        slideBtn = QToolButton()
        slideIcon = QIcon("resource/slide.png")
        slideBtn.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        slideBtn.setText("切换")
        slideBtn.setIcon(slideIcon)

        toolbar.addWidget(resizeBtn)
        toolbar.addWidget(slideBtn)
        toolbar.addSeparator()

        viewBtn = QToolButton()
        viewBtn.setAutoRaise(True)
        viewBtn.setIcon(QIcon("resource/view.png"))
        viewBtn.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        viewSubMenu = QMenu()
        viewBtn.setText("视图")
        viewBtn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        viewS = viewSubMenu.addAction(QIcon("resource/S.png"), "矢状面")
        viewC = viewSubMenu.addAction(QIcon("resource/C.png"), "冠状面")
        viewT = viewSubMenu.addAction(QIcon("resource/T.png"), "横截面")
        viewBtn.setMenu(viewSubMenu)
        toolbar.addWidget(viewBtn)
        toolbar.addSeparator()

        toolInfoLayout = QHBoxLayout()
        toolInfoLayout.addWidget(toolbar)
        toolInfoLayout.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        self.viewInfo = QLabel()
        self.viewInfo.setText(self.VIEW_NAME["t"])
        self.viewInfo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.slideInfo = QLabel()
        self.slideInfo.setText("{:0>4d}|{:0>4d}".format(0, 0))
        self.slideInfo.setFixedWidth(100)
        self.viewInfo.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        toolInfoLayout.addWidget(self.viewInfo)
        toolInfoLayout.addWidget(self.slideInfo)

        scene = QGraphicsScene()
        self.view = GraphicsView(scene, "t", self)

        layout = QVBoxLayout()
        layout.addLayout(toolInfoLayout)
        layout.addWidget(self.view)

        self.setLayout(layout)
        self.resize(1920, 1080)

        # 绑定函数
        resetBtn.clicked.connect(self.activateReset)
        arrowBtn.clicked.connect(self.deactivateDragMode)
        dragBtn.clicked.connect(self.activateDragMode)
        resizeBtn.clicked.connect(self.activateResizeMode)
        slideBtn.clicked.connect(self.activateSlideMode)

        viewS.triggered.connect(self.setViewS)
        viewC.triggered.connect(self.setViewC)
        viewT.triggered.connect(self.setViewT)

    # 复原
    def activateReset(self):
        self.view.reset()

    # 拖动
    def activateDragMode(self):
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    # 取消拖动
    def deactivateDragMode(self):
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    # 缩放
    def activateResizeMode(self):
        self.view.resizeOrSlide = True

    # 切换
    def activateSlideMode(self):
        self.view.resizeOrSlide = False

    def setViewS(self):
        self.view.setView("s")
        self.viewInfo.setText(self.VIEW_NAME["s"])

    def setViewC(self):
        self.view.setView("c")
        self.viewInfo.setText(self.VIEW_NAME["c"])

    def setViewT(self):
        self.view.setView("t")
        self.viewInfo.setText(self.VIEW_NAME["t"])


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    MainWindow = ImageDisplayer()
    image = ReadNIFTI(r"DATA\001_CT.nii.gz", True)
    MainWindow.view.setImage(image)
    MainWindow.show()
    sys.exit(app.exec())

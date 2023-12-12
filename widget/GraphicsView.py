from typing import Union

import numpy as np
from PyQt6.QtCore import *
from PyQt6.QtGui import *
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
    def __init__(self, view: str, parent: QWidget = None):
        # 定义成员属性
        self._image, self._label = None, None
        self._view = view
        self._imageItem, self_labelItem = None, None

        # 初始化
        super().__init__(parent)

        scene = GraphicsScene()
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
        resetBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        resetBtn.setIcon(QIcon("resource/reset.png"))
        resetBtn.setText("复原")
        toolbar.addWidget(resetBtn)
        toolbar.addSeparator()

        arrowBtn = QToolButton()
        arrowBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        arrowIcon = QIcon("resource/arrow.png")
        arrowBtn.setIcon(arrowIcon)
        arrowBtn.setText("普通")
        dragBtn = QToolButton()
        dragIcon = QIcon("resource/drag.png")
        dragBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        dragBtn.setText("拖动")
        dragBtn.setIcon(dragIcon)

        toolbar.addWidget(arrowBtn)
        toolbar.addWidget(dragBtn)
        toolbar.addSeparator()

        resizeBtn = QToolButton()
        resizeIcon = QIcon("resource/resize.png")
        resizeBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        resizeBtn.setIcon(resizeIcon)
        resizeBtn.setText("缩放")
        slideBtn = QToolButton()
        slideIcon = QIcon("resource/slide.png")
        slideBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        slideBtn.setText("切换")
        slideBtn.setIcon(slideIcon)

        toolbar.addWidget(resizeBtn)
        toolbar.addWidget(slideBtn)
        toolbar.addSeparator()

        viewBtn = QToolButton()
        viewBtn.setAutoRaise(True)
        viewBtn.setIcon(QIcon("resource/view.png"))
        viewBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        viewSubMenu = QMenu()
        viewBtn.setText("视图")
        viewBtn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        viewS = viewSubMenu.addAction(QIcon("resource/S.png"), "矢状面")
        viewC = viewSubMenu.addAction(QIcon("resource/C.png"), "冠状面")
        viewT = viewSubMenu.addAction(QIcon("resource/T.png"), "横截面")
        viewBtn.setMenu(viewSubMenu)
        toolbar.addWidget(viewBtn)
        toolbar.addSeparator()

        constrastBtn = QToolButton()
        constrastBtn.setText("对比度")
        constrastBtn.setIcon(QIcon("resource/constrast.png"))
        constrastBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.subWindowConstrast = SubWindowConstrast()
        toolbar.addWidget(constrastBtn)
        toolbar.addSeparator()

        toolInfoLayout = QHBoxLayout()
        toolInfoLayout.addWidget(toolbar)
        toolInfoLayout.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        font = QFont("黑体", 14)
        self.viewInfo = QLabel()
        self.viewInfo.setText(self.VIEW_NAME["t"])
        self.viewInfo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.viewInfo.setStyleSheet("background-color:transparent; color: rgb(255, 0, 0)")
        self.viewInfo.setFont(font)
        self.slideInfo = QLabel()
        self.slideInfo.setText("{:0>4d}|{:0>4d}".format(0, 0))
        self.slideInfo.setFixedWidth(100)
        self.slideInfo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slideInfo.setStyleSheet("background-color:transparent; color: rgb(255, 0, 0)")
        self.slideInfo.setFont(font)
        toolInfoLayout.addWidget(self.viewInfo)
        toolInfoLayout.addWidget(self.slideInfo)

        self.view = GraphicsView("t", self)

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
        constrastBtn.clicked.connect(self.activateConstrastWindow)

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

    # 对比度
    def activateConstrastWindow(self):
        self.subWindowConstrast.show()
        self.subWindowConstrast.constrastValue.connect(self.adjustConstrast)

    # 调整对比度
    def adjustConstrast(self, mi, ma):
        if self.view._image is not None:
            self.view._image.normlize(mi, ma)
            self.view.setImageItem(self.view._image.plane(self.view._view))

    def setViewS(self):
        self.view.setView("s")
        self.viewInfo.setText(self.VIEW_NAME["s"])

    def setViewC(self):
        self.view.setView("c")
        self.viewInfo.setText(self.VIEW_NAME["c"])

    def setViewT(self):
        self.view.setView("t")
        self.viewInfo.setText(self.VIEW_NAME["t"])

    def setImage(self, image: MedicalImage):
        mi, ma = image.array.min(), image.array.max()
        self.subWindowConstrast.editMin.setText(f"{mi:.2f}")
        self.subWindowConstrast.editMax.setText(f"{ma:.2f}")
        self.subWindowConstrast.editWindowLevel.setText(f"{(mi + ma) / 2:.2f}")
        self.subWindowConstrast.editWindowWidth.setText(f"{ma- mi:.2f}")
        self.view.setImage(image)


class SubWindowConstrast(QWidget):
    constrastValue = pyqtSignal(float, float)

    def __init__(self, mi=0.0, ma=0.0, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.resize(300, 100)

        self.setWindowTitle("对比度")
        validator = QDoubleValidator(self)

        labelMin = QLabel()
        labelMin.setText("最小值")
        labelMin.setFixedWidth(40)
        labelMin.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.editMin = QLineEdit()
        self.editMin.setText(str(mi))
        self.editMin.setFixedWidth(80)
        self.editMin.setValidator(validator)

        labelMax = QLabel()
        labelMax.setText("最大值")
        labelMax.setFixedWidth(40)
        labelMax.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.editMax = QLineEdit()
        self.editMax.setText(str(ma))
        self.editMax.setFixedWidth(80)
        self.editMax.setValidator(validator)

        layout1 = QHBoxLayout()
        layout1.setSpacing(0)
        layout1.setContentsMargins(0, 0, 10, 0)
        layout1.addWidget(labelMin)
        layout1.addWidget(self.editMin)
        layout1.addWidget(labelMax)
        layout1.addWidget(self.editMax)

        labelWindowLevel = QLabel()
        labelWindowLevel.setText("窗位")
        labelWindowLevel.setFixedWidth(40)
        labelWindowLevel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.editWindowLevel = QLineEdit()
        self.editWindowLevel.setText(str((mi + ma) / 2))
        self.editWindowLevel.setFixedWidth(80)
        self.editWindowLevel.setValidator(validator)

        labelWindowWidth = QLabel()
        labelWindowWidth.setText("窗宽")
        labelWindowWidth.setFixedWidth(40)
        labelWindowWidth.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.editWindowWidth = QLineEdit()
        self.editWindowWidth.setText(str(ma - mi))
        self.editWindowWidth.setFixedWidth(80)
        self.editWindowWidth.setValidator(validator)

        layout2 = QHBoxLayout()
        layout2.setSpacing(0)
        layout2.setContentsMargins(0, 0, 10, 0)
        layout2.addWidget(labelWindowLevel)
        layout2.addWidget(self.editWindowLevel)
        layout2.addWidget(labelWindowWidth)
        layout2.addWidget(self.editWindowWidth)

        btn = QPushButton()
        btn.setText("确定")
        btn.setFixedWidth(80)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(layout1)
        layout.addLayout(layout2)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(layout)

        #
        self.editMax.editingFinished.connect(lambda: self.valueChanged("min_max"))
        self.editMin.editingFinished.connect(lambda: self.valueChanged("min_max"))

        #
        self.editWindowLevel.editingFinished.connect(lambda: self.valueChanged("level_width"))
        self.editWindowWidth.editingFinished.connect(lambda: self.valueChanged("level_width"))

        #
        btn.clicked.connect(self.clicked)

    def valueChanged(self, param: str):
        if param == "min_max":
            mi = 0.0 if len(self.editMin.text()) == 0 else float(self.editMin.text())
            ma = 0.0 if len(self.editMin.text()) == 0 else float(self.editMax.text())
            if mi > ma:
                ma = mi
            self.editMin.setText(f"{mi:.2f}")
            self.editMax.setText(f"{ma:.2f}")
            self.editWindowLevel.setText(f"{(ma + mi) / 2:.2f}")
            self.editWindowWidth.setText(f"{ma - mi:.2f}")
        elif param == "level_width":
            level = 0.0 if len(self.editWindowLevel.text()) == 0 else float(self.editWindowLevel.text())
            width = 0.0 if len(self.editWindowWidth.text()) == 0 else float(self.editWindowWidth.text())
            self.editMin.setText(f"{level - width / 2:.2f}")
            self.editMax.setText(f"{level + width / 2:.2f}")
            self.editWindowLevel.setText(f"{level:.2f}")
            self.editWindowWidth.setText(f"{width:.2f}")
        else:
            raise Exception(f"not supprot param = {param}")

    def clicked(self):
        mi, ma = float(self.editMin.text()), float(self.editMax.text())
        self.constrastValue.emit(mi, ma)
        self.close()


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    MainWindow = ImageDisplayer()
    image = ReadNIFTI(r"DATA\001_CT.nii.gz", True)
    MainWindow.setImage(image)
    MainWindow.show()
    sys.exit(app.exec())

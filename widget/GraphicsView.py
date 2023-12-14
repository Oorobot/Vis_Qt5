import colorsys
from typing import Union

import cv2
import numpy as np
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from entity import MedicalImage, ReadDICOM, ReadNIFTI
from widget.subWidget.SubWindowConstrast import SubWindowConstrast

np.random.seed(66)


def _get_colors(num):
    assert num > 0
    colors = []
    for i in np.arange(0.0, 360.0, 360.0 / num):
        hue = i / 360
        lightness = (50 + np.random.rand() * 10) / 100.0
        saturation = (90 + np.random.rand() * 10) / 100.0
        colors.append(colorsys.hls_to_rgb(hue, lightness, saturation))
    return colors


class ImageItem(QGraphicsPixmapItem):
    def __init__(self, array: np.ndarray, channel: int) -> None:
        # 创建 ImageItem
        image = QImage(
            array.data.tobytes(),
            array.shape[1],
            array.shape[0],
            array.shape[1] * channel,
            QImage.Format.Format_Grayscale8 if channel == 1 else QImage.Format.Format_RGB888,
        )
        pixmap = QPixmap.fromImage(image)
        # 初始化
        super(ImageItem, self).__init__(pixmap)

        # 属性
        self._w, self._h = self.pixmap().width(), self.pixmap().height()
        self._left, self._top = round(-self._w / 2), round(-self._h / 2)

    def boundingRect(self) -> QRectF:
        return QRectF(self._left, self._top, self._w, self._h)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: Union[QWidget, None]) -> None:
        painter.drawPixmap(self._left, self._top, self.pixmap())


class LabelItem(QGraphicsPixmapItem):
    def __init__(self, array: np.ndarray, alpha: int = 127) -> None:
        # 初始化
        super(LabelItem, self).__init__()
        # 属性
        self._w, self._h = array.shape[1], array.shape[0]
        self._left, self._top = round(-self._w / 2), round(-self._h / 2)
        self.alpha = alpha

        # 找到需要标注的位置及其颜色
        uint8 = array.astype(np.uint8)
        num_color = uint8.max()
        colors = _get_colors(num_color)

        self.paths = []
        for i in range(1, num_color + 1):
            uint8_i = (uint8 == i).astype(np.uint8)
            contours, _ = cv2.findContours(uint8_i, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            path = QPainterPath()
            for contour in contours:
                path.addPolygon(QPolygonF([QPointF(c[0] + self._left, c[1] + self._top) for c in np.squeeze(contour)]))
            self.paths.append([path, colors[i - 1]])

    def boundingRect(self) -> QRectF:
        return QRectF(self._left, self._top, self._w, self._h)

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget) -> None:
        for path in self.paths:
            painter.fillPath(path[0], QColor(*[int(p * 255) for p in path[1]], self.alpha))


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
        self._imageItem, self._labelItem = None, None

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
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        # 缩放
        self._scale_factor = 1.05
        self._scale_default = {"s": (1.0, 1.0), "c": (1.0, 1.0), "t": (1.0, 1.0)}

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

                # 分割图
                if self._label is not None:
                    self._label.position[self._view] = self._image.position[self._view]
                    self.setLabelItem(self._label.planeOrigin(self._view))

                # 切换信息
                self.parent().slideInfo.setText(
                    "{:0>4d}|{:0>4d}".format(self._image.position[self._view], self._image.size[self._view])
                )

    def reset(self) -> None:
        size_s, size_c, size_t = (
            self._image.size["s"] * self._image.spacing[0],
            self._image.size["c"] * self._image.spacing[1],
            self._image.size["t"] * self._image.spacing[2],
        )
        _scale_s, _scale_c, _scale_t = (
            min(self.height() * 1.0 / size_t, self.width() * 1.0 / size_c),
            min(self.height() * 1.0 / size_t, self.width() * 1.0 / size_s),
            min(self.height() * 1.0 / size_c, self.width() * 1.0 / size_s),
        )
        self._scale_default = {
            "s": (self._image.spacing[1] * _scale_s, self._image.spacing[2] * _scale_s),
            "c": (self._image.spacing[0] * _scale_c, self._image.spacing[2] * _scale_c),
            "t": (self._image.spacing[0] * _scale_t, self._image.spacing[1] * _scale_t),
        }
        self.resetTransform()
        self.scale(self._scale_default[self._view][0], self._scale_default[self._view][1])  # x, y
        self.centerOn(0, 0)

    def resizeEvent(self, event: QResizeEvent) -> None:
        # scene 的大小随着 view 变化
        w, h = event.size().width(), event.size().height()
        self.scene().setSceneRect(-w * 10, -h * 10, w * 20, h * 20)

    # 切换视图
    def setView(self, view: str):
        self._view = view
        self.reset()
        self.setImageItem(self._image.plane(self._view))
        if self._label is not None:
            self.setLabelItem(self._label.planeOrigin(self._view))

    # 切换图像
    def setImage(self, image: MedicalImage):
        self._image = image
        self.reset()
        self.setImageItem(self._image.plane(self._view))

    # 设置ImageItem
    def setImageItem(self, imageArray: np.ndarray):
        if self._imageItem is not None:
            self.scene().removeItem(self._imageItem)  # 清除图像
        else:
            self.reset()  # 缩放

        self._imageItem = ImageItem(imageArray, self._image.channel)
        self.scene().addItem(self._imageItem)
        self.parent().slideInfo.setText(
            "{:0>4d}|{:0>4d}".format(self._image.position[self._view], self._image.size[self._view])
        )

    def setLabel(self, label: MedicalImage):
        self._label = label
        if (
            self._label.size["s"] != self._image.size["s"]
            or self._label.size["c"] != self._image.size["c"]
            or self._label.size["t"] != self._image.size["t"]
        ):
            messageBox = QMessageBox(
                QMessageBox.Icon.Warning, "警告", "分割图与图像的尺寸（size）不匹配。", QMessageBox.StandardButton.Close
            )
            messageBox.exec()
        else:
            self.setLabelItem(self._label.planeOrigin(self._view))

    def setLabelItem(self, labelArray: np.ndarray):
        if self._labelItem is not None:
            self.scene().removeItem(self._labelItem)  # 清除分割图
        self._labelItem = LabelItem(labelArray)
        self.scene().addItem(self._labelItem)

    # 水平镜像
    def horizontalFlip(self):
        horizontalFlip = QTransform()
        horizontalFlip.scale(-1, 1)
        self.setTransform(self.transform() * horizontalFlip)

    # 垂直镜像
    def verticalFlip(self):
        verticalFlip = QTransform()
        verticalFlip.scale(1, -1)
        self.setTransform(self.transform() * verticalFlip)


class ImageDisplayer(QWidget):
    VIEW_NAME = {"s": "矢状面", "c": "冠状面", "t": "横截面"}

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        toolbar = QToolBar(self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        resetBtn = QToolButton()
        resetBtn.setText("复原")
        resetBtn.setIcon(QIcon("resource/reset.png"))
        resetBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(resetBtn)
        toolbar.addSeparator()

        arrowBtn = QToolButton()
        arrowBtn.setText("普通")
        arrowBtn.setIcon(QIcon("resource/arrow.png"))
        arrowBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        dragBtn = QToolButton()
        dragBtn.setText("拖动")
        dragBtn.setIcon(QIcon("resource/drag.png"))
        dragBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(arrowBtn)
        toolbar.addWidget(dragBtn)
        toolbar.addSeparator()

        resizeBtn = QToolButton()
        resizeBtn.setText("缩放")
        resizeBtn.setIcon(QIcon("resource/resize.png"))
        resizeBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        slideBtn = QToolButton()
        slideBtn.setText("切换")
        slideBtn.setIcon(QIcon("resource/slide.png"))
        slideBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(resizeBtn)
        toolbar.addWidget(slideBtn)
        toolbar.addSeparator()

        viewBtn = QToolButton()
        viewBtn.setText("视图")
        viewBtn.setAutoRaise(True)
        viewBtn.setIcon(QIcon("resource/view.png"))
        viewBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        viewBtn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        viewSubMenu = QMenu()
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

        flipHBtn = QToolButton()
        flipHBtn.setText("水平")
        flipHBtn.setIcon(QIcon("resource/flipH.png"))
        flipHBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        flipVBtn = QToolButton()
        flipVBtn.setText("垂直")
        flipVBtn.setIcon(QIcon("resource/flipV.png"))
        flipVBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(flipHBtn)
        toolbar.addWidget(flipVBtn)
        toolbar.addSeparator()

        maskBtn = QToolButton()
        maskBtn.setText("分割图")
        maskBtn.setIcon(QIcon("resource/mask.png"))
        maskBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(maskBtn)
        toolbar.addSeparator()

        # 视图信息和切换信息
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
        flipHBtn.clicked.connect(self.flipHorizontal)
        flipVBtn.clicked.connect(self.flipVertical)
        maskBtn.clicked.connect(self.openMask)

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
        if self.view._label is not None:
            self.view.setLabelItem(self.view._label.planeOrigin(self.view._view))

    def flipHorizontal(self):
        self.view.horizontalFlip()

    def flipVertical(self):
        self.view.verticalFlip()

    def openMask(self):
        filename = QFileDialog().getOpenFileName(self, "选择文件", "./", filter="NIFTI(*.nii *.nii.gz);;")
        if len(filename[0]) == 0:
            return

        maskImage = ReadNIFTI(filename[0], True)
        self.setLabel(maskImage)

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

    def setLabel(self, label: MedicalImage):
        self.view.setLabel(label)


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    MainWindow = ImageDisplayer()
    image = ReadNIFTI(r"DATA\001_CT.nii.gz", True)
    # image = ReadDICOM(r"DATA\001\CT\ImageFileName000.dcm").popitem()
    # image = image[1].popitem()
    # image = image[1]
    # label = ReadNIFTI(r"DATA\001_Label_Body.nii.gz", True)
    # label.convertLabelMask()
    MainWindow.setImage(image)
    # MainWindow.setLabel(label)
    MainWindow.show()
    sys.exit(app.exec())

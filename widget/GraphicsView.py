from typing import Union

import cv2
import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QImage,
    QPainter,
    QPainterPath,
    QPixmap,
    QPolygonF,
    QResizeEvent,
    QTransform,
    QWheelEvent,
)
from PyQt6.QtWidgets import (
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QMessageBox,
    QStyleOptionGraphicsItem,
    QWidget,
)

from utility.common import get_colors
from utility.MedicalImage import MedicalImage


class ImageItem(QGraphicsPixmapItem):
    def __init__(self, array: np.ndarray, channel: int) -> None:
        # 初始化
        image = QImage(
            array.data.tobytes(),
            array.shape[1],
            array.shape[0],
            array.shape[1] * channel,
            QImage.Format.Format_Grayscale8 if channel == 1 else QImage.Format.Format_RGB888,
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


class LabelItem(QGraphicsPixmapItem):
    def __init__(self, array: np.ndarray, opacity: float = 0.5) -> None:
        # 初始化
        super(LabelItem, self).__init__()

        # 属性
        self.setOpacity(opacity)
        self.w, self.h = array.shape[1], array.shape[0]
        self.left, self.top = round(-self.w / 2), round(-self.h / 2)

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


class GraphicsScene(QGraphicsScene):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        # 设置背景为黑色
        self.setBackgroundBrush(QBrush(QColor("#000000")))

    def setBackGroudColor(self, color: QColor):
        self.setBackgroundBrush(QBrush(color))


class GraphicsView(QGraphicsView):
    positionChanged = pyqtSignal(int)

    def __init__(self, view: str, parent: QWidget = None):
        # 定义成员属性
        self.view = view
        self.image, self.label = None, None
        self.imageItem, self.labelItem = None, None
        self.__position = self.__positionMax = {"s": 1, "c": 1, "t": 1}

        self.scaleFactor = 1.05
        self.__scaleDefault = {"s": (1.0, 1.0), "c": (1.0, 1.0), "t": (1.0, 1.0)}

        self.resizeOrSlide = False

        self.labelOpacity = 0.50

        # 初始化
        super().__init__(parent)

        self.setScene(GraphicsScene())

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
        # 设置缩放中心
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

    @property
    def position(self):
        return self.__position[self.view]

    @position.setter
    def position(self, p: int):
        self.__position[self.view] = min(max(p, 1), self.position_max)

    @property
    def position_max(self):
        return self.__positionMax[self.view]

    @property
    def scale_default(self):
        return self.__scaleDefault[self.view]

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.resizeOrSlide:
            if event.angleDelta().y() > 0:
                factor = self.scaleFactor
            else:
                factor = 1 / self.scaleFactor
            self.scale(factor, factor)
        else:
            if event.angleDelta().y() > 0:
                self.position += 1
            else:
                self.position -= 1
            # 位置信息改变
            self.positionChanged.emit(self.position)
            self.setCurrentPlane()

    def reset(self) -> None:
        size_s, size_c, size_t = (s1 * s2 for s1, s2 in zip(self.image.size, self.image.spacing))
        _scale_s, _scale_c, _scale_t = (
            min(self.height() * 1.0 / size_t, self.width() * 1.0 / size_c),
            min(self.height() * 1.0 / size_t, self.width() * 1.0 / size_s),
            min(self.height() * 1.0 / size_c, self.width() * 1.0 / size_s),
        )
        self.__scaleDefault = {
            "s": (self.image.spacing[1] * _scale_s, self.image.spacing[2] * _scale_s),
            "c": (self.image.spacing[0] * _scale_c, self.image.spacing[2] * _scale_c),
            "t": (self.image.spacing[0] * _scale_t, self.image.spacing[1] * _scale_t),
        }
        self.resetTransform()
        self.scale(*self.scale_default)  # x, y
        self.centerOn(0, 0)

    def resizeEvent(self, event: QResizeEvent) -> None:
        # scene 的大小随着 view 变化
        w, h = event.size().width(), event.size().height()
        self.scene().setSceneRect(-w * 10, -h * 10, w * 20, h * 20)

    # 切换视图
    def setView(self, view: str):
        self.view = view
        self.reset()
        if self.image is not None:
            self.setImageItem(self.image.plane_norm(self.view, self.position))
        if self.label is not None:
            self.setLabelItem(self.label.plane_origin(self.view, self.position))

    # 切换图像
    def setImage(self, image: MedicalImage):
        self.image = image
        self.__position = {
            "s": self.image.size[0] // 2 + 1,
            "c": self.image.size[1] // 2 + 1,
            "t": self.image.size[2] // 2 + 1,
        }
        self.__positionMax = {
            "s": self.image.size[0],
            "c": self.image.size[1],
            "t": self.image.size[2],
        }
        self.reset()
        self.setImageItem(self.image.plane_norm(self.view, self.position))

    # 设置ImageItem
    def setImageItem(self, imageArray: np.ndarray):
        if self.imageItem is not None:
            self.scene().removeItem(self.imageItem)  # 清除图像
        else:
            self.reset()  # 缩放

        self.imageItem = ImageItem(imageArray, self.image.channel)
        self.scene().addItem(self.imageItem)

    def setLabel(self, label: MedicalImage):
        if self.image is None:
            messageBox = QMessageBox(QMessageBox.Icon.Warning, "警告", "打开图像", QMessageBox.StandardButton.Close)
            messageBox.exec()
        elif label.size != self.image.size:
            messageBox = QMessageBox(QMessageBox.Icon.Warning, "警告", "分割图与图像的大小不同", QMessageBox.StandardButton.Close)
            messageBox.exec()
        else:
            self.label = label
            self.setLabelItem(self.label.plane_origin(self.view, self.position))

    def setLabelItem(self, labelArray: np.ndarray):
        if self.labelItem is not None:
            self.scene().removeItem(self.labelItem)  # 清除分割图
        self.labelItem = LabelItem(labelArray, self.labelOpacity)
        self.scene().addItem(self.labelItem)

    def setLabelItemOpacity(self, v: float):
        self.labelOpacity = v
        if self.labelItem is not None:
            self.labelItem.setOpacity(self.labelOpacity)

    # 设置当前平面
    def setCurrentPlane(self):
        if self.image is not None:
            self.setImageItem(self.image.plane_norm(self.view, self.position))
        if self.label is not None:
            self.setLabelItem(self.label.plane_origin(self.view, self.position))

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

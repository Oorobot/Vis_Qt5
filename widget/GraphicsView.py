import numpy as np
from matplotlib.cm import get_cmap
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QResizeEvent, QTransform, QWheelEvent
from PyQt6.QtWidgets import QGraphicsView, QMessageBox, QWidget

from utility.MedicalImage import MedicalImage
from utility.MedicalImage2 import MedicalImage2
from widget.subview.GraphicsScene import GraphicsScene
from widget.subview.ImageItem import ImageItem
from widget.subview.LabelItem import LabelItem


class GraphicsView(QGraphicsView):
    positionChanged = pyqtSignal(int)

    def __init__(self, view: str, parent: QWidget = None):
        # 定义成员属性
        self.view = view
        self.image, self.label = None, None
        self.imageItem, self.labelItem = None, None
        self.__position = self.__positionMax = {"s": 1, "c": 1, "t": 1}

        self.colorMap = None

        self.scaleFactor = 1.05
        self.__scaleDefault = {"s": (1.0, 1.0), "c": (1.0, 1.0), "t": (1.0, 1.0)}

        self.resizeOrSlide = False

        self.labelOpacity = 0.50

        # 初始化
        super().__init__(parent)
        self.__scene = GraphicsScene()
        self.setScene(self.__scene)

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
            self.setLabelItem(self.label.plane(self.view, self.position))

    # 切换图像
    def setImage(self, image: MedicalImage):
        self.image = image
        # 位置信息
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
        # 映射颜色图
        if image.modality == "CT":
            self.colorMap = get_cmap("gray")
        elif image.modality == "PT" or image.modality == "NM":
            self.colorMap = get_cmap("binary")
        else:
            if image.channel == 1:
                self.colorMap = get_cmap("gray")
        # 设置背景色
        if self.colorMap is not None:
            self.__scene.setBackGroudColor(QColor(*[round(_ * 255) for _ in self.colorMap(0)]))
        # 初始化缩放信息
        self.reset()
        # 添加图像
        self.setImageItem(self.image.plane_norm(self.view, self.position))

    # 设置ImageItem
    def setImageItem(self, imageArray: np.ndarray):
        if self.imageItem is not None:
            self.scene().removeItem(self.imageItem)  # 清除图像
        else:
            self.reset()  # 缩放

        self.imageItem = ImageItem(imageArray, self.colorMap)
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
            self.setLabelItem(self.label.plane(self.view, self.position))

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
            self.setLabelItem(self.label.plane(self.view, self.position))

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

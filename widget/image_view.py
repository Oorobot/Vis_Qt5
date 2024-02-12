import copy
from typing import Union

import numpy as np
from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QMouseEvent, QPainter, QPen, QResizeEvent, QWheelEvent
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QWidget

from utility import MedicalImage, MedicalImage2

from .image_item import ImageItem
from .image_item2 import ImageItem2
from .message_box import warning


class ImageView(QGraphicsView):
    position_changed = pyqtSignal(int, int, int)

    def __init__(self, view: str, image: Union[MedicalImage, MedicalImage2], parent: QWidget = None):
        # 初始化
        super().__init__(parent)
        self.setScene(QGraphicsScene())
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
        # 设置缩放和变换中心
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        # 定义成员属性
        self.view = view
        self.image = None
        self.image_item: ImageItem = None
        self.label: MedicalImage = None
        self.label_item: ImageItem2 = None
        self.label_opacity: float = 0.50
        #
        self._position = {"s": 1, "c": 1, "t": 1}
        self._position_max = {"s": 1, "c": 1, "t": 1}
        #
        self._scale_current = {"s": (1.0, 1.0), "c": (1.0, 1.0), "t": (1.0, 1.0)}
        self._scale_default = None
        #
        self.set_image(image)

        self.resize_or_slide = False
        self._scene_pos = QPointF(0, 0)

        #
        self.PJI_mode = True
        self.PJI_box = None

    @property
    def position(self):
        return self._position[self.view]

    @position.setter
    def position(self, p: int):
        self._position[self.view] = min(max(p, 1), self.position_max)

    @property
    def position_max(self):
        return self._position_max[self.view]

    @property
    def scale_default(self):
        return self._scale_default[self.view]

    @property
    def scale_current(self):
        return self._scale_current[self.view]

    @scale_current.setter
    def scale_current(self, v):
        self._scale_current[self.view] = v

    @property
    def image_rect(self):
        return self.image_item.boundingRect()

    @property
    def image_value(self):
        return self.image.array[self._position["t"] - 1, self._position["c"] - 1, self._position["s"] - 1]

    @property
    def image_value_pt(self):
        if self.image.modality == "PTCT":
            return self.image.array_pt[self._position["t"] - 1, self._position["c"] - 1, self._position["s"] - 1]
        else:
            return 0

    @property
    def scene_pos(self):
        return self._scene_pos

    @scene_pos.setter
    def scene_pos(self, v: QPointF):
        if not self.image_rect.contains(v):
            if v.x() < self.image_rect.left():
                v.setX(self.image_rect.left())
            if v.x() > self.image_rect.right():
                v.setX(self.image_rect.right())
            if v.y() < self.image_rect.top():
                v.setY(self.image_rect.top())
            if v.y() > self.image_rect.bottom():
                v.setY(self.image_rect.bottom())
        self._scene_pos = v
        # 修改 position
        _pos = int(v.x() - self.image_rect.left()), int(v.y() - self.image_rect.top())
        if self.view == "t":
            self._position["s"], self._position["c"] = max(_pos[0], 1), max(_pos[1], 1)
        elif self.view == "c":
            self._position["s"], self._position["t"] = max(_pos[0], 1), max(_pos[1], 1)
        else:
            self._position["c"], self._position["t"] = max(_pos[0], 1), max(_pos[1], 1)
        self.position_changed.emit(self._position["s"], self._position["c"], self._position["t"])

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self.resize_or_slide:
            if event.angleDelta().y() > 0:
                factor = 1.05
            else:
                factor = 1 / 1.05
            self.scale(factor, factor)
            self.scale_current = (self.scale_current[0] * factor, self.scale_current[1] * factor)
        else:
            if event.angleDelta().y() > 0:
                self.position += 1
            else:
                self.position -= 1
            # 位置信息改变
            self.position_changed.emit(self._position["s"], self._position["c"], self._position["t"])

    def resizeEvent(self, event: QResizeEvent) -> None:
        # scene 的大小随着 view 变化
        w, h = event.size().width(), event.size().height()
        self.scene().setSceneRect(-w * 10, -h * 10, w * 20, h * 20)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self.dragMode() == QGraphicsView.DragMode.NoDrag:
            self.scene_pos = self.mapToScene(event.pos())
            self.scene().update()
            if self.PJI_mode:
                print("self.scene_pos", self.scene_pos, ", self.PJI_box", self.PJI_box)
                self.PJI_box = (
                    min(max(self.scene_pos.x() - 20, 0), self.image_rect.right() - 40),
                    min(max(self.scene_pos.y() - 20, 0), self.image_rect.bottom() - 40),
                )
        else:
            return super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self.dragMode() == QGraphicsView.DragMode.NoDrag:
            self.scene_pos = self.mapToScene(event.pos())
            self.scene().update()
            if self.PJI_mode:
                print("self.scene_pos", self.scene_pos, ", self.PJI_box", self.PJI_box)
                self.PJI_box = (
                    min(max(self.scene_pos.x() - 20, self.image_rect.left()), self.image_rect.right() - 40),
                    min(max(self.scene_pos.y() - 20, self.image_rect.top()), self.image_rect.bottom() - 40),
                )
        else:
            return super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self.dragMode() == QGraphicsView.DragMode.NoDrag and self.PJI_mode:
            pass
        else:
            return super().mouseReleaseEvent()

    def drawForeground(self, painter: QPainter, rect: QRectF) -> None:
        painter.setPen(
            QPen(
                QColor("#0000FF"),
                1 / self.scale_current[0],
                Qt.PenStyle.DotLine,
                Qt.PenCapStyle.SquareCap,
                Qt.PenJoinStyle.BevelJoin,
            )
        )
        if self.image_rect.top() < self.scene_pos.y() - 1.5:
            painter.drawLine(
                QPointF(self.scene_pos.x(), self.image_rect.top()),
                QPointF(self.scene_pos.x(), self.scene_pos.y() - 1.5),
            )
        if self.scene_pos.y() + 1.5 < self.image_rect.bottom():
            painter.drawLine(
                QPointF(self.scene_pos.x(), self.scene_pos.y() + 1.5),
                QPointF(self.scene_pos.x(), self.image_rect.bottom()),
            )
        painter.setPen(
            QPen(
                QColor("#0000FF"),
                1 / self.scale_current[1],
                Qt.PenStyle.DotLine,
                Qt.PenCapStyle.SquareCap,
                Qt.PenJoinStyle.BevelJoin,
            )
        )
        if self.image_rect.left() < self.scene_pos.x() - 1.5:
            painter.drawLine(
                QPointF(self.image_rect.left(), self.scene_pos.y()),
                QPointF(self.scene_pos.x() - 1.5, self.scene_pos.y()),
            )
        if self.scene_pos.x() + 1.5 < self.image_rect.right():
            painter.drawLine(
                QPointF(self.scene_pos.x() + 1.5, self.scene_pos.y()),
                QPointF(self.image_rect.right(), self.scene_pos.y()),
            )

        # 绘制40×40的红色边界框
        if self.PJI_mode and self.PJI_box is not None:
            painter.setPen(
                QPen(
                    QColor("#FF0000"),
                    1 / self.scale_current[0],
                    Qt.PenStyle.SolidLine,
                    Qt.PenCapStyle.SquareCap,
                    Qt.PenJoinStyle.BevelJoin,
                )
            )
            painter.drawRect(self.PJI_box[0], self.PJI_box[1], 40, 40)

    def position_to_scene_pos(self):
        if self.view == "t":
            pos = (self._position["s"], self._position["c"])
        elif self.view == "c":
            pos = (self._position["s"], self._position["t"])
        else:
            pos = (self._position["c"], self._position["t"])
        return QPointF(self.image_rect.left() + pos[0] + 0.5, self.image_rect.top() + pos[1] + 0.5)

    def reset(self):
        _size_s, _size_c, _size_t = (s1 * s2 for s1, s2 in zip(self.image.size, self.image.spacing))
        _scale_s, _scale_c, _scale_t = (
            min(self.height() * 1.0 / _size_t, self.width() * 1.0 / _size_c),
            min(self.height() * 1.0 / _size_t, self.width() * 1.0 / _size_s),
            min(self.height() * 1.0 / _size_c, self.width() * 1.0 / _size_s),
        )
        self._scale_default = {
            "s": (self.image.spacing[1] * _scale_s, self.image.spacing[2] * _scale_s),
            "c": (self.image.spacing[0] * _scale_c, self.image.spacing[2] * _scale_c),
            "t": (self.image.spacing[0] * _scale_t, self.image.spacing[1] * _scale_t),
        }
        self._scale_current = copy.deepcopy(self._scale_default)
        self.resetTransform()
        self.centerOn(0, 0)
        self.scale(*self.scale_default)  # x, y

    # 切换视图
    def set_view(self, view: str):
        self.view = view
        self.reset()
        if self.image is not None:
            self.set_image_item(self.image.plane(self.view, self.position))
            self.scene_pos = self.position_to_scene_pos()
        if self.label is not None:
            self.set_label_item(self.label.plane_origin(self.view, self.position))

    # 切换图像
    def set_image(self, image: Union[MedicalImage, MedicalImage2]):
        self.image = image
        # 位置信息
        self._position = {
            "s": self.image.size[0] // 2 + 1,
            "c": self.image.size[1] // 2 + 1,
            "t": self.image.size[2] // 2 + 1,
        }
        self._position_max = {
            "s": self.image.size[0],
            "c": self.image.size[1],
            "t": self.image.size[2],
        }
        # 背景色
        if self.image.cmap is None:
            self.scene().setBackgroundBrush(QColor("#000000"))
        else:
            self.scene().setBackgroundBrush(QColor(*[round(_ * 255) for _ in self.image.cmap(0)]))

        # 添加图像
        self.set_image_item(self.image.plane(self.view, self.position))

    # 设置ImageItem
    def set_image_item(self, image_array: np.ndarray):
        if self.image_item is not None:
            self.scene().removeItem(self.image_item)  # 清除图像
        else:
            self.reset()  # 缩放

        self.image_item = ImageItem(image_array)
        self.scene().addItem(self.image_item)

    def set_label(self, label: MedicalImage):
        if self.image is None:
            warning("请先打开图像。")
        elif label.size != self.image.size:
            warning("分割图与图像的大小尺寸不同。")
        else:
            self.label = label
            self.set_label_item(self.label.plane_origin(self.view, self.position))

    def set_label_item(self, labelArray: np.ndarray):
        if self.label_item is not None:
            self.scene().removeItem(self.label_item)  # 清除分割图
        self.label_item = ImageItem2(labelArray, self.label_opacity)
        self.scene().addItem(self.label_item)

    def set_label_opacity(self, v: float):
        self.label_opacity = v
        if self.label_item is not None:
            self.label_item.setOpacity(self.label_opacity)

    # 设置当前平面
    def set_current_plane(self):
        if self.image is not None:
            self.set_image_item(self.image.plane(self.view, self.position))
        if self.label is not None:
            self.set_label_item(self.label.plane_origin(self.view, self.position))

    def mirror1(self):  # 水平镜像
        self.scale(-1, 1)

    def mirror2(self):  # 垂直镜像
        self.scale(1, -1)

    def rotate1(self):  # 顺时针90°
        sx, sy = self.scale_current
        self.setTransform(self.transform().scale(1 / sx, 1 / sy).scale(sy, sx).rotate(90))

    def rotate2(self):  # 逆时针90°
        sx, sy = self.scale_current
        self.setTransform(self.transform().scale(1 / sx, 1 / sy).scale(sy, sx).rotate(-90))

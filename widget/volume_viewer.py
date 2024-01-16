import math
from typing import List, Tuple, Union

import numpy as np
import SimpleITK as sitk
import vtkmodules.vtkInteractionStyle
import vtkmodules.vtkRenderingAnnotation
import vtkmodules.vtkRenderingOpenGL2
import vtkmodules.vtkRenderingVolumeOpenGL2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMenu, QSlider, QToolBar, QToolButton, QWidget
from vtkmodules.all import vtkActor, vtkTextActor3D, vtkVolume
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# noinspection PyUnresolvedReferences
from vtkmodules.vtkRenderingCore import vtkRenderer

from utility import (
    MedicalImage,
    MedicalImage2,
    bbox,
    get_body_mask,
    get_colors,
    json_to_labels,
    nifti_to_labels,
    volume_ct,
    volume_pt,
)

from .message_box import error, information


class VolumeViewer(QMainWindow):
    def __init__(self, image: Union[MedicalImage, MedicalImage2], parent: QWidget = None):
        super().__init__(parent)
        self.images: List[Union[MedicalImage, MedicalImage2]] = []
        self.volumes: List[List[vtkVolume]] = []
        self.image_body: np.ndarray = None
        self.actors: List[Tuple[vtkActor, vtkTextActor3D]] = []
        self.label_opacity: float = 0.8
        self.checked_view: int = 0

        # 样式
        self.setStyleSheet("QToolBar {border: none;}" "QToolButton::menu-indicator {image: none;}")

        # 工具栏
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        view_button = QToolButton()
        view_button.setText("视图")
        view_button.setIcon(QIcon("asset/icon/view.png"))
        view_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        view_button.setAutoRaise(True)
        view_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.view_menu = QMenu()
        view_button.setMenu(self.view_menu)
        toolbar.addWidget(view_button)

        body_button = QToolButton()
        body_button.setText("人体")
        body_button.setIcon(QIcon("asset/icon/body.png"))
        body_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.addWidget(body_button)

        label_button = QToolButton()
        label_button.setText("标签")
        label_button.setIcon(QIcon("asset/icon/label.png"))
        label_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        toolbar.addWidget(label_button)

        label_slider = QSlider(Qt.Orientation.Horizontal)
        label_slider.setRange(0, 100)
        label_slider.setValue(self.label_opacity * 100)
        label_slider.setSingleStep(1)
        label_slider.setMinimumWidth(50)
        label_slider.setMaximumWidth(100)
        toolbar.addWidget(label_slider)
        toolbar.addSeparator()

        self.addToolBar(toolbar)

        # 三维可视化部件
        view = QVTKRenderWindowInteractor()
        self.setCentralWidget(view)
        self.renderer = vtkRenderer()
        view.GetRenderWindow().AddRenderer(self.renderer)
        self.camera = self.renderer.GetActiveCamera()

        # 信号与槽
        body_button.clicked.connect(self.add_body)
        label_button.clicked.connect(self.open_label)
        label_slider.valueChanged.connect(self.adjust_label_opacity)

        # 加载
        view.Initialize()
        view.Start()
        self.show()
        self.add_image(image)

    def adjust_camera(self, image: Union[MedicalImage, MedicalImage2]):
        _ = -0.5 * max(image.size[0] * image.spacing[0], image.size[2] * image.spacing[2]) / math.tan(math.pi / 6)
        self.camera.SetPosition(0.0, _, 0.0)
        self.camera.SetFocalPoint(0.0, 0.0, 0.0)
        self.camera.SetViewUp(0, 0, 1)
        self.camera.SetViewAngle(60.0)

    def add_image(self, image: Union[MedicalImage, MedicalImage2]):
        self.images.append(image)
        self.volumes.append(self.image_to_volume(image, self.image_body))

        # 渲染三维影像
        for v in self.volumes[0]:
            self.renderer.AddVolume(v)
        self.adjust_camera(image)

        _action = self.view_menu.addAction(QIcon("asset/icon/checked2.png"), "0 - 主影像")
        _action.triggered.connect(self.view_action_clicked)
        self.checked_view = 0

    def add_body(self):
        if self.images[0].modality == "PTCT":
            if self.image_body is None:
                self.image_body = sitk.GetArrayFromImage(get_body_mask(*self.images[0].to_sitk_image()))

                _volume_new = self.image_to_volume(self.images[0], self.image_body)

                if self.checked_view == 0:
                    for v in self.volumes[0]:
                        self.renderer.RemoveVolume(v)

                    self.volumes[0].clear()
                    self.volumes[0] = _volume_new

                    for v in self.volumes[0]:
                        self.renderer.AddVolume(v)
                    self.adjust_camera(self.images[0])
        else:
            information("该功能仅支持PET/CT融合成像。")

    def open_label(self):
        # 标签
        _labels = []  # [x1, y1, z1, x2, y2, z2, text, color]

        # 打开文件
        filename = QFileDialog().getOpenFileName(
            self, "选择文件", "./", filter="ALL FILES(*.nii *.nii.gz *.json);;NIFTI(*.nii *.nii.gz);;JSON(*.json)"
        )
        if len(filename[0]) == 0:
            return
        try:
            if filename[0].endswith(".nii.gz") or filename[0].endswith(".nii"):
                classes, labels = nifti_to_labels(filename[0])
            elif filename[0].endswith(".json"):
                classes, labels = json_to_labels(filename[0])
            else:
                raise Exception("not support the file format.")

            unique_classes = set(classes)
            colors = get_colors(len(unique_classes))
            c2c = {c1: c2 for c1, c2 in zip(unique_classes, colors)}
            for c, l in zip(classes, labels):
                _labels.append([*l, c, c2c[c]])

        except Exception as e:
            error(f"解析失败：{str(e)}")

        # 切换至主影像
        self.view_menu.actions()[0].trigger()
        # 更新view_menu
        for a in self.view_menu.actions()[1:]:
            self.view_menu.removeAction(a)
        # 移除掉之前的label
        for c, t in self.actors:
            self.renderer.RemoveActor(c)
            self.renderer.RemoveActor(t)
        self.actors.clear()
        del self.images[1:]
        del self.volumes[1:]

        # 根据图像获取原点与体素间距
        _origin = [-0.5 * s1 * s2 for s1, s2 in zip(self.images[0].size, self.images[0].spacing)]
        _spacing = self.images[0].spacing
        for i, _l in enumerate(_labels):
            self.actors.append(bbox(_l[0:3], _l[3:6], _origin, _spacing, _l[6], _l[7], self.label_opacity))
            self.images.append(self.images[0][_l[2] : _l[5] + 1, _l[1] : _l[4] + 1, _l[0] : _l[3] + 1])
            self.volumes.append(self.image_to_volume(self.images[-1]))
            _action = self.view_menu.addAction(QIcon("asset/icon/checked1.png"), f"{i + 1} - {_l[6]}")
            _action.triggered.connect(self.view_action_clicked)

        # 渲染新的label
        for c, t in self.actors:
            self.renderer.AddActor(c)
            self.renderer.AddActor(t)

    def view_action_clicked(self):
        action = self.sender()
        idx = self.view_menu.actions().index(action)

        # 更新
        if idx == self.checked_view:
            return
        for v in self.volumes[self.checked_view]:
            self.renderer.RemoveVolume(v)
        if self.checked_view == 0:
            for c, t in self.actors:
                self.renderer.RemoveActor(c)
                self.renderer.RemoveActor(t)
        self.view_menu.actions()[self.checked_view].setIcon(QIcon("asset/icon/checked1.png"))

        #
        self.checked_view = idx
        self.view_menu.actions()[self.checked_view].setIcon(QIcon("asset/icon/checked2.png"))
        for v in self.volumes[self.checked_view]:
            self.renderer.AddVolume(v)
        if self.checked_view == 0:
            for c, t in self.actors:
                self.renderer.AddActor(c)
                self.renderer.AddActor(t)
        self.adjust_camera(self.images[self.checked_view])
        self.centralWidget().GetRenderWindow().Render()

    def adjust_label_opacity(self, v: int):
        self.label_opacity = 0.01 * v
        for c, t in self.actors:
            c.GetProperty().SetOpacity(self.label_opacity)
            t.GetTextProperty().SetOpacity(self.label_opacity)
        self.centralWidget().GetRenderWindow().Render()

    @staticmethod
    def image_to_volume(image: Union[MedicalImage, MedicalImage2], image_body: np.ndarray = None):
        # 根据图像获取原点与体素间距
        _origin = [-0.5 * s1 * s2 for s1, s2 in zip(image.size, image.spacing)]
        _spacing = image.spacing

        if image.modality == "CT":
            _volume = [volume_ct(image.array, _origin, _spacing, image_body)]
        elif image.modality == "PT":
            _volume = [volume_pt(image.array, _origin, _spacing, image_body)]
        elif image.modality == "PTCT":
            _volume = [
                volume_ct(image.array, _origin, _spacing, image_body),
                volume_pt(image.array_pt, _origin, _spacing, image_body),
            ]
        return _volume

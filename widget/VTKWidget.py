import json
import math
from typing import Union

import vtkmodules.vtkInteractionStyle
import vtkmodules.vtkRenderingAnnotation
import vtkmodules.vtkRenderingOpenGL2
import vtkmodules.vtkRenderingVolumeOpenGL2
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileDialog, QMainWindow, QMessageBox, QSlider, QToolBar, QToolButton, QWidget
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

# noinspection PyUnresolvedReferences
from vtkmodules.vtkRenderingCore import vtkRenderer

from utility.common import get_colors
from utility.constant import LABEL_TO_NAME
from utility.io import ReadNIFTI
from utility.MedicalImage import MedicalImage
from utility.MedicalImage2 import MedicalImage2
from utility.vtktool import BoundingBox, labelToPoints, volumeCT, volumePT


class VTKWidget(QMainWindow):
    image = None
    origin = None
    spacing = None

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.labelOpacity = 0.5
        self.cubeActors, self.textActors = [], []

        toolbar = QToolBar()
        toolbar.setMovable(False)

        labelButton = QToolButton()
        labelButton.setText("标签")
        labelButton.setIcon(QIcon("resource/label.png"))
        labelButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        labelSlider = QSlider(Qt.Orientation.Horizontal)
        labelSlider.setRange(0, 100)
        labelSlider.setValue(50)
        labelSlider.setSingleStep(1)
        labelSlider.setMinimumWidth(50)
        labelSlider.setMaximumWidth(100)

        toolbar.addWidget(labelButton)
        toolbar.addWidget(labelSlider)
        toolbar.addSeparator()

        widget = QVTKRenderWindowInteractor()
        self.ren = vtkRenderer()
        widget.GetRenderWindow().AddRenderer(self.ren)

        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)
        self.setCentralWidget(widget)
        self.ren.SetBackground(1.0, 1.0, 1.0)

        # 信号与槽
        labelButton.clicked.connect(self.openLabel)
        labelSlider.valueChanged.connect(self.adjustLabelOpacity)

        widget.Initialize()
        widget.Start()
        self.show()

    def addVolume(self, image: Union[MedicalImage, MedicalImage2]):
        if image.modality == "CT":
            self.initByImage(image)
            self.ren.AddVolume(volumeCT(image.array, self.origin, self.spacing))
            self.adjustCamera()
        elif image.modality == "PT":
            self.initByImage(image)
            self.ren.AddVolume(volumePT(image.array, self.origin, self.spacing))
            self.adjustCamera()
        elif image.modality == "PTCT":
            self.initByImage(image)
            self.ren.AddVolume(volumeCT(image.array, self.origin, self.spacing, image.body_mask))
            self.ren.AddVolume(volumePT(image.array_pt, self.origin, self.spacing, image.body_mask))
            self.adjustCamera()
        else:
            raise Exception(f"[ERROR] not support the image's modality = {image.modality}.")

    def adjustCamera(self):
        camera = self.ren.GetActiveCamera()
        _ = (
            -0.5
            * max(self.image.size[0] * self.image.spacing[0], self.image.size[2] * self.image.spacing[2])
            / math.tan(math.pi / 6)
        )
        camera.SetPosition(0.0, _, 0.0)
        camera.SetFocalPoint(0.0, 0.0, 0.0)
        camera.SetViewUp(0, 0, 1)
        camera.SetViewAngle(60.0)
        # camera.Azimuth(30.0)  # 表示 camera 的视点位置沿顺时针旋转 30 度角
        # camera.Elevation(30.0)  # 表示 camera 的视点位置沿向上的方面旋转 30 度角

    def initByImage(self, image: Union[MedicalImage, MedicalImage2]):
        self.image = image
        self.spacing = self.image.spacing
        # 自定义 origin 使中心位于 (0, 0, 0)
        self.origin = [-0.5 * s1 * s2 for s1, s2 in zip(self.image.size, self.image.spacing)]

    def openLabel(self):
        filename = QFileDialog().getOpenFileName(
            self, "选择文件", "./", filter="ALL FILES(*.nii *.nii.gz *.json);;NIFTI(*.nii *.nii.gz);;JSON(*.json)"
        )
        if len(filename[0]) == 0:
            return
        try:
            if filename[0].endswith(".nii.gz") or filename[0].endswith(".nii"):
                labelImage: MedicalImage = ReadNIFTI(filename[0], only_image=True)
                classes, labels = labelToPoints(labelImage.array)
                num_colors = max(classes)

                if num_colors == 0:  # 不存在
                    return

                # 依次添加
                colors = get_colors(num_colors)
                for c, l in zip(classes, labels):
                    cube, text = BoundingBox(
                        l[0], l[1], self.origin, self.spacing, colors[c - 1], LABEL_TO_NAME[c], self.labelOpacity
                    )
                    self.ren.AddActor(cube)
                    self.ren.AddActor(text)
                    self.cubeActors.append(cube)
                    self.textActors.append(text)

            elif filename[0].endswith(".json"):
                labelJson = json.load(open(filename[0], "r"))

                assert isinstance(
                    labelJson, list
                ), "json should be a list, in which each item should be a dict. the dict have two key: class_name and bbox."

                if len(labelJson) == 0:
                    return

                classes, labels = [], []
                for label in labelJson:
                    classes.append(label["class_name"])
                    labels.append(label["bbox"])
                unique_classes = set(classes)
                num_colors = len(unique_classes)
                if num_colors == 0:
                    return

                colors = get_colors(num_colors)
                c2c = {c1: c2 for c1, c2 in zip(unique_classes, colors)}
                for c, l in zip(classes, labels):
                    cube, text = BoundingBox(l[0:3], l[3:6], self.origin, self.spacing, c2c[c], c, self.labelOpacity)
                    self.ren.AddActor(cube)
                    self.ren.AddActor(text)
                    self.cubeActors.append(cube)
                    self.textActors.append(text)
            else:
                raise Exception("not support the file format.")

        except Exception as e:
            messageBox = QMessageBox(
                QMessageBox.Icon.Critical, "错误", "解析文件失败, " + str(e), QMessageBox.StandardButton.Close
            )
            messageBox.exec()

    def adjustLabelOpacity(self, v: int):
        self.labelOpacity = 0.01 * v
        for actor in self.cubeActors:
            actor.GetProperty().SetOpacity(self.labelOpacity)
        for actor in self.textActors:
            actor.GetTextProperty().SetOpacity(self.labelOpacity)
        self.centralWidget().GetRenderWindow().Render()


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    widget = VTKWidget()
    image = ReadNIFTI(r"DATA\001_CT.nii.gz", True)
    image.modality = "CT"
    widget.addVolume(image)
    image = ReadNIFTI(r"DATA\001_SUVbw.nii.gz", True)
    image.modality = "PT"
    widget.addVolume(image)
    sys.exit(app.exec())

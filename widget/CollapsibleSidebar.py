from typing import Dict, List

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileDialog, QGridLayout, QMessageBox, QScrollArea, QToolButton, QVBoxLayout, QWidget

from utility.io import ReadImage
from utility.MedicalImage import MedicalImage
from utility.MedicalImage2 import MedicalImage2

from .CollapsibleWidget import CollapsibleWidget


class CollapsibleSidebar(QWidget):
    displayImage2D = pyqtSignal(str, str, MedicalImage)
    displayImage3D = pyqtSignal(str, str, MedicalImage)
    displayImageFused = pyqtSignal(str, str, MedicalImage2)

    def __init__(self, parent: QWidget = None) -> None:
        # 初始化
        super().__init__(parent)
        self.setStyleSheet(
            "QToolButton {background-color:transparent;}"
            "QToolButton::hover {background-color:rgba(71,141,141,0.4);}"
            "QToolButton::pressed {background-color:rgba(174,238,238,0.4);}"
            "QScrollArea {background-color:transparent; border: none;}"
        )

        self.checkedChildren: List[str] = []
        self.collapsibleWidgets: Dict[str, CollapsibleWidget] = {}

        self.setMinimumWidth(150)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # 主按钮
        openButton = QToolButton(self)
        openButton.setIcon(QIcon("asset/icon/open.png"))
        openButton.setIconSize(QSize(30, 30))
        openButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        openButton.setToolTip("打开文件")
        openButton.setToolTipDuration(5000)

        display2DButton = QToolButton(self)
        display2DButton.setIcon(QIcon("asset/icon/display2D.png"))
        display2DButton.setIconSize(QSize(30, 30))
        display2DButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        display2DButton.setToolTip("二维浏览")
        display2DButton.setToolTipDuration(5000)

        display3DButton = QToolButton(self)
        display3DButton.setIcon(QIcon("asset/icon/display3D.png"))
        display3DButton.setIconSize(QSize(30, 30))
        display3DButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        display3DButton.setToolTip("三维浏览")
        display3DButton.setToolTipDuration(5000)

        displayFusion2DButton = QToolButton(self)
        displayFusion2DButton.setIcon(QIcon("asset/icon/displayFusion2D.png"))
        displayFusion2DButton.setIconSize(QSize(30, 30))
        displayFusion2DButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        displayFusion2DButton.setToolTip("二维融合")
        displayFusion2DButton.setToolTipDuration(5000)

        displayFusion3DButton = QToolButton(self)
        displayFusion3DButton.setIcon(QIcon("asset/icon/displayFusion3D.png"))
        displayFusion3DButton.setIconSize(QSize(30, 30))
        displayFusion3DButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        displayFusion3DButton.setToolTip("三维融合")
        displayFusion3DButton.setToolTipDuration(5000)

        layoutButton = QGridLayout()
        layoutButton.setSpacing(20)
        layoutButton.setContentsMargins(0, 0, 0, 0)
        layoutButton.addWidget(openButton, 0, 0, 2, 1)
        layoutButton.addWidget(display2DButton, 0, 1, 1, 1)
        layoutButton.addWidget(displayFusion2DButton, 1, 1, 1, 1)
        layoutButton.addWidget(display3DButton, 0, 2, 1, 1)
        layoutButton.addWidget(displayFusion3DButton, 1, 2, 1, 1)
        layout.addLayout(layoutButton)

        # scrollArea
        self.layoutCollapsibleButtons = QVBoxLayout()
        self.layoutCollapsibleButtons.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.layoutCollapsibleButtons.setSpacing(0)
        self.layoutCollapsibleButtons.setContentsMargins(0, 0, 0, 0)
        scrollArea = QScrollArea(self)
        scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scrollAreaContent = QWidget(scrollArea)
        scrollAreaContent.setLayout(self.layoutCollapsibleButtons)
        # 添加
        scrollArea.setWidget(scrollAreaContent)
        scrollArea.setWidgetResizable(True)
        layout.addWidget(scrollArea)

        # 信号与槽
        openButton.clicked.connect(self.openButtonClicked)
        display2DButton.clicked.connect(self.display2DButtonClicked)
        display3DButton.clicked.connect(self.display3DButtonClicked)
        displayFusion2DButton.clicked.connect(lambda: self.displayFusionButtonClicked("2DFusion"))
        displayFusion3DButton.clicked.connect(lambda: self.displayFusionButtonClicked("3DFusion"))

    def addCollapsibleWidget(self, study_image: dict):
        for study_uid, series_image in study_image.items():
            description = series_image.pop("description")
            if study_uid in self.collapsibleWidgets:
                self.collapsibleWidgets[study_uid].addChildren(series_image)
            else:
                widget = CollapsibleWidget(study_uid, description, series_image)
                # 绑定信号与槽
                widget.deleted.connect(self.removeCollapsibleWidget)
                widget.childChecked.connect(self.childToggled)
                self.collapsibleWidgets[study_uid] = widget
                self.layoutCollapsibleButtons.addWidget(widget)

    def removeCollapsibleWidget(self, collapsibleWidgetUid):
        _collapsibleWidget = self.collapsibleWidgets.pop(collapsibleWidgetUid)
        _collapsibleWidget.close()
        _collapsibleWidget.destroy()

    def childToggled(self, widget_uid: str, child_uid: str, c: bool):
        if c:
            self.checkedChildren.append(widget_uid + "_^_" + child_uid)
            if self.checkedChildren[0].startswith(widget_uid):
                while len(self.checkedChildren) >= 3:
                    checked = self.checkedChildren[0]
                    widget_uid, child_uid = checked.split("_^_")
                    self.collapsibleWidgets[widget_uid].children[child_uid].radioButton.setChecked(False)
            else:
                for checked in self.checkedChildren[:-1]:
                    widget_uid, child_uid = checked.split("_^_")
                    self.collapsibleWidgets[widget_uid].children[child_uid].radioButton.setChecked(False)
        else:
            self.checkedChildren.remove(widget_uid + "_^_" + child_uid)

    def openButtonClicked(self):
        filename = QFileDialog().getOpenFileName(
            self, "选择文件", "./", filter="IMAGE(*.dcm *.nii *.nii.gz);;NIFTI(*.nii *.nii.gz);;DICOM(*.dcm)"
        )
        if len(filename[0]) == 0:
            return

        uidDictImage = ReadImage(filename[0])
        self.addCollapsibleWidget(uidDictImage)

    def display2DButtonClicked(self):
        for uid in self.checkedChildren:
            widget_uid, child_uid = uid.split("_^_")
            widget = self.collapsibleWidgets[widget_uid]
            child = widget.children[child_uid]
            title = widget.collapsibleButton.text().split(" ")[0] + " - " + child.radioButton.text().split(" ")[0]
            self.displayImage2D.emit(uid + "2D", title, child.image)

    def display3DButtonClicked(self):
        for uid in self.checkedChildren:
            widget_uid, child_uid = uid.split("_^_")
            widget = self.collapsibleWidgets[widget_uid]
            child = widget.children[child_uid]
            if child.image.modality == "CT" or child.image.modality == "PT":
                title = widget.collapsibleButton.text().split(" ")[0] + " - " + child.radioButton.text().split(" ")[0]
                self.displayImage2D.emit(uid + "3D", title, child.image)
            else:
                messageBox = QMessageBox(
                    QMessageBox.Icon.Information, "提示", "该功能仅支持PET或CT三维成像。", QMessageBox.StandardButton.Ok
                )
                messageBox.exec()
                return

    def displayFusionButtonClicked(self, fusion_type: str):
        images, title = [], None
        for uid in self.checkedChildren:
            widget_uid, child_uid = uid.split("_^_")
            widget = self.collapsibleWidgets[widget_uid]
            child = widget.children[child_uid]
            images.append(child.image)
            title = widget.collapsibleButton.text().split(" ")[0] + " - " + child.radioButton.text().split(" ")[0]
        if len(images) == 2 and (
            ("PT" == images[0].modality and "CT" == images[1].modality)
            or ("PT" == images[1].modality and "CT" == images[0].modality)
        ):
            if images[0].modality == "PT":
                imagePT, imageCT = images[0], images[1]
            else:
                imagePT, imageCT = images[1], images[0]
            image = MedicalImage2.from_ct_pt(imageCT, imagePT)
            self.displayImageFused.emit(uid + fusion_type, title, image)
        else:
            messageBox = QMessageBox(
                QMessageBox.Icon.Information, "提示", "该功能仅支持PET/CT融合成像。", QMessageBox.StandardButton.Ok
            )
            messageBox.exec()

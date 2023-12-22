from typing import Dict, List

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from utility.io import ReadImage
from utility.MedicalImage import MedicalImage
from widget.CollapsibleWidget import CollapsibleWidget


class Sidebar(QWidget):
    displayImage2D = pyqtSignal(str, str, MedicalImage)

    def __init__(self, parent: QWidget = None) -> None:
        # 初始化
        super().__init__(parent)
        self.checkedChildren: List[str] = []
        self.collapsibleWidgets: Dict[str, CollapsibleWidget] = {}

        self.setMinimumWidth(150)

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        layoutMain = QVBoxLayout()
        self.widgetMain = QWidget()
        self.widgetMain.setLayout(layoutMain)
        layout.addWidget(self.widgetMain)
        # 主按钮
        openButton = QToolButton(self)
        openButton.setIcon(QIcon("resource/open.png"))
        openButton.setIconSize(QSize(30, 30))
        openButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        openButton.setToolTip("打开文件")
        openButton.setToolTipDuration(5000)
        openButton.setObjectName("openButton")
        openButton.setStyleSheet(
            "#openButton{background-color:transparent;}"
            "#openButton:hover{background-color:rgba(71,141,141,0.4);}"
            "#openButton:pressed{background-color:rgba(174,238,238,0.4);}"
        )
        display2DButton = QToolButton(self)
        display2DButton.setIcon(QIcon("resource/display2d.png"))
        display2DButton.setIconSize(QSize(30, 30))
        display2DButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        display2DButton.setToolTip("2D浏览")
        display2DButton.setToolTipDuration(5000)
        display2DButton.setObjectName("display2DButton")
        display2DButton.setStyleSheet(
            "#display2DButton{background-color:transparent;}"
            "#display2DButton:hover{background-color:rgba(71,141,141,0.4);}"
            "#display2DButton:pressed{background-color:rgba(174,238,238,0.4);}"
        )
        display3DButton = QToolButton(self)
        display3DButton.setIcon(QIcon("resource/display3d.png"))
        display3DButton.setIconSize(QSize(30, 30))
        display3DButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        display3DButton.setToolTip("3D浏览")
        display3DButton.setToolTipDuration(5000)
        display3DButton.setObjectName("display3DButton")
        display3DButton.setStyleSheet(
            "#display3DButton{background-color:transparent;}"
            "#display3DButton:hover{background-color:rgba(71,141,141,0.4);}"
            "#display3DButton:pressed{background-color:rgba(174,238,238,0.4);}"
        )
        displayFusionButton = QToolButton(self)
        displayFusionButton.setIcon(QIcon("resource/displayFusion.png"))
        displayFusionButton.setIconSize(QSize(30, 30))
        displayFusionButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        displayFusionButton.setToolTip("融合浏览")
        displayFusionButton.setToolTipDuration(5000)
        displayFusionButton.setObjectName("displayFusionButton")
        displayFusionButton.setStyleSheet(
            "#displayFusionButton{background-color:transparent;}"
            "#displayFusionButton:hover{background-color:rgba(71,141,141,0.4);}"
            "#displayFusionButton:pressed{background-color:rgba(174,238,238,0.4);}"
        )

        layoutButton = QHBoxLayout()
        layoutButton.setSpacing(20)
        layoutButton.setContentsMargins(0, 0, 0, 0)
        layoutButton.addWidget(openButton)
        layoutButton.addWidget(display2DButton)
        layoutButton.addWidget(display3DButton)
        layoutButton.addWidget(displayFusionButton)
        layoutMain.addLayout(layoutButton)

        # scrollArea
        self.layoutCollapsibleButtons = QVBoxLayout()
        self.layoutCollapsibleButtons.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.layoutCollapsibleButtons.setSpacing(0)
        self.layoutCollapsibleButtons.setContentsMargins(0, 0, 0, 0)
        scrollArea = QScrollArea(self)
        scrollArea.setObjectName("scrollArea")
        scrollArea.setStyleSheet("#scrollArea{background-color:transparent; border: none;}")
        scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scrollAreaContent = QWidget(scrollArea)
        scrollAreaContent.setLayout(self.layoutCollapsibleButtons)
        # 添加
        scrollArea.setWidget(scrollAreaContent)
        scrollArea.setWidgetResizable(True)
        layoutMain.addWidget(scrollArea)

        self.setLayout(layout)

        # 信号与槽
        openButton.clicked.connect(self.openButtonClicked)
        display2DButton.clicked.connect(self.display2DButtonClicked)
        display3DButton.clicked.connect(self.display3DButtonClicked)
        displayFusionButton.clicked.connect(self.displayFusionButtonClicked)

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
        print("display3DButtonClicked...")

    def displayFusionButtonClicked(self):
        print("displayFusionButtonClicked...")
        messageBox = QMessageBox(QMessageBox.Icon.Information, "提示", "该功能仅支持PET/CT融合成像。", QMessageBox.StandardButton.Ok)
        messageBox.exec()


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    MainWindow = Sidebar()
    MainWindow.show()
    sys.exit(app.exec())

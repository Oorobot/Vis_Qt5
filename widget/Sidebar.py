from typing import Dict, List

from PyQt6.QtCore import QSize, Qt
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
from widget.CollapsibleWidget import CollapsibleWidget


class Sidebar(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        # 初始化
        super().__init__(parent)
        self.checkedChildren: List[str] = []
        self.collapsibleWidgets: Dict[str, CollapsibleWidget] = {}

        self.setMinimumWidth(380)
        self.setMinimumHeight(560)

        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        layoutMain = QVBoxLayout()
        self.widgetMain = QWidget()
        self.widgetMain.setLayout(layoutMain)
        layout.addWidget(self.widgetMain)
        # 主按钮
        openBtn = QToolButton(self)
        openBtn.setIcon(QIcon("resource/open.png"))
        openBtn.setIconSize(QSize(30, 30))
        openBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        openBtn.setToolTip("打开文件")
        openBtn.setToolTipDuration(5000)
        openBtn.setObjectName("openBtn")
        openBtn.setStyleSheet(
            "#openBtn{background-color:transparent;}"
            "#openBtn:hover{background-color:rgba(71,141,141,0.4);}"
            "#openBtn:pressed{background-color:rgba(174,238,238,0.4);}"
        )
        display2DBtn = QToolButton(self)
        display2DBtn.setIcon(QIcon("resource/display2d.png"))
        display2DBtn.setIconSize(QSize(30, 30))
        display2DBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        display2DBtn.setToolTip("2D浏览")
        display2DBtn.setToolTipDuration(5000)
        display2DBtn.setObjectName("display2DBtn")
        display2DBtn.setStyleSheet(
            "#display2DBtn{background-color:transparent;}"
            "#display2DBtn:hover{background-color:rgba(71,141,141,0.4);}"
            "#display2DBtn:pressed{background-color:rgba(174,238,238,0.4);}"
        )
        display3DBtn = QToolButton(self)
        display3DBtn.setIcon(QIcon("resource/display3d.png"))
        display3DBtn.setIconSize(QSize(30, 30))
        display3DBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        display3DBtn.setToolTip("3D浏览")
        display3DBtn.setToolTipDuration(5000)
        display3DBtn.setObjectName("display3DBtn")
        display3DBtn.setStyleSheet(
            "#display3DBtn{background-color:transparent;}"
            "#display3DBtn:hover{background-color:rgba(71,141,141,0.4);}"
            "#display3DBtn:pressed{background-color:rgba(174,238,238,0.4);}"
        )
        displayFusionBtn = QToolButton(self)
        displayFusionBtn.setIcon(QIcon("resource/displayFusion.png"))
        displayFusionBtn.setIconSize(QSize(30, 30))
        displayFusionBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        displayFusionBtn.setToolTip("融合浏览")
        displayFusionBtn.setToolTipDuration(5000)
        displayFusionBtn.setObjectName("displayFusionBtn")
        displayFusionBtn.setStyleSheet(
            "#displayFusionBtn{background-color:transparent;}"
            "#displayFusionBtn:hover{background-color:rgba(71,141,141,0.4);}"
            "#displayFusionBtn:pressed{background-color:rgba(174,238,238,0.4);}"
        )

        layoutBtn = QHBoxLayout()
        layoutBtn.setSpacing(20)
        layoutBtn.setContentsMargins(0, 0, 0, 0)
        layoutBtn.addWidget(openBtn)
        layoutBtn.addWidget(display2DBtn)
        layoutBtn.addWidget(display3DBtn)
        layoutBtn.addWidget(displayFusionBtn)
        layoutMain.addLayout(layoutBtn)

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

        # 侧边隐藏按钮
        self.hideBtn = QToolButton(self)
        self.hideBtn.setArrowType(Qt.ArrowType.LeftArrow)
        self.hideBtn.setFixedHeight(60)
        self.hideBtn.setFixedWidth(15)
        layoutHide = QVBoxLayout()
        layoutHide.setSpacing(0)
        layoutHide.setContentsMargins(0, 0, 0, 0)
        layoutHide.addItem(QSpacerItem(10, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        layoutHide.addWidget(self.hideBtn)
        layoutHide.addItem(QSpacerItem(10, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        layout.addLayout(layoutHide)

        self.setLayout(layout)

        # 绑定
        self.hideBtn.clicked.connect(self.hideBtnClicked)
        openBtn.clicked.connect(self.openBtnClicked)
        display2DBtn.clicked.connect(self.display2DBtnClicked)
        display3DBtn.clicked.connect(self.display3DBtnClicked)
        displayFusionBtn.clicked.connect(self.displayFusionBtnClicked)

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
                    self.collapsibleWidgets[widget_uid].children[child_uid].radioBtn.setChecked(False)
            else:
                for checked in self.checkedChildren[:-1]:
                    widget_uid, child_uid = checked.split("_^_")
                    self.collapsibleWidgets[widget_uid].children[child_uid].radioBtn.setChecked(False)
        else:
            self.checkedChildren.remove(widget_uid + "_^_" + child_uid)

    def hideBtnClicked(self):
        if self.widgetMain.isVisible():
            self.widgetMain.setVisible(False)
            self.hideBtn.setArrowType(Qt.ArrowType.RightArrow)
            self.setMinimumWidth(0)
        else:
            self.widgetMain.setVisible(True)
            self.hideBtn.setArrowType(Qt.ArrowType.LeftArrow)
            self.setMinimumWidth(320)

    def openBtnClicked(self):
        filename = QFileDialog().getOpenFileName(
            self, "选择文件", "./", filter="IMAGE(*.dcm *.nii *.nii.gz);;NIFTI(*.nii *.nii.gz);;DICOM(*.dcm)"
        )
        if len(filename[0]) == 0:
            return

        uidDictImage = ReadImage(filename[0])
        self.addCollapsibleWidget(uidDictImage)

    def display2DBtnClicked(self):
        print("display2DBtnClicked...")

    def display3DBtnClicked(self):
        print("display3DBtnClicked...")

    def displayFusionBtnClicked(self):
        print("displayFusionBtnClicked...")
        messageBox = QMessageBox(QMessageBox.Icon.Information, "提示", "该功能仅支持PET/CT融合成像。", QMessageBox.StandardButton.Ok)
        messageBox.exec()


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    MainWindow = Sidebar()
    MainWindow.show()
    sys.exit(app.exec())

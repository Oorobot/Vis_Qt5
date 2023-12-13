from typing import Dict, List

from PyQt6.QtCore import *
from PyQt6.QtGui import *
from PyQt6.QtWidgets import *

from entity import MedicalImage, ReadImage


class CollapsibleChild(QWidget):
    def __init__(self, parent: QWidget, uid: str, image: MedicalImage) -> None:
        # 定义成员属性
        self._uid: str = ""
        self._text: QLabel = QLabel()

        # 初始化
        super().__init__(parent)
        self._uid = uid
        self._image = image

        self.radioBtn = QRadioButton()
        self.radioBtn.setText(image.description if image is not None else "UNKNOWN")
        layout = QHBoxLayout()
        layout.addItem(QSpacerItem(28, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        layout.addWidget(self.radioBtn)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setFixedHeight(30)
        self.setMaximumWidth(250)

        # 样式
        self.radioBtn.setObjectName("RadioButton")
        self.radioBtn.setStyleSheet(
            "#RadioButton{background-color:transparent;}"
            "#RadioButton:hover{background-color:rgba(64,70,75,0.4);}"
            "#RadioButton:pressed{background-color:rgba(119,136,153,0.4);}"
            "#RadioButton{font-family: 'Times New Roman'; font-size: 16px;}"
        )

        # 初始隐藏
        self.setVisible(False)

        # 右键
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showCustomContextMenu)
        self.contextMenu = QMenu()
        deleteAction = QAction(QIcon("resource/delete.png"), "删除", self.contextMenu)
        self.contextMenu.addAction(deleteAction)
        deleteAction.triggered.connect(self.deleteActionTriggered)

        self.radioBtn.toggled.connect(self.radioBtnToggled)

    def showCustomContextMenu(self, pos):
        self.contextMenu.show()
        self.contextMenu.move(self.mapToGlobal(pos))

    def deleteActionTriggered(self):
        if self.parent() is not None:
            self.parent().removeChild(self._uid)

    def radioBtnToggled(self, c: bool):
        if self.parent() is not None:
            self.parent().childRadioBtnToggled(c, self._uid)


class CollapsibleWidget(QWidget):
    def __init__(self, uid: str, dictImage: dict, parent: QWidget = None):
        # 定义成员属性
        self._parent = parent
        self._uid: str = uid
        self._collapsible: bool = False
        self._children: Dict[str, CollapsibleChild] = {}

        # 初始化
        super().__init__(parent)

        # 主布局
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # 可折叠按钮
        self.collapsibleButton = QToolButton(self)
        self.collapsibleButton.setIcon(QIcon("resource/collapse.png"))
        self.collapsibleButton.setText(self._uid.split("_")[-1])
        layout.addWidget(self.collapsibleButton)

        # 样式
        self.collapsibleButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.collapsibleButton.setFixedHeight(40)
        self.collapsibleButton.setFixedWidth(250)
        self.collapsibleButton.setIconSize(QSize(25, 25))
        self.collapsibleButton.setObjectName("CollapsibleButton")
        self.collapsibleButton.setStyleSheet(
            "#CollapsibleButton{background-color:transparent}"
            "#CollapsibleButton:hover{background-color:rgba(51,51,51,0.4)}"
            "#CollapsibleButton:pressed{background-color:rgba(127,127,127,0.4)}"
            "#CollapsibleButton{font-family: 'Times New Roman'; font-size: 20px;}"
        )

        # 绑定事件
        self.collapsibleButton.clicked.connect(self.collapsibleBtnClicked)

        # 添加 child
        self.addChildren(dictImage)

    def addChildren(self, dictImage: dict) -> None:
        for i, d in dictImage.items():
            if i in self._children:
                continue
            child = CollapsibleChild(self, i, d)
            child.setVisible(self._collapsible)
            self._children[i] = child
            self.layout().addWidget(child)
            if self._collapsible:
                self.setFixedHeight(40 + (len(self._children) * 30))

    def removeChild(self, childUid: str):
        _child = self._children.pop(childUid)
        # 删除该子组件
        _child.close()
        _child.destroy()
        if len(self._children) == 0 and self._parent is not None:
            self._parent.removeCollapsibleWidget(self._uid)
        else:
            self.setFixedHeight(40 + (len(self._children) * 30))

    def childRadioBtnToggled(self, c: bool, childUid: str):
        if self._parent is not None:
            self._parent.childRadioBtnToggled(c, childUid, self._uid)

    def collapsibleBtnClicked(self) -> None:
        if self._collapsible:
            self.collapsibleButton.setIcon(QIcon("resource/collapse.png"))
            self.setFixedHeight(40)
            for child in self._children.values():
                child.radioBtn.setChecked(False)
        else:
            self.collapsibleButton.setIcon(QIcon("resource/expand.png"))
            self.setFixedHeight(40 + (len(self._children) * 30))
        self._collapsible = not self._collapsible
        for child in self._children.values():
            child.setVisible(self._collapsible)


class Sidebar(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        # 定义成员属性
        self._collapsibleWidgets: Dict[str, CollapsibleWidget] = {}
        self._checkedCollapsibleChildren: List[str] = []

        # 初始化
        super().__init__(parent)
        self.setMinimumWidth(320)
        self.setMinimumHeight(480)

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

    def addCollapsibleButtons(self, uidDictImage: dict):
        for uid, dictImage in uidDictImage.items():
            if uid in self._collapsibleWidgets:
                self._collapsibleWidgets[uid].addChildren(dictImage)
                continue
            collapsibleWidget = CollapsibleWidget(uid, dictImage, self)
            self._collapsibleWidgets[uid] = collapsibleWidget
            self.layoutCollapsibleButtons.addWidget(collapsibleWidget)

    def removeCollapsibleWidget(self, collapsibleWidgetUid):
        _collapsibleWidget = self._collapsibleWidgets.pop(collapsibleWidgetUid)
        _collapsibleWidget.close()
        _collapsibleWidget.destroy()

    def childRadioBtnToggled(self, c: bool, childUid: str, widgetUid: str):
        if c:
            self._checkedCollapsibleChildren.append(widgetUid + "_^_" + childUid)
            if self._checkedCollapsibleChildren[0].startswith(widgetUid):
                while len(self._checkedCollapsibleChildren) >= 3:
                    checked = self._checkedCollapsibleChildren[0]
                    widgetUid, childUid = checked.split("_^_")
                    self._collapsibleWidgets[widgetUid]._children[childUid].radioBtn.setChecked(False)
            else:
                for checked in self._checkedCollapsibleChildren[:-1]:
                    widgetUid, childUid = checked.split("_^_")
                    self._collapsibleWidgets[widgetUid]._children[childUid].radioBtn.setChecked(False)
        else:
            self._checkedCollapsibleChildren.remove(widgetUid + "_^_" + childUid)

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
        self.addCollapsibleButtons(uidDictImage)

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

    app = QApplication(sys.argv)
    MainWindow = Sidebar()
    MainWindow.show()
    sys.exit(app.exec())

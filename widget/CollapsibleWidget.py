from typing import Dict

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from utility.MedicalImage import MedicalImage


class CollapsibleChild(QWidget):
    deleted = pyqtSignal(str)
    checked = pyqtSignal(str, bool)

    def __init__(self, uid: str, description: str, image: MedicalImage, parent: QWidget = None) -> None:
        # 初始化
        super().__init__(parent)
        self.uid = uid
        self.image = image

        self.radioButton = QRadioButton(description, self)
        layout = QHBoxLayout()
        layout.addItem(QSpacerItem(28, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        layout.addWidget(self.radioButton)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setFixedHeight(30)
        self.setMinimumWidth(150)

        # 样式
        self.radioButton.setObjectName("RadioButton")
        self.radioButton.setStyleSheet(
            "#RadioButton{background-color:transparent;}"
            "#RadioButton:hover{background-color:rgba(64,70,75,0.4);}"
            "#RadioButton:pressed{background-color:rgba(119,136,153,0.4);}"
            "#RadioButton{font-family: 'Times New Roman'; font-size: 15px;}"
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
        self.radioButton.toggled.connect(self.radioButtonToggled)

    def showCustomContextMenu(self, pos):
        self.contextMenu.show()
        self.contextMenu.move(self.mapToGlobal(pos))

    def deleteActionTriggered(self):
        self.deleted.emit(self.uid)

    def radioButtonToggled(self, c: bool):
        self.checked.emit(self.uid, c)


class CollapsibleWidget(QWidget):
    deleted = pyqtSignal(str)
    childChecked = pyqtSignal(str, str, bool)

    def __init__(self, uid: str, description: str, series_image: dict, parent: QWidget = None):
        # 初始化
        super().__init__(parent)
        self.uid: str = uid
        self.collapsible: bool = True
        self.children: Dict[str, CollapsibleChild] = {}

        # 主布局
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # 可折叠按钮
        self.collapsibleButton = QToolButton(self)
        self.collapsibleButton.setIcon(QIcon("resource/expand.png"))
        self.collapsibleButton.setText(description)
        layout.addWidget(self.collapsibleButton)

        # 样式
        self.collapsibleButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.collapsibleButton.setFixedHeight(40)
        self.collapsibleButton.setMinimumWidth(150)
        self.collapsibleButton.setIconSize(QSize(25, 25))
        self.collapsibleButton.setObjectName("CollapsibleButton")
        self.collapsibleButton.setStyleSheet(
            "#CollapsibleButton{background-color:transparent}"
            "#CollapsibleButton:hover{background-color:rgba(51,51,51,0.4)}"
            "#CollapsibleButton:pressed{background-color:rgba(127,127,127,0.4)}"
            "#CollapsibleButton{font-family: 'Times New Roman'; font-size: 16px;}"
        )

        # 绑定事件
        self.collapsibleButton.clicked.connect(self.collapsibleButtonClicked)

        # 添加 child
        self.addChildren(series_image)

    def addChildren(self, series_image: dict) -> None:
        for series_uid, size_image in series_image.items():
            description = size_image.pop("description")
            for size_uid, image in size_image.items():
                child_uid = series_uid + "_._" + size_uid
                if child_uid in self.children:
                    continue
                child = CollapsibleChild(child_uid, description + " " + size_uid, image)
                # 绑定信号与槽
                child.deleted.connect(self.removeChild)
                child.checked.connect(self.childToggled)
                # 添加
                self.children[child_uid] = child
                # 设置布局
                self.layout().addWidget(child)
                child.setVisible(self.collapsible)
                if self.collapsible:
                    self.setFixedHeight(40 + (len(self.children) * 30))

    def removeChild(self, child_uid: str):
        _child = self.children.pop(child_uid)
        # 删除该子组件
        _child.close()
        _child.destroy()
        if len(self.children) == 0:
            self.deleted.emit(self.uid)
        else:
            self.setFixedHeight(40 + (len(self.children) * 30))

    def childToggled(self, child_uid: str, c: bool):
        self.childChecked.emit(self.uid, child_uid, c)

    def collapsibleButtonClicked(self) -> None:
        if self.collapsible:
            self.collapsibleButton.setIcon(QIcon("resource/collapse.png"))
            self.setFixedHeight(40)
            for child in self.children.values():
                child.radioButton.setChecked(False)
        else:
            self.collapsibleButton.setIcon(QIcon("resource/expand.png"))
            self.setFixedHeight(40 + (len(self.children) * 30))
        self.collapsible = not self.collapsible
        for child in self.children.values():
            child.setVisible(self.collapsible)

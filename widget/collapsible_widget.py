from typing import Dict

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QToolButton, QVBoxLayout, QWidget

from .collapsible_child import CollapsibleChild


class CollapsibleWidget(QWidget):
    child_toggled = pyqtSignal(str, str, bool)

    def __init__(self, uid: str, description: str, series_image: dict, parent: QWidget = None):
        # 初始化
        super().__init__(parent)
        self.uid: str = uid
        self.collapsed: bool = True
        self.children: Dict[str, CollapsibleChild] = {}

        # 样式
        self.setStyleSheet(
            "QToolButton {background-color: transparent; font-family: 'Times New Roman'; font-size: 16px;}"
            "QToolButton::hover {background-color: rgba(51,51,51,0.4)}"
            "QToolButton::pressed {background-color: rgba(127,127,127,0.4)}"
            "QScrollArea {background-color: transparent; border: none;}"
        )

        # 主布局
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # 可折叠按钮
        self.collapsible_button = QToolButton(self)
        self.collapsible_button.setIcon(QIcon("asset/icon/expand.png"))
        self.collapsible_button.setText(description)
        layout.addWidget(self.collapsible_button)

        # 样式
        self.collapsible_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.collapsible_button.setFixedHeight(40)
        self.collapsible_button.setMinimumWidth(150)
        self.collapsible_button.setIconSize(QSize(25, 25))

        # 绑定事件
        self.collapsible_button.clicked.connect(self.collapsible_button_clicked)

        # 添加 child
        self.add_children(series_image)

    def add_children(self, series_image: dict) -> None:
        for series_uid, size_image in series_image.items():
            description = size_image.pop("description")
            for size_uid, image in size_image.items():
                child_uid = series_uid + "_._" + size_uid
                if child_uid in self.children:
                    continue
                child = CollapsibleChild(child_uid, description + " " + size_uid, image)
                # 绑定信号与槽
                child.toggled.connect(self.toggle_child)
                # 添加
                self.children[child_uid] = child
                # 设置布局
                self.layout().addWidget(child)
                child.setVisible(self.collapsed)
                if self.collapsed:
                    self.setFixedHeight(40 + (len(self.children) * 30))

    def toggle_child(self, child_uid: str, c: bool):
        self.child_toggled.emit(self.uid, child_uid, c)

    def remove_child(self, child_uid: str):
        _child = self.children.pop(child_uid)
        _child.close()
        _child.destroy()
        if len(self.children) != 0:
            self.setFixedHeight(40 + (len(self.children) * 30))

    def collapsible_button_clicked(self) -> None:
        if self.collapsed:
            self.collapsible_button.setIcon(QIcon("asset/icon/collapse.png"))
            self.setFixedHeight(40)
            for child in self.children.values():
                child.radio_button.setChecked(False)
        else:
            self.collapsible_button.setIcon(QIcon("asset/icon/expand.png"))
            self.setFixedHeight(40 + (len(self.children) * 30))
        self.collapsed = not self.collapsed
        for child in self.children.values():
            child.setVisible(self.collapsed)

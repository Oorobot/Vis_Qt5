from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QHBoxLayout, QMenu, QRadioButton, QSizePolicy, QSpacerItem, QWidget

from utility.MedicalImage import MedicalImage


class CollapsibleChild(QWidget):
    deleted = pyqtSignal(str)
    checked = pyqtSignal(str, bool)

    uid: str
    image: MedicalImage

    def __init__(self, uid: str, description: str, image: MedicalImage, parent: QWidget = None) -> None:
        # 初始化
        super().__init__(parent)
        self.setStyleSheet(
            "QRadioButton {background-color: transparent; font-family: 'Times New Roman'; font-size: 15px;}"
            "QRadioButton::hover {background-color: rgba(64,70,75,0.4);}"
            "QRadioButton::pressed {background-color: rgba(119,136,153,0.4);}"
        )
        self.uid = uid
        self.image = image

        self.radio_button = QRadioButton(description, self)
        layout = QHBoxLayout()
        layout.addItem(QSpacerItem(28, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        layout.addWidget(self.radio_button)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setFixedHeight(30)
        self.setMinimumWidth(150)

        # 初始隐藏
        self.setVisible(False)

        # 右键
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showCustomContextMenu)
        self.contextMenu = QMenu()
        deleteAction = QAction(QIcon("asset/icon/delete.png"), "删除", self.contextMenu)
        self.contextMenu.addAction(deleteAction)

        deleteAction.triggered.connect(self.deleteActionTriggered)
        self.radio_button.toggled.connect(self.radioButtonToggled)

    def showCustomContextMenu(self, pos):
        self.contextMenu.show()
        self.contextMenu.move(self.mapToGlobal(pos))

    def deleteActionTriggered(self):
        self.deleted.emit(self.uid)

    def radioButtonToggled(self, c: bool):
        self.checked.emit(self.uid, c)

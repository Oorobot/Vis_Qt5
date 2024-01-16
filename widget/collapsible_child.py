from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QHBoxLayout, QRadioButton, QSizePolicy, QSpacerItem, QWidget

from utility import MedicalImage


class CollapsibleChild(QWidget):
    toggled = pyqtSignal(str, bool)

    def __init__(self, uid: str, description: str, image: MedicalImage, parent: QWidget = None) -> None:
        # 初始化
        super().__init__(parent)
        self.uid = uid
        self.image = image

        # 样式
        self.setStyleSheet(
            "QRadioButton {background-color: transparent; font-family: 'Times New Roman'; font-size: 15px;}"
            "QRadioButton::hover {background-color: rgba(64,70,75,0.4);}"
            "QRadioButton::pressed {background-color: rgba(119,136,153,0.4);}"
        )
        self.setVisible(False)  # 初始隐藏

        self.radio_button = QRadioButton(description, self)
        layout = QHBoxLayout()
        layout.addItem(QSpacerItem(28, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))
        layout.addWidget(self.radio_button)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.setFixedHeight(30)
        self.setMinimumWidth(150)

        self.radio_button.toggled.connect(self.radio_button_toggled)

    def radio_button_toggled(self, c: bool):
        self.toggled.emit(self.uid, c)

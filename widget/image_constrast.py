from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class ImageConstrast(QDialog):
    changed = pyqtSignal(float, float)

    def __init__(self, mi=0.0, ma=0.0, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setFixedSize(400, 150)

        self.setWindowTitle("对比度")
        validator = QDoubleValidator(self)

        label_min = QLabel()
        label_min.setText("最小值")
        label_min.setFixedWidth(40)
        label_min.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.edit_min = QLineEdit()
        self.edit_min.setText(str(mi))
        self.edit_min.setFixedWidth(80)
        self.edit_min.setValidator(validator)

        label_max = QLabel()
        label_max.setText("最大值")
        label_max.setFixedWidth(40)
        label_max.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.edit_max = QLineEdit()
        self.edit_max.setText(str(ma))
        self.edit_max.setFixedWidth(80)
        self.edit_max.setValidator(validator)

        layout1 = QHBoxLayout()
        layout1.setSpacing(0)
        layout1.setContentsMargins(0, 0, 10, 0)
        layout1.addWidget(label_min)
        layout1.addWidget(self.edit_min)
        layout1.addWidget(label_max)
        layout1.addWidget(self.edit_max)

        label_window_level = QLabel()
        label_window_level.setText("窗位")
        label_window_level.setFixedWidth(40)
        label_window_level.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.edit_window_level = QLineEdit()
        self.edit_window_level.setText(str((mi + ma) / 2))
        self.edit_window_level.setFixedWidth(80)
        self.edit_window_level.setValidator(validator)

        label_window_width = QLabel()
        label_window_width.setText("窗宽")
        label_window_width.setFixedWidth(40)
        label_window_width.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.edit_window_width = QLineEdit()
        self.edit_window_width.setText(str(ma - mi))
        self.edit_window_width.setFixedWidth(80)
        self.edit_window_width.setValidator(validator)

        layout2 = QHBoxLayout()
        layout2.setSpacing(0)
        layout2.setContentsMargins(0, 0, 10, 0)
        layout2.addWidget(label_window_level)
        layout2.addWidget(self.edit_window_level)
        layout2.addWidget(label_window_width)
        layout2.addWidget(self.edit_window_width)

        button = QPushButton()
        button.setText("确定")
        button.setFixedWidth(80)

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(layout1)
        layout.addLayout(layout2)
        layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignHCenter)

        self.setLayout(layout)

        #
        self.edit_max.editingFinished.connect(lambda: self.change("min_max"))
        self.edit_min.editingFinished.connect(lambda: self.change("min_max"))

        #
        self.edit_window_level.editingFinished.connect(lambda: self.change("level_width"))
        self.edit_window_width.editingFinished.connect(lambda: self.change("level_width"))

        #
        button.clicked.connect(self.clicked)

    def change(self, param: str):
        if param == "min_max":
            mi = 0.0 if len(self.edit_min.text()) == 0 else float(self.edit_min.text())
            ma = 0.0 if len(self.edit_min.text()) == 0 else float(self.edit_max.text())
            if mi > ma:
                ma = mi
            self.edit_min.setText(f"{mi:.2f}")
            self.edit_max.setText(f"{ma:.2f}")
            self.edit_window_level.setText(f"{(ma + mi) / 2:.2f}")
            self.edit_window_width.setText(f"{ma - mi:.2f}")
        elif param == "level_width":
            level = 0.0 if len(self.edit_window_level.text()) == 0 else float(self.edit_window_level.text())
            width = 0.0 if len(self.edit_window_width.text()) == 0 else float(self.edit_window_width.text())
            self.edit_min.setText(f"{level - width / 2:.2f}")
            self.edit_max.setText(f"{level + width / 2:.2f}")
            self.edit_window_level.setText(f"{level:.2f}")
            self.edit_window_width.setText(f"{width:.2f}")
        else:
            raise Exception(f"not supprot param = {param}")

    def clicked(self):
        mi, ma = float(self.edit_min.text()), float(self.edit_max.text())
        self.changed.emit(mi, ma)
        self.close()

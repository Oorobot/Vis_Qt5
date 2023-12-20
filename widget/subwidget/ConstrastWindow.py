from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget


class ConstrastWindow(QWidget):
    constrastChanged = pyqtSignal(float, float)

    def __init__(self, mi=0.0, ma=0.0, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.setFixedSize(400, 150)

        self.setWindowTitle("对比度")
        validator = QDoubleValidator(self)

        labelMin = QLabel()
        labelMin.setText("最小值")
        labelMin.setFixedWidth(40)
        labelMin.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.editMin = QLineEdit()
        self.editMin.setText(str(mi))
        self.editMin.setFixedWidth(80)
        self.editMin.setValidator(validator)

        labelMax = QLabel()
        labelMax.setText("最大值")
        labelMax.setFixedWidth(40)
        labelMax.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.editMax = QLineEdit()
        self.editMax.setText(str(ma))
        self.editMax.setFixedWidth(80)
        self.editMax.setValidator(validator)

        layout1 = QHBoxLayout()
        layout1.setSpacing(0)
        layout1.setContentsMargins(0, 0, 10, 0)
        layout1.addWidget(labelMin)
        layout1.addWidget(self.editMin)
        layout1.addWidget(labelMax)
        layout1.addWidget(self.editMax)

        labelWindowLevel = QLabel()
        labelWindowLevel.setText("窗位")
        labelWindowLevel.setFixedWidth(40)
        labelWindowLevel.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.editWindowLevel = QLineEdit()
        self.editWindowLevel.setText(str((mi + ma) / 2))
        self.editWindowLevel.setFixedWidth(80)
        self.editWindowLevel.setValidator(validator)

        labelWindowWidth = QLabel()
        labelWindowWidth.setText("窗宽")
        labelWindowWidth.setFixedWidth(40)
        labelWindowWidth.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.editWindowWidth = QLineEdit()
        self.editWindowWidth.setText(str(ma - mi))
        self.editWindowWidth.setFixedWidth(80)
        self.editWindowWidth.setValidator(validator)

        layout2 = QHBoxLayout()
        layout2.setSpacing(0)
        layout2.setContentsMargins(0, 0, 10, 0)
        layout2.addWidget(labelWindowLevel)
        layout2.addWidget(self.editWindowLevel)
        layout2.addWidget(labelWindowWidth)
        layout2.addWidget(self.editWindowWidth)

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
        self.editMax.editingFinished.connect(lambda: self.valueChanged("min_max"))
        self.editMin.editingFinished.connect(lambda: self.valueChanged("min_max"))

        #
        self.editWindowLevel.editingFinished.connect(lambda: self.valueChanged("level_width"))
        self.editWindowWidth.editingFinished.connect(lambda: self.valueChanged("level_width"))

        #
        button.clicked.connect(self.clicked)

    def valueChanged(self, param: str):
        if param == "min_max":
            mi = 0.0 if len(self.editMin.text()) == 0 else float(self.editMin.text())
            ma = 0.0 if len(self.editMin.text()) == 0 else float(self.editMax.text())
            if mi > ma:
                ma = mi
            self.editMin.setText(f"{mi:.2f}")
            self.editMax.setText(f"{ma:.2f}")
            self.editWindowLevel.setText(f"{(ma + mi) / 2:.2f}")
            self.editWindowWidth.setText(f"{ma - mi:.2f}")
        elif param == "level_width":
            level = 0.0 if len(self.editWindowLevel.text()) == 0 else float(self.editWindowLevel.text())
            width = 0.0 if len(self.editWindowWidth.text()) == 0 else float(self.editWindowWidth.text())
            self.editMin.setText(f"{level - width / 2:.2f}")
            self.editMax.setText(f"{level + width / 2:.2f}")
            self.editWindowLevel.setText(f"{level:.2f}")
            self.editWindowWidth.setText(f"{width:.2f}")
        else:
            raise Exception(f"not supprot param = {param}")

    def clicked(self):
        mi, ma = float(self.editMin.text()), float(self.editMax.text())
        self.constrastChanged.emit(mi, ma)
        self.close()

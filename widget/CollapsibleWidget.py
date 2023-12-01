from typing import List

from PyQt6 import QtCore
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QSizePolicy,
    QSpacerItem,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from entity import MedicalImage, ReadImage


class IconButton(QPushButton):
    def __init__(self, iconPath: str, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(30)
        self.setFixedHeight(30)

        pixmap = QPixmap(iconPath)
        layout = QHBoxLayout()
        self._icon = QLabel()
        self._icon.setScaledContents(True)
        self._icon.setStyleSheet("QLabel{background-color:transparent}")
        self._icon.setPixmap(pixmap)
        layout.addWidget(self._icon)
        self.setLayout(layout)


class CollapsibleChild(QWidget):
    def __init__(self, parent: QWidget, uid: str, image: MedicalImage) -> None:
        # 定义成员属性
        self._uid: str = ""
        self._text: QLabel = None

        # 初始化
        super().__init__(parent)
        self._uid = uid

        self._radioBtn = QRadioButton()
        self._text = QLabel()
        self._text.setText(image.description if image is not None else "UNKNOWN")
        self._image = image
        self.setVisible(False)
        self.setupUI()

    def setupUI(self):
        self.setFixedHeight(20)
        self._radioBtn.setFixedSize(20, 20)
        self._text.setMinimumWidth(80)
        layout = QHBoxLayout()
        spacer = QSpacerItem(30, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        layout.addItem(spacer)
        layout.addWidget(self._radioBtn)
        layout.addWidget(self._text)
        layout.addStretch
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 5, 0)
        self.setLayout(layout)


class CollapsibleButton(QPushButton):
    def __init__(self, uid: str, dictImage: dict, parent: QWidget = None):
        # 定义成员属性
        self._uid: str = None
        self._icon: QLabel = None
        self._text: QLabel = None
        self._children: List[CollapsibleChild] = []
        self._children_uid: List[str] = []
        self._children_visible: bool = False

        # 初始化
        super().__init__(parent)
        # 唯一标识符
        self._uid = uid

        # 图标
        self._icon = QLabel()
        self._icon.setFixedWidth(20)
        self._icon.setFixedHeight(20)
        self._icon.setScaledContents(True)
        self._icon.setStyleSheet("QLabel{background-color:transparent}")
        self._icon.setPixmap(QPixmap("resource/collapse.png"))

        # 文字
        self._text = QLabel()
        self._text.setStyleSheet("QLabel{background-color:transparent}")
        self._text.setText(self._uid.split("_")[-1])

        # 布局
        layoutMain = QVBoxLayout()
        layoutMain.setSpacing(1)
        layoutMain.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layoutMain)

        layoutBtn = QHBoxLayout()
        layoutBtn.addWidget(self._icon)
        layoutBtn.addWidget(self._text)
        layoutBtn.setContentsMargins(0, 0, 0, 0)
        layoutBtn.setSpacing(5)
        layoutMain.addLayout(layoutBtn)

        # 设置自身样式
        self.setFixedHeight(30)
        self.setObjectName("CollapsibleButton")
        self.setStyleSheet(
            "#CollapsibleButton{background-color:transparent}"
            "#CollapsibleButton:hover{background-color:rgba(195,195,195,0.4)}"
            "#CollapsibleButton:pressed{background-color:rgba(127,127,127,0.4)}"
        )

        # 添加子组件
        self.layoutChildren = QVBoxLayout()
        self.layoutChildren.setSpacing(0)
        self.layoutChildren.setContentsMargins(0, 0, 0, 0)
        layoutMain.addLayout(self.layoutChildren)
        self.addChildren(dictImage)

        # 绑定事件
        self.clicked.connect(self.clickedFunc)

    def addChildren(self, dictImage: dict) -> None:
        for i, d in dictImage.items():
            if i in self._children_uid:
                continue
            child = CollapsibleChild(self, i, d)
            self.layoutChildren.addWidget(child)
            self._children.append(child)
            self._children_uid.append(i)

    def clickedFunc(self) -> None:
        if self._children_visible:
            self._icon.setPixmap(QPixmap("resource/collapse.png"))
            self.setFixedHeight(30)
            for child in self._children:
                child._radioBtn.setChecked(False)
        else:
            self._icon.setPixmap(QPixmap("resource/expand.png"))
            self.setFixedHeight(30 + (len(self._children) * 20))
        self._children_visible = not self._children_visible
        for child in self._children:
            child.setVisible(self._children_visible)


class CollapsibleWidget(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        # 定义成员属性
        self._uid = {}

        # 初始化
        super().__init__(parent)
        self.resize(300, 400)

        layout = QHBoxLayout()

        self.widgetMain = QWidget()
        layoutMain = QVBoxLayout()
        self.widgetMain.setLayout(layoutMain)
        # 创建三个按钮
        self.openBtn = IconButton("resource/open.png")
        self.openBtn.setToolTip("打开文件")
        self.openBtn.setToolTipDuration(3000)
        self.display2DBtn = IconButton("resource/display2d.png")
        self.display2DBtn.setToolTip("2D浏览")
        self.display2DBtn.setToolTipDuration(3000)
        self.display3DBtn = IconButton("resource/display3d.png")
        self.display3DBtn.setToolTip("3D浏览")
        self.display3DBtn.setToolTipDuration(3000)
        layoutBtn = QHBoxLayout()
        layoutBtn.setSpacing(20)
        layoutBtn.setContentsMargins(0, 0, 0, 0)
        layoutBtn.addWidget(self.openBtn)
        layoutBtn.addWidget(self.display2DBtn)
        layoutBtn.addWidget(self.display3DBtn)

        layoutMain.addLayout(layoutBtn)
        # BtnList
        self.layoutCBtn = QVBoxLayout()
        self.layoutCBtn.setSpacing(0)
        self.layoutCBtn.setContentsMargins(0, 0, 0, 0)
        # for uid, dictImage in uidDictImage.items():
        #     collapsibleButton = CollapsibleButton(uid, dictImage)
        #     self.layoutCBtn.addWidget(collapsibleButton)

        layoutMain.addLayout(self.layoutCBtn)
        # Strech
        spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layoutMain.addItem(spacer)
        layout.addWidget(self.widgetMain)

        # 侧边隐藏按钮
        self.hideBtn = QToolButton()
        self.hideBtn.setArrowType(QtCore.Qt.ArrowType.LeftArrow)
        self.hideBtn.setFixedHeight(60)
        self.hideBtn.setFixedWidth(15)
        layoutHide = QVBoxLayout()
        layoutHide.setSpacing(0)
        layoutHide.setContentsMargins(0, 0, 0, 0)
        spacer1Hide = QSpacerItem(10, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layoutHide.addItem(spacer1Hide)
        layoutHide.addWidget(self.hideBtn)
        spacer2Hide = QSpacerItem(10, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        layoutHide.addItem(spacer2Hide)
        layout.addLayout(layoutHide)

        self.setLayout(layout)

        # 绑定
        self.hideBtn.clicked.connect(self.hideBtnClickFunc)
        self.openBtn.clicked.connect(self.openBthClickFunc)

    def addCollapsibleButton(self, uidDictImage: dict):
        for uid, dictImage in uidDictImage.items():
            if uid in self._uid:
                self._uid[uid].addChildren(dictImage)
                continue
            collapsibleButton = CollapsibleButton(uid, dictImage)
            self.layoutCBtn.addWidget(collapsibleButton)
            self._uid[uid] = collapsibleButton

    def hideBtnClickFunc(self):
        if self.widgetMain.isVisible():
            self.widgetMain.setVisible(False)
            self.hideBtn.setArrowType(QtCore.Qt.ArrowType.RightArrow)
        else:
            self.widgetMain.setVisible(True)
            self.hideBtn.setArrowType(QtCore.Qt.ArrowType.LeftArrow)

    def openBthClickFunc(self):
        filename = QFileDialog().getOpenFileName(
            self, "选择文件", "./", filter="IMAGE(*.dcm *.nii *.nii.gz);;NIFTI(*.nii *.nii.gz);;DICOM(*.dcm)"
        )
        if len(filename[0]) == 0:
            return

        uidDictImage = ReadImage(filename[0])
        self.addCollapsibleButton(uidDictImage)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    uidDictImage = {
        "123_nieliangbing": {"1_CT": None, "2_PT": None},
        "456_peisiqi": {"1_CT": None, "2_PT": None},
        "1_peisiqi": {"1_CT": None, "2_PT": None},
        "2_peisiqi": {"1_CT": None, "2_PT": None},
        "3_peisiqi": {"1_CT": None, "2_PT": None},
        "4_peisiqi": {"1_CT": None, "2_PT": None},
        "5_peisiqi": {"1_CT": None, "2_PT": None},
        "6_peisiqi": {"1_CT": None, "2_PT": None},
        "7_peisiqi": {"1_CT": None, "2_PT": None},
        "8_peisiqi": {"1_CT": None, "2_PT": None},
        "9_peisiqi": {"1_CT": None, "2_PT": None},
        "10_peisiqi": {"1_CT": None, "2_PT": None},
        "11_peisiqi": {"1_CT": None, "2_PT": None},
        "12_peisiqi": {"1_CT": None, "2_PT": None},
    }
    MainWindow = CollapsibleWidget()
    MainWindow.show()
    sys.exit(app.exec())

from typing import Union

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator, QFont, QIcon, QIntValidator
from PyQt6.QtWidgets import (
    QFileDialog,
    QGraphicsView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QSlider,
    QToolBar,
    QToolButton,
    QWidget,
)

from utility.constant import VIEW_TO_NAME
from utility.io import ReadNIFTI
from utility.MedicalImage import MedicalImage
from utility.MedicalImage2 import MedicalImage2
from widget.GraphicsView import GraphicsView
from widget.subwidget.ConstrastWindow import ConstrastWindow


class ImageViewer(QMainWindow):
    opacityChanged = pyqtSignal(float)

    def __init__(self, bimodal: bool = False, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.bimodal = bimodal

        toolbar = QToolBar()
        toolbar.setStyleSheet("border: none;")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        # 视图和位置信息
        self.viewName = QLabel()
        self.viewName.setFixedWidth(80)
        self.viewName.setText(VIEW_TO_NAME["t"])
        self.viewName.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.viewName.setStyleSheet("background-color: transparent; color: #12074D")
        self.viewName.setFont(QFont("楷体", 12))
        self.positionMax = QLabel()
        self.positionMax.setText(str(0))
        self.positionMax.setFixedWidth(35)
        self.positionMax.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.positionMax.setStyleSheet("background-color: transparent; color: #07255C")
        self.positionMax.setFont(QFont("Times New Roman", 12))
        self.positionCurrent = QLineEdit()
        self.positionCurrent.setText("0")
        self.positionCurrent.setFixedWidth(35)
        self.positionCurrent.setValidator(QIntValidator())
        self.positionCurrent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.positionCurrent.setFont(QFont("Times New Roman", 12))
        self.positionCurrent.setStyleSheet("background-color: transparent; border: none; color: #135170")
        toolbar.addWidget(self.viewName)
        toolbar.addWidget(self.positionMax)
        toolbar.addWidget(self.positionCurrent)
        toolbar.addSeparator()

        # 三视图
        viewButton = QToolButton()
        viewButton.setText("视图")
        viewButton.setIcon(QIcon("resource/view.png"))
        viewButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        viewButton.setAutoRaise(True)
        viewButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        viewMenu = QMenu()
        viewS = viewMenu.addAction(QIcon("resource/S.png"), "矢状面")
        viewC = viewMenu.addAction(QIcon("resource/C.png"), "冠状面")
        viewT = viewMenu.addAction(QIcon("resource/T.png"), "横截面")
        viewButton.setMenu(viewMenu)
        toolbar.addWidget(viewButton)

        # 操作：重置、翻转
        operateButton = QToolButton()
        operateButton.setText("操作")
        operateButton.setIcon(QIcon("resource/operate.png"))
        operateButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        operateButton.setAutoRaise(True)
        operateButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        operateMenu = QMenu()
        operateReset = operateMenu.addAction(QIcon("resource/reset.png"), "复原")
        operateFlipH = operateMenu.addAction(QIcon("resource/flipH.png"), "水平")
        operateFlipV = operateMenu.addAction(QIcon("resource/flipV.png"), "垂直")
        operateButton.setMenu(operateMenu)
        toolbar.addWidget(operateButton)

        # 鼠标左键
        self.mouseLeftButton = QToolButton()
        self.mouseLeftButton.setText("普通")
        self.mouseLeftButton.setIcon(QIcon("resource/arrow.png"))
        self.mouseLeftButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.mouseLeftButton.setAutoRaise(True)
        self.mouseLeftButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        mouseLeftMenu = QMenu()
        mouseLeftNormal = mouseLeftMenu.addAction(QIcon("resource/arrow.png"), "普通")
        mouseLeftDrag = mouseLeftMenu.addAction(QIcon("resource/drag.png"), "拖动")
        self.mouseLeftButton.setMenu(mouseLeftMenu)
        toolbar.addWidget(self.mouseLeftButton)

        # 鼠标滑轮
        self.wheelButton = QToolButton()
        self.wheelButton.setText("切换")
        self.wheelButton.setIcon(QIcon("resource/slide.png"))
        self.wheelButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.wheelButton.setAutoRaise(True)
        self.wheelButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        wheelMenu = QMenu()
        wheelSlide = wheelMenu.addAction(QIcon("resource/slide.png"), "切换")
        wheelResize = wheelMenu.addAction(QIcon("resource/resize.png"), "缩放")
        self.wheelButton.setMenu(wheelMenu)
        toolbar.addWidget(self.wheelButton)
        toolbar.addSeparator()

        # 对比度
        constrastButton = QToolButton()
        constrastButton.setText("对比度")
        constrastButton.setIcon(QIcon("resource/constrast.png"))
        constrastButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.constrastWindow = ConstrastWindow()
        toolbar.addWidget(constrastButton)

        if bimodal:
            self.constrastSlider = QSlider(Qt.Orientation.Horizontal)
            self.constrastSlider.setValue(25)
            self.constrastSlider.setRange(0, 50)
            self.constrastSlider.setSingleStep(1)
            self.constrastSlider.setMinimumWidth(50)
            self.constrastSlider.setMaximumWidth(100)
            self.constrastMax = QLineEdit()
            self.constrastMax.setValidator(QDoubleValidator())
            self.constrastMax.setText("5.0")
            self.constrastMax.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.constrastMax.setStyleSheet("background-color: transparent; border: none;")
            self.constrastMax.setFixedWidth(30)
            self.constrastMax.setFont(QFont("Times New Roman", 12))
            toolbar.addWidget(self.constrastSlider)
            toolbar.addWidget(self.constrastMax)
            toolbar.addSeparator()

            # 信号与槽
            self.constrastSlider.valueChanged.connect(self.adjustConstrast2)
            self.constrastMax.textEdited.connect(self.validateConstrastMax2)
            self.constrastMax.editingFinished.connect(self.adjustConstrastMax2)

        # 标签、透明度
        labelButton = QToolButton()
        labelButton.setText("标签")
        labelButton.setIcon(QIcon("resource/label.png"))
        labelButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        labelSlider = QSlider(Qt.Orientation.Horizontal)
        labelSlider.setRange(0, 100)
        labelSlider.setValue(50)
        labelSlider.setSingleStep(1)
        labelSlider.setMinimumWidth(50)
        labelSlider.setMaximumWidth(100)
        toolbar.addWidget(labelButton)
        toolbar.addWidget(labelSlider)
        toolbar.addSeparator()

        self.addToolBar(toolbar)
        self.view = GraphicsView("t", self)
        self.setCentralWidget(self.view)

        self.resize(1920, 1080)

        # 信号与槽
        viewS.triggered.connect(lambda: self.setView("s"))
        viewC.triggered.connect(lambda: self.setView("c"))
        viewT.triggered.connect(lambda: self.setView("t"))

        operateReset.triggered.connect(self.activateReset)
        operateFlipH.triggered.connect(self.flipHorizontal)
        operateFlipV.triggered.connect(self.flipVertical)

        mouseLeftNormal.triggered.connect(self.deactivateDragMode)
        mouseLeftDrag.triggered.connect(self.activateDragMode)

        wheelResize.triggered.connect(self.activateResizeMode)
        wheelSlide.triggered.connect(self.activateSlideMode)

        constrastButton.clicked.connect(self.activateConstrastWindow)

        labelButton.clicked.connect(self.openLabel)
        labelSlider.valueChanged.connect(self.adjustLabelOpacity)

        self.view.positionChanged.connect(self.setPosition)
        self.positionCurrent.editingFinished.connect(self.setCurrentPlane)
        self.positionCurrent.textEdited.connect(self.validatePosition)

        self.opacityChanged.connect(self.view.setLabelItemOpacity)

    # 复原
    def activateReset(self):
        self.view.reset()

    # 水平翻转
    def flipHorizontal(self):
        self.view.horizontalFlip()

    # 垂直翻转
    def flipVertical(self):
        self.view.verticalFlip()

    # 拖动
    def activateDragMode(self):
        self.mouseLeftButton.setText("拖动")
        self.mouseLeftButton.setIcon(QIcon("resource/drag.png"))
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    # 取消拖动
    def deactivateDragMode(self):
        self.mouseLeftButton.setText("普通")
        self.mouseLeftButton.setIcon(QIcon("resource/arrow.png"))
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    # 缩放
    def activateResizeMode(self):
        self.wheelButton.setText("缩放")
        self.wheelButton.setIcon(QIcon("resource/resize.png"))
        self.view.resizeOrSlide = True

    # 切换
    def activateSlideMode(self):
        self.wheelButton.setText("切换")
        self.wheelButton.setIcon(QIcon("resource/slide.png"))
        self.view.resizeOrSlide = False

    # 对比度
    def activateConstrastWindow(self):
        self.constrastWindow.show()
        self.constrastWindow.constrastChanged.connect(self.adjustConstrast)

    # 调整对比度
    def adjustConstrast(self, mi, ma):
        if self.view.image is not None:
            self.view.image.normlize(mi, ma)
            self.view.setCurrentPlane()

    def adjustConstrast2(self, ma):
        if self.view.image is not None:
            self.view.image.normlize(0, ma * 0.1, "PT")
            self.view.setCurrentPlane()

    def validateConstrastMax2(self, t: str):
        if t == "" or float(t) <= 0:
            self.constrastMax.setText("5.0")
        else:
            return

    def adjustConstrastMax2(self):
        ma = float(self.constrastMax.text())
        self.constrastMax.setText(f"{ma:.1f}")
        ma = float(self.constrastMax.text())
        self.constrastSlider.setMaximum(int(ma * 10))

    # 打开分割图
    def openLabel(self):
        filename = QFileDialog().getOpenFileName(self, "选择文件", "./", filter="NIFTI(*.nii *.nii.gz);;")
        if len(filename[0]) == 0:
            return

        labelImage = ReadNIFTI(filename[0], True)
        self.view.setLabel(labelImage)

    # 调整分割图透明度
    def adjustLabelOpacity(self, v: int):
        self.opacityChanged.emit(v * 0.01)

    def setView(self, v: str):
        self.view.setView(v)
        self.viewName.setText(VIEW_TO_NAME[v])
        self.positionCurrent.setText(str(self.view.position))
        self.positionMax.setText(str(self.view.position_max))

    def setPosition(self, p: int):
        self.positionCurrent.setText(str(p))

    def setCurrentPlane(self):
        self.view.position = int(self.positionCurrent.text())
        self.view.setCurrentPlane()

    def validatePosition(self, t: str):
        if t == "" or int(t) < 1:
            self.positionCurrent.setText("1")
        elif int(t) > self.view.position_max:
            self.positionCurrent.setText(str(self.view.position_max))
        else:
            return

    def setImage(self, image: Union[MedicalImage, MedicalImage2]):
        mi, ma = image.array.min(), image.array.max()
        self.constrastWindow.editMin.setText(f"{mi:.2f}")
        self.constrastWindow.editMax.setText(f"{ma:.2f}")
        self.constrastWindow.editWindowLevel.setText(f"{(mi + ma) / 2:.2f}")
        self.constrastWindow.editWindowWidth.setText(f"{ma- mi:.2f}")
        self.view.setImage(image)
        self.positionCurrent.setText(str(self.view.position))
        self.positionMax.setText(str(self.view.position_max))


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    MainWindow = ImageViewer()
    image = ReadNIFTI(r"DATA\001_CT.nii.gz", True)
    MainWindow.setImage(image)
    MainWindow.show()
    sys.exit(app.exec())

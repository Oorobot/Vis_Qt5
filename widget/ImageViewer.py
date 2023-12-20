from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QIntValidator
from PyQt6.QtWidgets import (
    QFileDialog,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from utility.constant import VIEW_NAME
from utility.io import ReadNIFTI
from utility.MedicalImage import MedicalImage
from widget.GraphicsView import GraphicsView
from widget.subwidget.ConstrastWindow import ConstrastWindow


class ImageViewer(QWidget):
    opacityChanged = pyqtSignal(float)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        toolbar = QToolBar(self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        resetButton = QToolButton()
        resetButton.setText("复原")
        resetButton.setIcon(QIcon("resource/reset.png"))
        resetButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(resetButton)
        toolbar.addSeparator()

        arrowButton = QToolButton()
        arrowButton.setText("普通")
        arrowButton.setIcon(QIcon("resource/arrow.png"))
        arrowButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        dragButton = QToolButton()
        dragButton.setText("拖动")
        dragButton.setIcon(QIcon("resource/drag.png"))
        dragButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(arrowButton)
        toolbar.addWidget(dragButton)
        toolbar.addSeparator()

        resizeButton = QToolButton()
        resizeButton.setText("缩放")
        resizeButton.setIcon(QIcon("resource/resize.png"))
        resizeButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        slideButton = QToolButton()
        slideButton.setText("切换")
        slideButton.setIcon(QIcon("resource/slide.png"))
        slideButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(resizeButton)
        toolbar.addWidget(slideButton)
        toolbar.addSeparator()

        viewButton = QToolButton()
        viewButton.setText("视图")
        viewButton.setAutoRaise(True)
        viewButton.setIcon(QIcon("resource/view.png"))
        viewButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        viewButton.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        viewSubMenu = QMenu()
        viewS = viewSubMenu.addAction(QIcon("resource/S.png"), "矢状面")
        viewC = viewSubMenu.addAction(QIcon("resource/C.png"), "冠状面")
        viewT = viewSubMenu.addAction(QIcon("resource/T.png"), "横截面")
        viewButton.setMenu(viewSubMenu)
        toolbar.addWidget(viewButton)
        toolbar.addSeparator()

        constrastButton = QToolButton()
        constrastButton.setText("对比度")
        constrastButton.setIcon(QIcon("resource/constrast.png"))
        constrastButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.constrastWindow = ConstrastWindow()

        toolbar.addWidget(constrastButton)
        toolbar.addSeparator()

        flipHButton = QToolButton()
        flipHButton.setText("水平")
        flipHButton.setIcon(QIcon("resource/flipH.png"))
        flipHButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        flipVButton = QToolButton()
        flipVButton.setText("垂直")
        flipVButton.setIcon(QIcon("resource/flipV.png"))
        flipVButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(flipHButton)
        toolbar.addWidget(flipVButton)
        toolbar.addSeparator()

        maskButton = QToolButton()
        maskButton.setText("分割图")
        maskButton.setIcon(QIcon("resource/mask.png"))
        maskButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        maskSlider = QSlider(Qt.Orientation.Horizontal)
        maskSlider.setRange(0, 100)
        maskSlider.setValue(50)
        maskSlider.setSingleStep(1)
        maskSlider.setFixedWidth(100)

        toolbar.addWidget(maskButton)
        toolbar.addWidget(maskSlider)
        toolbar.addSeparator()

        # 视图信息和切换信息
        toolInfoLayout = QHBoxLayout()
        toolInfoLayout.addWidget(toolbar)
        toolInfoLayout.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        font = QFont("黑体", 14)
        self.viewName = QLabel()
        self.viewName.setText(VIEW_NAME["t"])
        self.viewName.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.viewName.setStyleSheet("background-color:transparent; color: rgb(255, 0, 0)")
        self.viewName.setFont(font)
        self.positionCurrent = QLineEdit()
        self.positionCurrent.setText("0")
        self.positionCurrent.setFixedWidth(50)
        self.positionCurrent.setValidator(QIntValidator())
        self.positionCurrent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.positionCurrent.setStyleSheet("background-color:transparent; color: rgb(0, 0, 255)")
        self.positionCurrent.setFont(font)
        self.positionMax = QLabel()
        self.positionMax.setText(str(0))
        self.positionMax.setFixedWidth(50)
        self.positionMax.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.positionMax.setStyleSheet("background-color:transparent; color: rgb(0, 0, 255)")
        self.positionMax.setFont(font)

        toolInfoLayout.addWidget(self.positionCurrent)
        toolInfoLayout.addWidget(self.viewName)
        toolInfoLayout.addWidget(self.positionMax)

        self.view = GraphicsView("t", self)

        layout = QVBoxLayout()
        layout.addLayout(toolInfoLayout)
        layout.addWidget(self.view)

        self.setLayout(layout)
        self.resize(1920, 1080)

        # 绑定函数
        resetButton.clicked.connect(self.activateReset)
        arrowButton.clicked.connect(self.deactivateDragMode)
        dragButton.clicked.connect(self.activateDragMode)
        resizeButton.clicked.connect(self.activateResizeMode)
        slideButton.clicked.connect(self.activateSlideMode)
        constrastButton.clicked.connect(self.activateConstrastWindow)
        flipHButton.clicked.connect(self.flipHorizontal)
        flipVButton.clicked.connect(self.flipVertical)
        maskButton.clicked.connect(self.openMask)
        maskSlider.valueChanged.connect(self.adjustMaskOpacity)

        viewS.triggered.connect(self.setViewS)
        viewC.triggered.connect(self.setViewC)
        viewT.triggered.connect(self.setViewT)

        self.view.positionChanged.connect(self.setPosition)
        self.positionCurrent.editingFinished.connect(self.setCurrentPlane)
        self.positionCurrent.textEdited.connect(self.validatePosition)

        self.opacityChanged.connect(self.view.setLabelItemOpacity)

    # 复原
    def activateReset(self):
        self.view.reset()

    # 拖动
    def activateDragMode(self):
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    # 取消拖动
    def deactivateDragMode(self):
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    # 缩放
    def activateResizeMode(self):
        self.view.resizeOrSlide = True

    # 切换
    def activateSlideMode(self):
        self.view.resizeOrSlide = False

    # 对比度
    def activateConstrastWindow(self):
        self.constrastWindow.show()
        self.constrastWindow.constrastChanged.connect(self.adjustConstrast)

    # 调整对比度
    def adjustConstrast(self, mi, ma):
        if self.view.image is not None:
            self.view.image.normlize(mi, ma)
            self.view.setImageItem(self.view.image.plane_norm(self.view.view, self.view.position))
        if self.view.label is not None:
            self.view.setLabelItem(self.view.label.plane_origin(self.view.view, self.view.position))

    # 水平翻转
    def flipHorizontal(self):
        self.view.horizontalFlip()

    # 垂直翻转
    def flipVertical(self):
        self.view.verticalFlip()

    # 打开分割图
    def openMask(self):
        filename = QFileDialog().getOpenFileName(self, "选择文件", "./", filter="NIFTI(*.nii *.nii.gz);;")
        if len(filename[0]) == 0:
            return

        maskImage = ReadNIFTI(filename[0], True)
        self.setLabel(maskImage)

    # 调整分割图透明度
    def adjustMaskOpacity(self, v: float):
        self.opacityChanged.emit(v * 0.01)

    def setViewS(self):
        self.view.setView("s")
        self.viewName.setText(VIEW_NAME["s"])
        self.positionCurrent.setText(str(self.view.position))
        self.positionMax.setText(str(self.view.position_max))

    def setViewC(self):
        self.view.setView("c")
        self.viewName.setText(VIEW_NAME["c"])
        self.positionCurrent.setText(str(self.view.position))
        self.positionMax.setText(str(self.view.position_max))

    def setViewT(self):
        self.view.setView("t")
        self.viewName.setText(VIEW_NAME["t"])
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
            pass

    def setImage(self, image: MedicalImage):
        mi, ma = image.array.min(), image.array.max()
        self.constrastWindow.editMin.setText(f"{mi:.2f}")
        self.constrastWindow.editMax.setText(f"{ma:.2f}")
        self.constrastWindow.editWindowLevel.setText(f"{(mi + ma) / 2:.2f}")
        self.constrastWindow.editWindowWidth.setText(f"{ma- mi:.2f}")
        self.view.setImage(image)
        self.positionCurrent.setText(str(self.view.position))
        self.positionMax.setText(str(self.view.position_max))

    def setLabel(self, label: MedicalImage):
        self.view.setLabel(label)


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    MainWindow = ImageViewer()
    image = ReadNIFTI(r"DATA\001_CT.nii.gz", True)
    MainWindow.setImage(image)
    MainWindow.show()
    sys.exit(app.exec())

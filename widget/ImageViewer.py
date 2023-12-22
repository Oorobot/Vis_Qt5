from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QIntValidator
from PyQt6.QtWidgets import (
    QFileDialog,
    QGraphicsView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QSizePolicy,
    QSlider,
    QSpacerItem,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from utility.constant import VIEW_TO_NAME
from utility.io import ReadNIFTI
from utility.MedicalImage import MedicalImage
from widget.GraphicsView import GraphicsView
from widget.subwidget.ConstrastWindow import ConstrastWindow


class ImageViewer(QMainWindow):
    opacityChanged = pyqtSignal(float)

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        # 视图和位置信息
        font = QFont("黑体", 14)
        self.viewName = QLabel()
        self.viewName.setText(VIEW_TO_NAME["t"])
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
        self.positionCurrent.setStyleSheet("background-color: transparent;border: none;color: #1E1E1E;")
        self.positionMax = QLabel()
        self.positionMax.setText(str(0))
        self.positionMax.setFixedWidth(50)
        self.positionMax.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.positionMax.setStyleSheet("background-color:transparent; color: rgb(0, 0, 255)")
        self.positionMax.setFont(font)

        toolbar.addWidget(self.viewName)
        toolbar.addWidget(self.positionMax)
        toolbar.addSeparator()
        toolbar.addWidget(self.positionCurrent)
        toolbar.addSeparator()

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

        labelButton = QToolButton()
        labelButton.setText("分割图")
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

        self.view = GraphicsView("t", self)

        self.addToolBar(toolbar)
        self.setCentralWidget(self.view)

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
        labelButton.clicked.connect(self.openLabel)
        labelSlider.valueChanged.connect(self.adjustLabelOpacity)

        viewS.triggered.connect(lambda: self.setView("s"))
        viewC.triggered.connect(lambda: self.setView("c"))
        viewT.triggered.connect(lambda: self.setView("t"))

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


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    MainWindow = ImageViewer()
    image = ReadNIFTI(r"DATA\001_CT.nii.gz", True)
    MainWindow.setImage(image)
    MainWindow.show()
    sys.exit(app.exec())

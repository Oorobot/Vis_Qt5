from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QFileDialog,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QMenu,
    QSizePolicy,
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
from widget.subwidget.SubWindowConstrast import SubWindowConstrast


class ImageViewer(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        toolbar = QToolBar(self)
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        resetBtn = QToolButton()
        resetBtn.setText("复原")
        resetBtn.setIcon(QIcon("resource/reset.png"))
        resetBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(resetBtn)
        toolbar.addSeparator()

        arrowBtn = QToolButton()
        arrowBtn.setText("普通")
        arrowBtn.setIcon(QIcon("resource/arrow.png"))
        arrowBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        dragBtn = QToolButton()
        dragBtn.setText("拖动")
        dragBtn.setIcon(QIcon("resource/drag.png"))
        dragBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(arrowBtn)
        toolbar.addWidget(dragBtn)
        toolbar.addSeparator()

        resizeBtn = QToolButton()
        resizeBtn.setText("缩放")
        resizeBtn.setIcon(QIcon("resource/resize.png"))
        resizeBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        slideBtn = QToolButton()
        slideBtn.setText("切换")
        slideBtn.setIcon(QIcon("resource/slide.png"))
        slideBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(resizeBtn)
        toolbar.addWidget(slideBtn)
        toolbar.addSeparator()

        viewBtn = QToolButton()
        viewBtn.setText("视图")
        viewBtn.setAutoRaise(True)
        viewBtn.setIcon(QIcon("resource/view.png"))
        viewBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        viewBtn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        viewSubMenu = QMenu()
        viewS = viewSubMenu.addAction(QIcon("resource/S.png"), "矢状面")
        viewC = viewSubMenu.addAction(QIcon("resource/C.png"), "冠状面")
        viewT = viewSubMenu.addAction(QIcon("resource/T.png"), "横截面")
        viewBtn.setMenu(viewSubMenu)
        toolbar.addWidget(viewBtn)
        toolbar.addSeparator()

        constrastBtn = QToolButton()
        constrastBtn.setText("对比度")
        constrastBtn.setIcon(QIcon("resource/constrast.png"))
        constrastBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.subWindowConstrast = SubWindowConstrast()

        toolbar.addWidget(constrastBtn)
        toolbar.addSeparator()

        flipHBtn = QToolButton()
        flipHBtn.setText("水平")
        flipHBtn.setIcon(QIcon("resource/flipH.png"))
        flipHBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        flipVBtn = QToolButton()
        flipVBtn.setText("垂直")
        flipVBtn.setIcon(QIcon("resource/flipV.png"))
        flipVBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(flipHBtn)
        toolbar.addWidget(flipVBtn)
        toolbar.addSeparator()

        maskBtn = QToolButton()
        maskBtn.setText("分割图")
        maskBtn.setIcon(QIcon("resource/mask.png"))
        maskBtn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        toolbar.addWidget(maskBtn)
        toolbar.addSeparator()

        # 视图信息和切换信息
        toolInfoLayout = QHBoxLayout()
        toolInfoLayout.addWidget(toolbar)
        toolInfoLayout.addSpacerItem(QSpacerItem(5, 5, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        font = QFont("黑体", 14)
        self.viewInfo = QLabel()
        self.viewInfo.setText(VIEW_NAME["t"])
        self.viewInfo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.viewInfo.setStyleSheet("background-color:transparent; color: rgb(255, 0, 0)")
        self.viewInfo.setFont(font)
        self.slideInfo = QLabel()
        self.slideInfo.setText("{:0>4d}|{:0>4d}".format(0, 0))
        self.slideInfo.setFixedWidth(100)
        self.slideInfo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.slideInfo.setStyleSheet("background-color:transparent; color: rgb(255, 0, 0)")
        self.slideInfo.setFont(font)
        toolInfoLayout.addWidget(self.viewInfo)
        toolInfoLayout.addWidget(self.slideInfo)

        self.view = GraphicsView("t", self)

        layout = QVBoxLayout()
        layout.addLayout(toolInfoLayout)
        layout.addWidget(self.view)

        self.setLayout(layout)
        self.resize(1920, 1080)

        # 绑定函数
        resetBtn.clicked.connect(self.activateReset)
        arrowBtn.clicked.connect(self.deactivateDragMode)
        dragBtn.clicked.connect(self.activateDragMode)
        resizeBtn.clicked.connect(self.activateResizeMode)
        slideBtn.clicked.connect(self.activateSlideMode)
        constrastBtn.clicked.connect(self.activateConstrastWindow)
        flipHBtn.clicked.connect(self.flipHorizontal)
        flipVBtn.clicked.connect(self.flipVertical)
        maskBtn.clicked.connect(self.openMask)

        viewS.triggered.connect(self.setViewS)
        viewC.triggered.connect(self.setViewC)
        viewT.triggered.connect(self.setViewT)

        self.view.position_changed.connect(self.setPosition)

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
        self.subWindowConstrast.show()
        self.subWindowConstrast.constrastValue.connect(self.adjustConstrast)

    # 调整对比度
    def adjustConstrast(self, mi, ma):
        if self.view.image is not None:
            self.view.image.normlize(mi, ma)
            self.view.setImageItem(self.view.image.plane_norm(self.view.view, self.view.position))
        if self.view.label is not None:
            self.view.setLabelItem(self.view.label.plane_origin(self.view.view, self.view.position))

    def flipHorizontal(self):
        self.view.horizontalFlip()

    def flipVertical(self):
        self.view.verticalFlip()

    def openMask(self):
        filename = QFileDialog().getOpenFileName(self, "选择文件", "./", filter="NIFTI(*.nii *.nii.gz);;")
        if len(filename[0]) == 0:
            return

        maskImage = ReadNIFTI(filename[0], True)
        self.setLabel(maskImage)

    def setViewS(self):
        self.view.setView("s")
        self.viewInfo.setText(VIEW_NAME["s"])

    def setViewC(self):
        self.view.setView("c")
        self.viewInfo.setText(VIEW_NAME["c"])

    def setViewT(self):
        self.view.setView("t")
        self.viewInfo.setText(VIEW_NAME["t"])

    def setPosition(self, text: str):
        self.slideInfo.setText(text)

    def setImage(self, image: MedicalImage):
        mi, ma = image.array.min(), image.array.max()
        self.subWindowConstrast.editMin.setText(f"{mi:.2f}")
        self.subWindowConstrast.editMax.setText(f"{ma:.2f}")
        self.subWindowConstrast.editWindowLevel.setText(f"{(mi + ma) / 2:.2f}")
        self.subWindowConstrast.editWindowWidth.setText(f"{ma- mi:.2f}")
        self.view.setImage(image)

    def setLabel(self, label: MedicalImage):
        self.view.setLabel(label)


if __name__ == "__main__":
    import sys

    from PyQt6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    MainWindow = ImageViewer()
    image = ReadNIFTI(r"DATA\001_CT.nii.gz", True)
    # image = ReadDICOM(r"DATA\001\CT\ImageFileName000.dcm").popitem()
    # image = image[1].popitem()
    # image = image[1]
    # label = ReadNIFTI(r"DATA\001_Label_Body.nii.gz", True)
    # label.convertLabelMask()
    MainWindow.setImage(image)
    # MainWindow.setLabel(label)
    MainWindow.show()
    sys.exit(app.exec())

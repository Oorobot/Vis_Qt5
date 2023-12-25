from typing import Union

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QTabBar, QTabWidget, QToolButton, QWidget

from utility.MedicalImage import MedicalImage
from utility.MedicalImage2 import MedicalImage2
from widget.ImageViewer import ImageViewer
from widget.Sidebar import Sidebar
from widget.VTKWidget import VTKWidget


class Main(QMainWindow):
    def __init__(self) -> None:
        super(Main, self).__init__()
        self.tabs = []

        widget = QWidget(self)
        self.setCentralWidget(widget)
        layout = QHBoxLayout(widget)

        # 侧边栏
        self.sidebar = Sidebar(self)
        layout.addWidget(self.sidebar, 1)

        # 侧边栏隐藏按钮
        self.hideButton = QToolButton(self)
        self.hideButton.setArrowType(Qt.ArrowType.LeftArrow)
        self.hideButton.setFixedHeight(60)
        self.hideButton.setFixedWidth(15)
        layout.addWidget(self.hideButton)

        # 标签页
        self.tabWidget = QTabWidget(self)
        layout.addWidget(self.tabWidget, 4)

        # 信号与槽
        self.sidebar.displayImage2D.connect(self.addTab)
        self.sidebar.displayImage3D.connect(self.addTab)
        self.sidebar.displayImageFused.connect(self.addTab)
        self.hideButton.clicked.connect(self.hideButtonClicked)

        # 样式
        self.resize(1920, 1080)
        self.show()

    def addTab(self, uid: str, title: str, image: Union[MedicalImage, MedicalImage2]):
        if uid in self.tabs:
            self.tabWidget.setCurrentIndex(self.tabs.index(uid))
        else:
            if uid.endswith("2D"):
                viewer = ImageViewer()
                index = self.tabWidget.addTab(viewer, title)
                self.tabWidget.setCurrentIndex(index)
                # 重置图像大小
                viewer.setImage(image)
                viewer.view.reset()
            if uid.endswith("3D"):
                vtkViewer = VTKWidget()
                vtkViewer.addVolume(image)
                index = self.tabWidget.addTab(vtkViewer, title)
                self.tabWidget.setCurrentIndex(index)
            if uid.endswith("2DFused"):
                # 2D
                viewer = ImageViewer(bimodal=True)
                index = self.tabWidget.addTab(viewer, title)
                self.tabWidget.setCurrentIndex(index)
                # 重置图像大小
                viewer.setImage(image)
                viewer.view.reset()
            if uid.endswith("3DFused"):
                # 3D
                vtkViewer = VTKWidget()
                vtkViewer.addVolume(image)
                index = self.tabWidget.addTab(vtkViewer, title)
                self.tabWidget.setCurrentIndex(index)

            # 关闭按钮
            tabCloseButton = QToolButton()
            tabCloseButton.setIcon(QIcon("resource/close.png"))
            tabCloseButton.setStyleSheet("background-color:transparent")
            tabCloseButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            tabCloseButton.clicked.connect(lambda: self.removeTab(self.tabs.index(uid)))
            self.tabWidget.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, tabCloseButton)

            self.tabs.append(uid)

    def removeTab(self, index):
        self.tabWidget.removeTab(index)
        self.tabs.pop(index)

    def hideButtonClicked(self):
        layout: QHBoxLayout = self.centralWidget().layout()
        if self.sidebar.isVisible():
            self.sidebar.setVisible(False)
            self.hideButton.setArrowType(Qt.ArrowType.RightArrow)
            layout.setStretch(0, 0)
        else:
            self.sidebar.setVisible(True)
            self.hideButton.setArrowType(Qt.ArrowType.LeftArrow)
            layout.setStretch(0, 1)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec())

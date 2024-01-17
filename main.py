from typing import Union

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHBoxLayout, QMainWindow, QTabBar, QTabWidget, QToolButton, QWidget

from utility import MedicalImage, MedicalImage2
from widget import CollapsibleSidebar, ImageViewer, VolumeViewer


class Main(QMainWindow):
    def __init__(self) -> None:
        super(Main, self).__init__()
        self.tabs = []

        widget = QWidget(self)
        self.setCentralWidget(widget)
        layout = QHBoxLayout(widget)

        # 侧边栏
        self.sidebar = CollapsibleSidebar(self)
        layout.addWidget(self.sidebar, 1)

        # 侧边栏隐藏按钮
        self.hide_sidebar_button = QToolButton(self)
        self.hide_sidebar_button.setArrowType(Qt.ArrowType.LeftArrow)
        self.hide_sidebar_button.setFixedHeight(60)
        self.hide_sidebar_button.setFixedWidth(15)
        layout.addWidget(self.hide_sidebar_button)

        # 标签页
        self.tab_widget = QTabWidget(self)
        layout.addWidget(self.tab_widget, 4)

        # 信号与槽
        self.sidebar.image_displayed.connect(self.add_tab)
        self.sidebar.fusion_image_displayed.connect(self.add_tab)
        self.hide_sidebar_button.clicked.connect(self.hide_sidebar)

        # 样式
        self.resize(1920, 1080)
        self.show()

    def add_tab(self, uid: str, title: str, image: Union[MedicalImage, MedicalImage2]):
        if uid in self.tabs:
            self.tab_widget.setCurrentIndex(self.tabs.index(uid))
        else:
            if uid.endswith("2D"):
                viewer = ImageViewer(image)
                index = self.tab_widget.addTab(viewer, title)
                self.tab_widget.setCurrentIndex(index)
                # 重置图像大小
                viewer.view.reset()
            elif uid.endswith("2DFusion"):
                # 2D
                viewer = ImageViewer(image)
                index = self.tab_widget.addTab(viewer, title)
                self.tab_widget.setCurrentIndex(index)
                # 重置图像大小
                viewer.view.reset()
            elif uid.endswith("3D"):
                vtkViewer = VolumeViewer(image)
                index = self.tab_widget.addTab(vtkViewer, title)
                self.tab_widget.setCurrentIndex(index)
            elif uid.endswith("3DFusion"):
                # 3D
                vtkViewer = VolumeViewer(image)
                index = self.tab_widget.addTab(vtkViewer, title)
                self.tab_widget.setCurrentIndex(index)

            # 关闭按钮
            tabCloseButton = QToolButton()
            tabCloseButton.setIcon(QIcon("asset/icon/close.png"))
            tabCloseButton.setStyleSheet("background-color:transparent")
            tabCloseButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            tabCloseButton.clicked.connect(lambda: self.remove_tab(self.tabs.index(uid)))
            self.tab_widget.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, tabCloseButton)

            self.tabs.append(uid)

    def remove_tab(self, index):
        self.tabs.pop(index)
        self.tab_widget.removeTab(index)

    def hide_sidebar(self):
        layout: QHBoxLayout = self.centralWidget().layout()
        if self.sidebar.isVisible():
            self.sidebar.setVisible(False)
            self.hide_sidebar_button.setArrowType(Qt.ArrowType.RightArrow)
            layout.setStretch(0, 0)
        else:
            self.sidebar.setVisible(True)
            self.hide_sidebar_button.setArrowType(Qt.ArrowType.LeftArrow)
            layout.setStretch(0, 1)


if __name__ == "__main__":
    import argparse
    import sys

    from PyQt6.QtWidgets import QApplication

    from utility import read_nifti

    args = argparse.ArgumentParser("debug Widget.")
    args.add_argument(
        "--widget", type=str, default="main", choices=["main", "ImageViewer", "VolumeViewer", "CollapsibleSidebar"]
    )

    args = args.parse_args()
    if args.widget == "main":
        app = QApplication(sys.argv)
        main = Main()
        sys.exit(app.exec())
    elif args.widget == "CollapsibleSidebar":
        app = QApplication(sys.argv)
        MainWindow = CollapsibleSidebar()
        MainWindow.show()
        sys.exit(app.exec())
    elif args.widget == "ImageViewer":
        app = QApplication(sys.argv)
        image = read_nifti(r"DATA\001_CT.nii.gz", True)
        MainWindow = ImageViewer(image)
        MainWindow.show()
        MainWindow.view.reset()
        sys.exit(app.exec())
    elif args.widget == "VolumeViewer":
        app = QApplication(sys.argv)
        ct = read_nifti(r"DATA\001_CT.nii.gz", True)
        pt = read_nifti(r"DATA\001_SUVbw.nii.gz", True)
        image = MedicalImage2.from_ct_pt(ct, pt)
        widget = VolumeViewer(image)
        sys.exit(app.exec())
    else:
        print("end.")

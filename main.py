from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QHBoxLayout,
    QMainWindow,
    QTabBar,
    QTabWidget,
    QToolButton,
    QWidget,
)

from widget.ImageViewer import ImageViewer
from widget.Sidebar import Sidebar


class Main(QMainWindow):
    def __init__(self) -> None:
        super(Main, self).__init__()
        self.tabs = []

        widget = QWidget(self)
        self.setCentralWidget(widget)

        layout = QHBoxLayout(widget)

        self.sidebar = Sidebar(self)
        layout.addWidget(self.sidebar, 1)
        self.tabWidget = QTabWidget(self)
        layout.addWidget(self.tabWidget, 4)

        self.resize(1920, 1080)
        self.show()

        # 设置属性
        self.tabWidget.setStyleSheet("background-color:black;background:transparent;")
        self.tabWidget.setTabsClosable(True)

        # 信号与槽
        self.sidebar.displayImage2D.connect(self.addTab)

    def addTab(self, uid, title, image):
        if uid in self.tabs:
            self.tabWidget.setCurrentIndex(self.tabs.index(uid))
        else:
            viewer = ImageViewer()
            index = self.tabWidget.addTab(viewer, title)
            self.tabWidget.setCurrentIndex(index)

            # 创建关闭按钮
            tabCloseButton = QToolButton()
            tabCloseButton.setIcon(QIcon("resource/close.png"))
            tabCloseButton.setStyleSheet("background-color:transparent")
            tabCloseButton.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
            tabCloseButton.clicked.connect(lambda: self.removeTab(self.tabs.index(uid)))
            self.tabWidget.tabBar().setTabButton(index, QTabBar.ButtonPosition.RightSide, tabCloseButton)

            # 重置图像大小
            viewer.setImage(image)
            viewer.view.reset()
            self.tabs.append(uid)

    def removeTab(self, index):
        self.tabWidget.removeTab(index)
        self.tabs.pop(index)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec())

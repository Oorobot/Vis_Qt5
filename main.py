from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QTabWidget, QWidget

from widget.ImageViewer import ImageViewer
from widget.Sidebar import Sidebar


class Main(QMainWindow):
    def __init__(self) -> None:
        super(Main, self).__init__()

        widget = QWidget(self)

        mainLayout = QHBoxLayout(self)

        self.sidebar = Sidebar(self)
        mainLayout.addWidget(self.sidebar, 1)

        self.tabs = QTabWidget(self)
        mainLayout.addWidget(self.tabs, 4)

        widget.setLayout(mainLayout)

        self.setCentralWidget(widget)

        self.resize(1920, 1080)

        self.show()

    def add_tab(self, title, image):
        self.tabs.addTab()


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    main = Main()
    sys.exit(app.exec())

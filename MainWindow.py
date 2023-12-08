import typing

from PyQt6 import QtCore, QtGui
from PyQt6.QtWidgets import QApplication, QGridLayout, QHBoxLayout, QTabWidget, QWidget

from widget.CollapsibleWidget import Sidebar


class customedWidget(QWidget):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        mainLayout = QHBoxLayout(self)

        self.sidebar = Sidebar(self)
        mainLayout.addWidget(self.sidebar)
        self.tabs = QTabWidget(self)
        mainLayout.addWidget(self.tabs)

        self.setLayout(mainLayout)

        self.resize(1920, 1080)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    MainWindow = customedWidget()
    MainWindow.show()
    sys.exit(app.exec())

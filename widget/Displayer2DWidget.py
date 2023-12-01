import numpy as np
from PyQt6 import QtGui
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPixmap
from PyQt6.QtWidgets import QApplication, QFileDialog, QWidget

from entity import ReadImage, ReadNIFTI
from ui.Ui_Displayer2D import Ui_Displayer2D
from widget.GraphicsView import ImageItem


class Displayer2DWidget(QWidget, Ui_Displayer2D):
    def __init__(self, view: str = "t"):
        super().__init__()
        self.setupUi(self)

        self.imageDisplay.setView(view)
        self.initWidgets()

    def initWidgets(self):
        self.fitButton.clicked.connect(self.openFile)
        self.imageScroll.valueChanged.connect(self.imageScrollFunction)
        self.imageScroll.setEnabled(False)

    def openFile(self):
        filename = QFileDialog().getOpenFileName(self, "选择文件", "./", filter="图像文件(*.nii *.nii.gz)")
        if len(filename[0]) == 0:
            return

        image = ReadNIFTI(filename[0], True)
        self.imageDisplay.setImage(image)

        self.imageScroll.setEnabled(True)
        self.imageScroll.setSingleStep(1)
        self.imageScroll.setRange(1, image.size[self.imageDisplay._view])
        self.sliceCurrent.setText(str(image.position[self.imageDisplay._view]))
        self.sliceTotal.setText(str(image.size[self.imageDisplay._view]))

    def imageScrollFunction(self, value):
        self.sliceCurrent.setText(str(value))
        self.imageDisplay.changeSliceOfImage(value)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    MainWindow = Displayer2DWidget()
    MainWindow.show()
    sys.exit(app.exec())

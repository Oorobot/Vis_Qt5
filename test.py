from ui.Ui_Displayer2D import Ui_Displayer2D
from utils.image import Image
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import QImage, QPixmap
import numpy as np


class win(QWidget, Ui_Displayer2D):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.image = None

        self.zoomBtn.clicked.connect(self.openFile)
        self.imageDisplay.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.imageDisplay.dragMoveEvent()

    def openFile(self):
        filename = QFileDialog().getOpenFileName(
            self, '选择文件', './', filter='图像文件(*.nii *.nii.gz)'
        )
        if len(filename[0]) == 0:
            return

        self.image = Image(filename=filename[0])

        self.imageDisplay.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)

        array: np.ndarray = self.image.sagittal_plane()
        qImage = QImage(
            array.data.tobytes(),
            array.shape[1],
            array.shape[0],
            array.shape[1] * self.image.channel,
            QImage.Format.Format_Grayscale8
            if self.image.channel == 1
            else QImage.Format.Format_RGB888,
        )

        qPixmap = QPixmap.fromImage(qImage)

        self.qScene = QGraphicsScene(self.imageDisplay)
        self.qScene.addPixmap(qPixmap)
        self.imageDisplay.setScene(self.qScene)


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    MainWindow = win()
    MainWindow.show()
    sys.exit(app.exec())

import numpy as np
from PyQt6.QtGui import QColor, QImage, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGraphicsScene,
    QGraphicsView,
    QWidget,
)

from ui.Ui_Displayer2D import Ui_Displayer2D
from utils.image import Image
from widget.ImageWidget import ImageWidget


class win(QWidget, Ui_Displayer2D):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.image = None

        self.initView()
        self.initWidgets()

    def initView(self):
        self.pixmap: QPixmap = None
        self.imageWidget: ImageWidget = None
        self.scene = QGraphicsScene()
        self.imageDisplay.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.imageDisplay.setCacheMode(QGraphicsView.CacheModeFlag.CacheBackground)

        self.background_color = QColor()
        self.background_color.setNamedColor("#FFFFFF")
        self.imageDisplay.setScene(self.scene)
        self.imageDisplay.setSceneRect(
            -self.imageDisplay.width() // 2,
            -self.imageDisplay.height() // 2,
            self.imageDisplay.width(),
            self.imageDisplay.height(),
        )

    def initWidgets(self):
        self.fitButton.clicked.connect(self.openFile)
        self.imageScroll.valueChanged.connect(self.imageScrollFunction)
        self.imageScroll.setEnabled(False)

    def showImage(self, array: np.ndarray, view_width: int, view_height: int):
        self.scene.clear()
        q_image = QImage(
            array.data.tobytes(),
            array.shape[1],
            array.shape[0],
            array.shape[1] * self.image.channel,
            QImage.Format.Format_Grayscale8
            if self.image.channel == 1
            else QImage.Format.Format_RGB888,
        )
        self.pixmap = QPixmap.fromImage(q_image)
        self.imageWidget = ImageWidget(self.pixmap)
        self.imageWidget.setQGraphicsViewWH(view_width, view_height)
        self.scene.addItem(self.imageWidget)

    def openFile(self):
        filename = QFileDialog().getOpenFileName(
            self, "选择文件", "./", filter="图像文件(*.nii *.nii.gz)"
        )
        if len(filename[0]) == 0:
            return

        self.image = Image(filename=filename[0])
        self.imageScroll.setSingleStep(1)
        self.imageScroll.setRange(1, self.image.size["s"])
        self.imageScroll.setEnabled(True)
        self.sliceCurrent.setText(str(self.image.position["s"]))
        self.sliceTotal.setText(str(self.image.size["s"]))

        self.showImage(
            self.image.plane_s(), self.imageDisplay.width(), self.imageDisplay.height()
        )

    def imageScrollFunction(self, value):
        if self.image is not None:
            self.sliceCurrent.setText(str(value))
            self.image.position["s"] = value
            self.showImage(
                self.image.plane_s(),
                self.imageDisplay.width(),
                self.imageDisplay.height(),
            )


if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)
    MainWindow = win()
    MainWindow.show()
    sys.exit(app.exec())

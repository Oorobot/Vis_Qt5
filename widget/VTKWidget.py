from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget
from vtkmodules.qt import QVTKRenderWindowInteractor


class VTKWidget(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)

        self.vtk = QVTKRenderWindowInteractor()

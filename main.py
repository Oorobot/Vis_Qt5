# Form implementation generated from reading ui file 'main.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6 import QtOpenGLWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(800, 600)
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap("images/icon.png"),
            QtGui.QIcon.Mode.Normal,
            QtGui.QIcon.State.Off,
        )
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.widget = QtWidgets.QWidget(parent=self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(11, 11, 781, 541))
        self.widget.setObjectName("widget")
        self.gridLayout = QtWidgets.QGridLayout(self.widget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.coronalView = QtWidgets.QGraphicsView(parent=self.widget)
        self.coronalView.setObjectName("coronalView")
        self.verticalLayout.addWidget(self.coronalView)
        self.coronalLabel = QtWidgets.QLabel(parent=self.widget)
        self.coronalLabel.setText("")
        self.coronalLabel.setScaledContents(False)
        self.coronalLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.coronalLabel.setObjectName("coronalLabel")
        self.verticalLayout.addWidget(self.coronalLabel)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.transverseView = QtWidgets.QGraphicsView(parent=self.widget)
        self.transverseView.setObjectName("transverseView")
        self.verticalLayout_2.addWidget(self.transverseView)
        self.transverseLabel = QtWidgets.QLabel(parent=self.widget)
        self.transverseLabel.setText("")
        self.transverseLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.transverseLabel.setObjectName("transverseLabel")
        self.verticalLayout_2.addWidget(self.transverseLabel)
        self.gridLayout.addLayout(self.verticalLayout_2, 0, 1, 1, 1)
        self.openGL3DView = QtOpenGLWidgets.QOpenGLWidget(parent=self.widget)
        self.openGL3DView.setMinimumSize(QtCore.QSize(258, 216))
        self.openGL3DView.setMaximumSize(QtCore.QSize(16777215, 216))
        self.openGL3DView.setObjectName("openGL3DView")
        self.gridLayout.addWidget(self.openGL3DView, 1, 0, 1, 1)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.sagittalView = QtWidgets.QGraphicsView(parent=self.widget)
        self.sagittalView.setObjectName("sagittalView")
        self.verticalLayout_3.addWidget(self.sagittalView)
        self.sagittalLabel = QtWidgets.QLabel(parent=self.widget)
        self.sagittalLabel.setText("")
        self.sagittalLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.sagittalLabel.setObjectName("sagittalLabel")
        self.verticalLayout_3.addWidget(self.sagittalLabel)
        self.gridLayout.addLayout(self.verticalLayout_3, 1, 1, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        self.file = QtWidgets.QMenu(parent=self.menubar)
        self.file.setObjectName("file")
        self.about = QtWidgets.QMenu(parent=self.menubar)
        self.about.setObjectName("about")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.open = QtGui.QAction(parent=MainWindow)
        self.open.setObjectName("open")
        self.file.addAction(self.open)
        self.menubar.addAction(self.file.menuAction())
        self.menubar.addAction(self.about.menuAction())

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "医学影像工具"))
        self.file.setTitle(_translate("MainWindow", "文件"))
        self.about.setTitle(_translate("MainWindow", "关于"))
        self.open.setText(_translate("MainWindow", "打开"))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec())

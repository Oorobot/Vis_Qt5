from typing import Union

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QFont, QIcon, QIntValidator
from PyQt6.QtWidgets import (
    QFileDialog,
    QGraphicsView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QSlider,
    QToolBar,
    QToolButton,
    QWidget,
)

from utility import VIEW_TO_NAME, MedicalImage, MedicalImage2, read_nifti
from widget import ImageConstrast, ImageView

from .image_constrast import ImageConstrast
from .image_view import ImageView


class ImageViewer(QMainWindow):
    def __init__(self, image: Union[MedicalImage, MedicalImage2], parent: QWidget = None) -> None:
        super().__init__(parent)
        bimodal = isinstance(image, MedicalImage2)

        self.resize(1920, 1080)
        self.setStyleSheet(
            "QToolButton::menu-indicator {image: none;}"
            "QToolBar {border: none;}"
            "QLabel {background-color: transparent;}"
            "QLineEdit {background-color: transparent; border: none;}"
        )

        self.view = ImageView("t", self)
        self.setCentralWidget(self.view)
        self.view.set_image(image)

        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setFloatable(False)

        # 视图和位置信息
        self.view_name = QLabel()
        self.view_name.setFixedWidth(80)
        self.view_name.setText(VIEW_TO_NAME["t"])
        self.view_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view_name.setStyleSheet("color: #12074D")
        self.view_name.setFont(QFont("楷体", 12))
        self.position_max = QLabel()
        self.position_max.setText(str(0))
        self.position_max.setFixedWidth(35)
        self.position_max.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_max.setStyleSheet("color: #07255C")
        self.position_max.setFont(QFont("Times New Roman", 12))
        self.position_current = QLineEdit()
        self.position_current.setText("0")
        self.position_current.setFixedWidth(35)
        self.position_current.setValidator(QIntValidator())
        self.position_current.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.position_current.setFont(QFont("Times New Roman", 12))
        self.position_current.setStyleSheet("color: #135170")
        toolbar.addWidget(self.view_name)
        toolbar.addWidget(self.position_max)
        toolbar.addWidget(self.position_current)
        toolbar.addSeparator()
        # 设置默认值
        self.position_current.setText(str(self.view.position))
        self.position_max.setText(str(self.view.position_max))

        # 三视图
        view_button = QToolButton()
        view_button.setText("视图")
        view_button.setIcon(QIcon("asset/icon/view.png"))
        view_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        view_button.setAutoRaise(False)
        view_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        view_button.setArrowType(Qt.ArrowType.NoArrow)
        view_menu = QMenu()
        view_sagittal = view_menu.addAction(QIcon("asset/icon/S.png"), "矢状面")
        view_coronal = view_menu.addAction(QIcon("asset/icon/C.png"), "冠状面")
        view_transverse = view_menu.addAction(QIcon("asset/icon/T.png"), "横截面")
        view_button.setMenu(view_menu)
        toolbar.addWidget(view_button)

        # 操作：重置、翻转
        operate_button = QToolButton()
        operate_button.setText("操作")
        operate_button.setIcon(QIcon("asset/icon/operate.png"))
        operate_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        operate_button.setAutoRaise(True)
        operate_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        operate_menu = QMenu()
        operate_reset = operate_menu.addAction(QIcon("asset/icon/reset.png"), "重置")
        operate_menu.addSeparator()
        operate_mirror1 = operate_menu.addAction(QIcon("asset/icon/mirror1.png"), "水平镜像")
        operate_mirror2 = operate_menu.addAction(QIcon("asset/icon/mirror2.png"), "垂直镜像")
        operate_menu.addSeparator()
        operate_rotate1 = operate_menu.addAction(QIcon("asset/icon/rotate1.png"), "顺时针旋转")
        operate_rotate2 = operate_menu.addAction(QIcon("asset/icon/rotate2.png"), "逆时针旋转")
        operate_button.setMenu(operate_menu)
        toolbar.addWidget(operate_button)

        # 鼠标左键
        self.mouse_left_button = QToolButton()
        self.mouse_left_button.setText("普通")
        self.mouse_left_button.setIcon(QIcon("asset/icon/arrow.png"))
        self.mouse_left_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.mouse_left_button.setAutoRaise(True)
        self.mouse_left_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        mouse_left_menu = QMenu()
        mouse_left_normal = mouse_left_menu.addAction(QIcon("asset/icon/arrow.png"), "普通")
        mouse_left_drag = mouse_left_menu.addAction(QIcon("asset/icon/drag.png"), "拖动")
        self.mouse_left_button.setMenu(mouse_left_menu)
        toolbar.addWidget(self.mouse_left_button)

        # 鼠标滑轮
        self.wheel_button = QToolButton()
        self.wheel_button.setText("切换")
        self.wheel_button.setIcon(QIcon("asset/icon/slide.png"))
        self.wheel_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.wheel_button.setAutoRaise(True)
        self.wheel_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        wheel_menu = QMenu()
        wheel_slide = wheel_menu.addAction(QIcon("asset/icon/slide.png"), "切换")
        wheel_resize = wheel_menu.addAction(QIcon("asset/icon/resize.png"), "缩放")
        self.wheel_button.setMenu(wheel_menu)
        toolbar.addWidget(self.wheel_button)
        toolbar.addSeparator()

        # 对比度
        constrast_button = QToolButton()
        constrast_button.setText("对比度")
        constrast_button.setIcon(QIcon("asset/icon/constrast.png"))
        constrast_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.constrast_window = ImageConstrast()
        toolbar.addWidget(constrast_button)
        # 设置默认值
        mi, ma = image.array.min(), image.array.max()
        self.constrast_window.edit_min.setText(f"{mi:.2f}")
        self.constrast_window.edit_max.setText(f"{ma:.2f}")
        self.constrast_window.edit_window_level.setText(f"{(mi + ma) / 2:.2f}")
        self.constrast_window.edit_window_width.setText(f"{ma- mi:.2f}")

        if bimodal:
            self.constrast_slider = QSlider(Qt.Orientation.Horizontal)
            self.constrast_slider.setValue(25)
            self.constrast_slider.setRange(0, 50)
            self.constrast_slider.setSingleStep(1)
            self.constrast_slider.setMinimumWidth(50)
            self.constrast_slider.setMaximumWidth(100)
            self.constrast_max = QLineEdit()
            self.constrast_max.setValidator(QDoubleValidator())
            self.constrast_max.setText("5.0")
            self.constrast_max.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.constrast_max.setFixedWidth(30)
            self.constrast_max.setFont(QFont("Times New Roman", 12))
            toolbar.addWidget(self.constrast_slider)
            toolbar.addWidget(self.constrast_max)
            toolbar.addSeparator()

            # 归一化
            self.view.image.normlize_pt(float(self.constrast_max.text()) * 0.1)

            # 信号与槽
            self.constrast_slider.sliderReleased.connect(self.adjust_constrast2)
            self.constrast_max.textEdited.connect(self.validate_constrast_max2)
            self.constrast_max.editingFinished.connect(self.adjust_constrast_max2)

        # 标签、透明度
        label_button = QToolButton()
        label_button.setText("标签")
        label_button.setIcon(QIcon("asset/icon/label.png"))
        label_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        label_slider = QSlider(Qt.Orientation.Horizontal)
        label_slider.setRange(0, 100)
        label_slider.setValue(50)
        label_slider.setSingleStep(1)
        label_slider.setMinimumWidth(50)
        label_slider.setMaximumWidth(100)
        toolbar.addWidget(label_button)
        toolbar.addWidget(label_slider)
        toolbar.addSeparator()

        self.addToolBar(toolbar)

        # 信号与槽
        view_sagittal.triggered.connect(lambda: self.set_view("s"))
        view_coronal.triggered.connect(lambda: self.set_view("c"))
        view_transverse.triggered.connect(lambda: self.set_view("t"))

        operate_reset.triggered.connect(self.view.reset)
        operate_mirror1.triggered.connect(self.view.mirror1)
        operate_mirror2.triggered.connect(self.view.mirror2)
        operate_rotate1.triggered.connect(self.view.rotate1)
        operate_rotate2.triggered.connect(self.view.rotate2)

        mouse_left_normal.triggered.connect(self.activate_normal_mode)
        mouse_left_drag.triggered.connect(self.activate_drag_mode)

        wheel_resize.triggered.connect(self.activate_resize_mode)
        wheel_slide.triggered.connect(self.activate_slide_mode)

        constrast_button.clicked.connect(self.open_constrast_window)

        label_button.clicked.connect(self.open_label)
        label_slider.valueChanged.connect(self.adjust_label_opacity)

        self.view.position_changed.connect(self.set_position)
        self.position_current.editingFinished.connect(self.set_current_plane)
        self.position_current.textEdited.connect(self.validate_position)

    # 普通
    def activate_normal_mode(self):
        self.mouse_left_button.setText("普通")
        self.mouse_left_button.setIcon(QIcon("asset/icon/arrow.png"))
        self.view.setDragMode(QGraphicsView.DragMode.NoDrag)

    # 拖动
    def activate_drag_mode(self):
        self.mouse_left_button.setText("拖动")
        self.mouse_left_button.setIcon(QIcon("asset/icon/drag.png"))
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)

    # 缩放
    def activate_resize_mode(self):
        self.wheel_button.setText("缩放")
        self.wheel_button.setIcon(QIcon("asset/icon/resize.png"))
        self.view.resize_or_slide = True

    # 切换
    def activate_slide_mode(self):
        self.wheel_button.setText("切换")
        self.wheel_button.setIcon(QIcon("asset/icon/slide.png"))
        self.view.resize_or_slide = False

    # 对比度
    def open_constrast_window(self):
        self.constrast_window.show()
        self.constrast_window.changed.connect(self.adjust_constrast)

    # 调整对比度
    def adjust_constrast(self, mi, ma):
        if self.view.image is not None:
            self.view.image.normlize(mi, ma)
            self.view.set_current_plane()

    def adjust_constrast2(self):
        if self.view.image is not None:
            self.view.image.normlize_pt(self.constrast_slider.value() * 0.1)
            self.view.set_current_plane()

    def validate_constrast_max2(self, t: str):
        if t == "" or float(t) <= 0:
            self.constrast_max.setText("5.0")
        else:
            return

    def adjust_constrast_max2(self):
        ma = float(self.constrast_max.text())
        self.constrast_max.setText(f"{ma:.1f}")
        ma = float(self.constrast_max.text())
        self.constrast_slider.setMaximum(int(ma * 10))

    # 打开分割图
    def open_label(self):
        filename = QFileDialog().getOpenFileName(self, "选择文件", "./", filter="NIFTI(*.nii *.nii.gz);;")
        if len(filename[0]) == 0:
            return

        labelImage = read_nifti(filename[0], True)
        self.view.set_label(labelImage)

    # 调整分割图透明度
    def adjust_label_opacity(self, v: int):
        self.view.set_label_opacity(v * 0.01)

    def set_view(self, v: str):
        self.view.set_view(v)
        self.view_name.setText(VIEW_TO_NAME[v])
        self.position_current.setText(str(self.view.position))
        self.position_max.setText(str(self.view.position_max))

    def set_position(self, p: int):
        self.position_current.setText(str(p))

    def set_current_plane(self):
        self.view.position = int(self.position_current.text())
        self.view.set_current_plane()

    def validate_position(self, t: str):
        if t == "" or int(t) < 1:
            self.position_current.setText("1")
        elif int(t) > self.view.position_max:
            self.position_current.setText(str(self.view.position_max))
        else:
            return

import enum
from typing import Union

import numpy as np
import pydicom
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator, QFont, QIcon, QIntValidator
from PyQt6.QtWidgets import (
    QFileDialog,
    QGraphicsView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSlider,
    QToolBar,
    QToolButton,
    QWidget,
)

from utility import VIEW_TO_NAME, MedicalImage, MedicalImage2, read_nifti
from worker import FRIWorker, PJIWorker

from .image_constrast import ImageConstrast
from .image_view import ImageView
from .message_box import TimerMessageBox, information
from .note import Note


class ImageViewer(QMainWindow):
    class ToolbarMode(enum.Enum):
        Gray = 0
        RGB = 1
        Bimodal = 2

    def __init__(self, image: Union[MedicalImage, MedicalImage2], parent: QWidget = None) -> None:
        super().__init__(parent)
        if image.channel == 1:
            self.toolbar_mode = self.ToolbarMode.Gray
            if isinstance(image, MedicalImage2):
                self.toolbar_mode = self.ToolbarMode.Bimodal
        else:
            self.toolbar_mode = self.ToolbarMode.RGB

        self.resize(1920, 1080)
        self.setStyleSheet(
            "QToolButton::menu-indicator {image: none;}"
            "QToolBar {border: none;}"
            "QLabel {background-color: transparent; color: #00bfff;}"
            "QLineEdit {background-color: transparent; border: none; color: #dc7e23}"
            "QWidget {border: 1px;}"
        )

        self.view = ImageView("t", image, self)
        self.setCentralWidget(self.view)
        self.view.PJI_box_selected.connect(self.get_pji_box)

        self.toolbar = QToolBar()
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)

        # 视图和位置信息
        self.view_name = QLabel(VIEW_TO_NAME["t"])
        self.view_name.setFixedWidth(80)
        self.view_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.view_name.setFont(QFont("黑体", 16))
        self.position = {
            "s": Note(
                str(self.view._position["s"]),
                "S = {0}".format(self.view._position_max["s"]),
                True,
                QIntValidator(1, self.view._position_max["s"]),
            ),
            "c": Note(
                str(self.view._position["c"]),
                "C = {0}".format(self.view._position_max["c"]),
                True,
                QIntValidator(1, self.view._position_max["c"]),
            ),
            "t": Note(
                str(self.view._position["t"]),
                "T = {0}".format(self.view._position_max["t"]),
                True,
                QIntValidator(1, self.view._position_max["t"]),
            ),
        }
        self.toolbar.addWidget(self.view_name)
        self.toolbar.addWidget(self.position["s"])
        self.toolbar.addWidget(self.position["c"])
        self.toolbar.addWidget(self.position["t"])

        # Gray
        if self.toolbar_mode == self.ToolbarMode.Gray:
            self.pixel_value = Note(
                f"{self.view.image_value:.2f}",
                (
                    "HU"
                    if image.modality == "CT" or image.modality == "PTCT"
                    else "SUVbw" if image.modality == "PT" else "value"
                ),
            )
            self.toolbar.addWidget(self.pixel_value)
        # RGB
        elif self.toolbar_mode == self.ToolbarMode.RGB:
            self.pixel_value1 = Note(f"{self.view.image_value[0]}", "R")
            self.pixel_value2 = Note(f"{self.view.image_value[1]}", "G")
            self.pixel_value3 = Note(f"{self.view.image_value[2]}", "B")
            self.toolbar.addWidget(self.pixel_value1)
            self.toolbar.addWidget(self.pixel_value2)
            self.toolbar.addWidget(self.pixel_value3)
        else:
            self.pixel_value1 = Note(f"{self.view.image_value:.2f}", "HU")
            self.pixel_value2 = Note(f"{self.view.image_value_pt:.2f}", "SUVbw")
            self.toolbar.addWidget(self.pixel_value1)
            self.toolbar.addWidget(self.pixel_value2)
        self.toolbar.addSeparator()

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
        self.toolbar.addWidget(view_button)

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
        self.toolbar.addWidget(operate_button)

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
        self.toolbar.addWidget(self.mouse_left_button)

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
        self.toolbar.addWidget(self.wheel_button)
        self.toolbar.addSeparator()

        # 对比度
        constrast_button = QToolButton()
        constrast_button.setText("对比度")
        constrast_button.setIcon(QIcon("asset/icon/constrast.png"))
        constrast_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
        self.constrast_window = ImageConstrast()
        self.toolbar.addWidget(constrast_button)
        # 设置默认值
        mi, ma = image.array.min(), image.array.max()
        self.constrast_window.edit_min.setText(f"{mi:.2f}")
        self.constrast_window.edit_max.setText(f"{ma:.2f}")
        self.constrast_window.edit_window_level.setText(f"{(mi + ma) / 2:.2f}")
        self.constrast_window.edit_window_width.setText(f"{ma- mi:.2f}")

        if self.toolbar_mode == self.ToolbarMode.Bimodal:
            self.constrast_slider = QSlider(Qt.Orientation.Horizontal)
            self.constrast_slider.setValue(50)
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
            self.toolbar.addWidget(self.constrast_slider)
            self.toolbar.addWidget(self.constrast_max)
            self.toolbar.addSeparator()

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
        self.toolbar.addWidget(label_button)
        self.toolbar.addWidget(label_slider)
        self.toolbar.addSeparator()

        # AI
        self.ai_button = QToolButton()
        self.ai_button.setText("AI")
        self.ai_button.setIcon(QIcon("asset/icon/ai.png"))
        self.ai_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.toolbar.addWidget(self.ai_button)
        self.timer_message_box = TimerMessageBox(QMessageBox.Icon.Information, "正在处理中...")

        self.addToolBar(self.toolbar)

        # 信号与槽
        self.position["s"].value_changed.connect(lambda: self.edit_position("s"))
        self.position["c"].value_changed.connect(lambda: self.edit_position("c"))
        self.position["t"].value_changed.connect(lambda: self.edit_position("t"))

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

        constrast_button.clicked.connect(self.constrast_window.exec)
        self.constrast_window.changed.connect(self.adjust_constrast)

        label_button.clicked.connect(self.open_label)
        label_slider.valueChanged.connect(self.adjust_label_opacity)

        self.view.position_changed.connect(self.set_position)

        self.ai_button.clicked.connect(self.inference)

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

    def set_position(self, s: int, c: int, t: int):
        self.position["s"].set_value(str(s))
        self.position["c"].set_value(str(c))
        self.position["t"].set_value(str(t))
        if self.toolbar_mode == self.ToolbarMode.Gray:
            self.pixel_value.set_value(f"{self.view.image_value:.2f}")
        elif self.toolbar_mode == self.ToolbarMode.RGB:
            self.pixel_value1.set_value(f"{self.view.image_value[0]}")
            self.pixel_value2.set_value(f"{self.view.image_value[1]}")
            self.pixel_value3.set_value(f"{self.view.image_value[2]}")
        else:
            self.pixel_value1.set_value(f"{self.view.image_value:.2f}")
            self.pixel_value2.set_value(f"{self.view.image_value_pt:.2f}")
        self.view.set_current_plane()

    def edit_position(self, v: str):
        self.view._position[v] = int(self.position[v].text)
        if self.toolbar_mode == self.ToolbarMode.Gray:
            self.pixel_value.set_value(f"{self.view.image_value:.2f}")
        elif self.toolbar_mode == self.ToolbarMode.RGB:
            self.pixel_value1.set_value(f"{self.view.image_value[0]}")
            self.pixel_value2.set_value(f"{self.view.image_value[1]}")
            self.pixel_value3.set_value(f"{self.view.image_value[2]}")
        else:
            self.pixel_value1.set_value(f"{self.view.image_value:.2f}")
            self.pixel_value2.set_value(f"{self.view.image_value_pt:.2f}")
        self.view.set_current_plane()
        self.view.scene_pos = self.view.position_to_scene_pos()
        self.view.scene().update()

    def inference(self):
        # TODO: 整合入模型
        if isinstance(self.view.image, MedicalImage) and self.view.image.modality == "NM":
            _dcm = pydicom.dcmread(self.view.image.files[0])
            if _dcm.StudyDescription == "Three Phase Bone" and _dcm.SeriesDescription == "FLOW":
                # 选择膝部或者髋部
                selection = QMessageBox()
                selection.setIcon(QMessageBox.Icon.Question)
                selection.setWindowTitle("请选择")
                selection.setText("膝部或者髋部")
                selection.addButton("膝部", QMessageBox.ButtonRole.YesRole)
                selection.addButton("髋部", QMessageBox.ButtonRole.NoRole)
                selection.exec()
                # 膝部
                if selection.clickedButton().text() == "膝部":
                    self.woker = PJIWorker(self.view.image, "knee")
                    self.woker.finished.connect(self.get_pji_result)
                    self.woker.start()
                    self.timer_message_box.exec()
                    return
                # 髋部
                else:
                    self.view.PJI_mode = True
                    self.toolbar.setDisabled(True)
                    self.set_view("t")
                    information(
                        "请选择感兴趣区域：\n鼠标左键点击将显示红框，\n鼠标移动，红框跟随，\n鼠标松开，红框所在区域即为感兴趣区域。"
                    )
                    return
            else:
                information("AI功能不支持当前影像。")
                return
        elif isinstance(self.view.image, MedicalImage2) and self.view.image.modality == "PTCT":
            self.woker = FRIWorker(self.view.image)
            self.woker.finished.connect(self.get_fri_result)
            self.woker.start()
            self.timer_message_box.exec()
            return
        else:
            information("AI功能不支持当前影像。")
            return

    def get_pji_box(self, left, top):
        print(f"[INFO] PJI ROI: ({left}, {top}), ({left+40}, {top+40})")
        #
        self.view.PJI_mode = False
        self.view.PJI_box = None
        self.toolbar.setDisabled(False)
        #
        roi_array = np.zeros_like(self.view.image.array)
        roi_array[:, top : top + 40, left : left + 40] = 1
        roi_image = MedicalImage(
            roi_array,
            self.view.image.size,
            self.view.image.origin,
            self.view.image.spacing,
            self.view.image.direction,
            "OT",
            1,
        )
        self.view.set_label(roi_image)
        #
        direction = "left" if left + 19 <= 64 else "right"
        self.woker = PJIWorker(self.view.image[0:25, top : top + 40, left : left + 40], "hip", direction)
        self.woker.finished.connect(self.get_pji_result)
        self.woker.start()
        self.timer_message_box.exec()

    def get_pji_result(self, result):
        print(f"[INFO] PJI result: {result}")
        self.ai_button.setText(result)
        self.timer_message_box.accept()
        information(f"[INFO] PJI 的诊断结果为 {result}.")

    def get_fri_result(self, result):
        print(f"[INFO] FRI result: {result}")
        self.timer_message_box.accept()
        information(f"[INFO] FRI 的检测诊断结果为 {result}.")

        # 解析结果
        classes, labels = [], []
        for label in result:
            classes.append(label["class_name"])
            labels.append(label["bbox"])
        unique_classes = list(set(classes))

        #
        result_array = np.zeros_like(self.view.image.array)
        for c, l in zip(classes, labels):
            result_array[l[2] : l[5], l[1] : l[4], l[0] : l[3]] = unique_classes.index(c)
        result_image = MedicalImage(
            result_array,
            self.view.image.size,
            self.view.image.origin,
            self.view.image.spacing,
            self.view.image.direction,
            "OT",
            1,
        )
        self.view.set_label(result_image)

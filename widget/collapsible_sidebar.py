from typing import Dict, List

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileDialog, QGridLayout, QScrollArea, QToolButton, QVBoxLayout, QWidget

from utility import MedicalImage, MedicalImage2, read_image

from .collapsible_widget import CollapsibleWidget
from .message_box import information


class CollapsibleSidebar(QWidget):
    image_displayed = pyqtSignal(str, str, MedicalImage)
    fusion_image_displayed = pyqtSignal(str, str, MedicalImage2)

    def __init__(self, parent: QWidget = None) -> None:
        # 初始化
        super().__init__(parent)
        self.toggled_children: List[str] = []
        self.collapsible_widgets: Dict[str, CollapsibleWidget] = {}

        # 样式
        self.setStyleSheet(
            "QToolButton {background-color:transparent;}"
            "QToolButton::hover {background-color:rgba(71,141,141,0.4);}"
            "QToolButton::pressed {background-color:rgba(174,238,238,0.4);}"
            "QScrollArea {background-color:transparent; border: none;}"
        )
        self.setMinimumWidth(150)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # 主按钮
        open_button = QToolButton(self)
        open_button.setIcon(QIcon("asset/icon/open.png"))
        open_button.setIconSize(QSize(30, 30))
        open_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        open_button.setToolTip("打开文件")
        open_button.setToolTipDuration(5000)

        delete_button = QToolButton(self)
        delete_button.setIcon(QIcon("asset/icon/delete.png"))
        delete_button.setIconSize(QSize(30, 30))
        delete_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        delete_button.setToolTip("打开文件")
        delete_button.setToolTipDuration(5000)

        display_2d_button = QToolButton(self)
        display_2d_button.setIcon(QIcon("asset/icon/display2D.png"))
        display_2d_button.setIconSize(QSize(30, 30))
        display_2d_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        display_2d_button.setToolTip("二维浏览")
        display_2d_button.setToolTipDuration(5000)

        display_3d_button = QToolButton(self)
        display_3d_button.setIcon(QIcon("asset/icon/display3D.png"))
        display_3d_button.setIconSize(QSize(30, 30))
        display_3d_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        display_3d_button.setToolTip("三维浏览")
        display_3d_button.setToolTipDuration(5000)

        display_fusion_2d_button = QToolButton(self)
        display_fusion_2d_button.setIcon(QIcon("asset/icon/displayFusion2D.png"))
        display_fusion_2d_button.setIconSize(QSize(30, 30))
        display_fusion_2d_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        display_fusion_2d_button.setToolTip("二维融合")
        display_fusion_2d_button.setToolTipDuration(5000)

        display_fusion_3d_button = QToolButton(self)
        display_fusion_3d_button.setIcon(QIcon("asset/icon/displayFusion3D.png"))
        display_fusion_3d_button.setIconSize(QSize(30, 30))
        display_fusion_3d_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonIconOnly)
        display_fusion_3d_button.setToolTip("三维融合")
        display_fusion_3d_button.setToolTipDuration(5000)

        layout_button = QGridLayout()
        layout_button.setSpacing(20)
        layout_button.setContentsMargins(0, 0, 0, 0)
        layout_button.addWidget(open_button, 0, 0, 1, 1)
        layout_button.addWidget(delete_button, 1, 0, 1, 1)
        layout_button.addWidget(display_2d_button, 0, 1, 1, 1)
        layout_button.addWidget(display_fusion_2d_button, 1, 1, 1, 1)
        layout_button.addWidget(display_3d_button, 0, 2, 1, 1)
        layout_button.addWidget(display_fusion_3d_button, 1, 2, 1, 1)
        layout.addLayout(layout_button)

        # scroll_area
        self.collapsible_button_layout = QVBoxLayout()
        self.collapsible_button_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.collapsible_button_layout.setSpacing(0)
        self.collapsible_button_layout.setContentsMargins(0, 0, 0, 0)
        scroll_area = QScrollArea(self)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scrollAreaContent = QWidget(scroll_area)
        scrollAreaContent.setLayout(self.collapsible_button_layout)
        # 添加
        scroll_area.setWidget(scrollAreaContent)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # 信号与槽
        delete_button.clicked.connect(self.delete_button_clicked)
        open_button.clicked.connect(self.open_button_clicked)
        display_2d_button.clicked.connect(lambda: self.display_button_clicked("2D"))
        display_3d_button.clicked.connect(lambda: self.display_button_clicked("3D"))
        display_fusion_2d_button.clicked.connect(lambda: self.display_fusion_button_clicked("2DFusion"))
        display_fusion_3d_button.clicked.connect(lambda: self.display_fusion_button_clicked("3DFusion"))

    def add_collapsible_widget(self, study_image: dict):
        for study_uid, series_image in study_image.items():
            description = series_image.pop("description")
            if study_uid in self.collapsible_widgets:
                self.collapsible_widgets[study_uid].add_children(series_image)
            else:
                widget = CollapsibleWidget(study_uid, description, series_image)
                # 绑定信号与槽
                widget.child_toggled.connect(self.toggle_collapsible_child)
                self.collapsible_widgets[study_uid] = widget
                self.collapsible_button_layout.addWidget(widget)

    def toggle_collapsible_child(self, widget_uid: str, child_uid: str, c: bool):
        if c:
            self.toggled_children.append(widget_uid + "_^_" + child_uid)
            if self.toggled_children[0].startswith(widget_uid):
                while len(self.toggled_children) >= 3:
                    checked = self.toggled_children[0]
                    widget_uid, child_uid = checked.split("_^_")
                    self.collapsible_widgets[widget_uid].children[child_uid].radio_button.setChecked(False)
            else:
                for checked in self.toggled_children[:-1]:
                    widget_uid, child_uid = checked.split("_^_")
                    self.collapsible_widgets[widget_uid].children[child_uid].radio_button.setChecked(False)
        else:
            self.toggled_children.remove(widget_uid + "_^_" + child_uid)

    def open_button_clicked(self):
        filename = QFileDialog().getOpenFileName(
            self, "选择文件", "./", filter="IMAGE(*.dcm *.nii *.nii.gz);;NIFTI(*.nii *.nii.gz);;DICOM(*.dcm)"
        )
        if len(filename[0]) == 0:
            return

        uid_dict_image = read_image(filename[0])
        self.add_collapsible_widget(uid_dict_image)

    def delete_button_clicked(self):
        for uid in self.toggled_children:
            widget_uid, child_uid = uid.split("_^_")
            widget = self.collapsible_widgets[widget_uid]
            widget.remove_child(child_uid)
            if len(widget.children) == 0:
                _collapsible_widget = self.collapsible_widgets.pop(widget_uid)
                _collapsible_widget.close()
                _collapsible_widget.destroy()
        self.toggled_children.clear()

    def display_button_clicked(self, image_type: str):
        for uid in self.toggled_children:
            widget_uid, child_uid = uid.split("_^_")
            widget = self.collapsible_widgets[widget_uid]
            child = widget.children[child_uid]

            if image_type == "3D" and child.image.modality != "CT" and child.image.modality != "PT":
                information("该功能仅支持PET或CT三维成像。")
                return

            title = "{0} - {1}".format(
                widget.collapsible_button.text().split(" ")[0], child.radio_button.text().split(" ")[0]
            )
            self.image_displayed.emit(f"{uid}-{image_type}", title, child.image)

    def display_fusion_button_clicked(self, fusion_type: str):
        images, title = [], None
        for uid in self.toggled_children:
            widget_uid, child_uid = uid.split("_^_")
            widget = self.collapsible_widgets[widget_uid]
            child = widget.children[child_uid]

            images.append(child.image)
            title = widget.collapsible_button.text().split(" ")[0] + " - " + child.radio_button.text().split(" ")[0]

        if len(images) == 2:
            if "PT" == images[0].modality and "CT" == images[1].modality:
                imagePT, imageCT = images[0], images[1]
                image = MedicalImage2.from_ct_pt(imageCT, imagePT)
                self.fusion_image_displayed.emit(uid + fusion_type, title, image)
                return
            if "PT" == images[1].modality and "CT" == images[0].modality:
                imagePT, imageCT = images[1], images[0]
                image = MedicalImage2.from_ct_pt(imageCT, imagePT)
                self.fusion_image_displayed.emit(uid + fusion_type, title, image)
                return
        information("该功能仅支持PET/CT融合成像。")

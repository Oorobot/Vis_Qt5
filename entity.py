from typing import List, Union

import numpy as np
import SimpleITK as sitk

DICOM_TAGS = {
    # General Study
    "0008|0020": "Study Date",
    "0008|0030": "Study Time",
    "0008|1030": "Study Description",
    "0020|000D": "Study Instance UID",  # 研究的唯一标识符
    # General Series
    "0008|0021": "Series Date",
    "0008|0031": "Series Time",
    "0008|0060": "Modality",  # CT: Computed Tomography; PT: Positron Emission Tomography; NM: Nuclear Medicine; OT: Other;
    "0008|103E": "Series Description",
    "0010|2210": "Anatomical Orientation Type",
    # Patient
    "0010|0010": "Patient's Name",
    "0010|0030": "Patient's Birth Date",
    "0010|0032": "Patient's Birth Time",
    # Patient Study
    "0010|1010": "Patient's Age",
    "0010|1020": "Patient's Size",
    "0010|1030": "Patient's Weight",
    # General Image
    "0020|0013": "Instance Number",  # 图像号
    # Image Plane
    "0018|0050": "Slice Thickness",  # 切片厚度
    "0020|0032": "Image Position (Patient)",  # 图像左上角的x、y和z坐标
    "0020|0037": "Image Orientation (Patient)",  # 第一行和第一列相对于患者的方向余弦。这些属性应成对提供。分别用于x、y和z轴的行值，然后分别用于x、y和z轴的列值。
    "0020|1041": "Slice Location",  # 成像平面的相对位置，单位为mm
    "0028|0030": "Pixel Spacing",  # 像素间距
    # Image Pixel
    "0028|0002": "Samples Per Pixel",  # 图像通道数，1或3。
    "0028|0010": "Row",  # 行
    "0028|0011": "Columns",  # 列
    # Mutil-frame
    "0028|0008": "Number Of Frames",  # 多帧图像中的帧数
}


class MedicalSlice:
    def __init__(self, fileName: str) -> None:
        self.image: sitk.Image = sitk.ReadImage(fileName)
        keys = self.image.GetMetaDataKeys()
        self.description = {}
        for key in keys:
            self.description[key] = self.image.GetMetaData(key)
        self.array = sitk.GetArrayFromImage(self.image)


class MedicalImage:
    def __init__(
        self, fileName: Union[str, List[str]], description: dict = None
    ) -> None:
        # (H, W) 或 (H, W, C) 或 (D, H, W) 或 (D, H, W, C)
        self.image: sitk.Image = sitk.ReadImage(fileName)
        self.size = self.image.GetSize()  # W, H, D
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.dimension = self.image.GetDimension()
        self.array = sitk.GetArrayFromImage(self.image)

        self.modality = (
            self.image.GetMetaData("0008|0060")
            if self.image.HasMetaDataKey("0008|0060")
            else "OT"
        )
        # [channel] 1: Gray; 3: RGB
        self.channel = (
            int(self.image.GetMetaData("0028|0002"))
            if self.image.HasMetaDataKey("0028|0002")
            else 1
        )
        # [view] s: sagittal; c: coronal; t: transverse
        if self.dimension == 2:
            self.size = {"s": self.size[0], "c": self.size[1], "t": 1}
            self.array = self.array[np.newaxis, ...]
        elif self.dimension == 3 or self.dimension == 4:
            self.size = {"s": self.size[0], "c": self.size[1], "t": self.size[-1]}
        self.position = {"s": 1, "c": 1, "t": 1}

        # 归一化
        self.normlize()
        # 翻转
        self.array = np.ascontiguousarray(np.flip(self.array, 0))

    def normlize(self, amin=None, amax=None):
        if amin is None:
            amin = self.array.min()
        if amax is None:
            amax = self.array.max()
        self.normlized_array = 1.0 * (self.array - amin) / (amax - amin)
        self.normlized_array = np.clip((self.normlized_array * 255), 0, 255)
        self.normlized_array = self.normlized_array.astype(np.uint8)

    def plane_s(self):
        return self.normlized_array[:, :, self.position["s"] - 1, ...]

    def plane_c(self):
        return self.normlized_array[:, self.position["c"] - 1, ...]

    def plane_t(self):
        return self.normlized_array[self.position["t"] - 1, ...]

    def position_add(self, view: str):
        self.position[view] += 1
        if self.position[view] > self.size[view]:
            self.position[view] = self.size[view]

    def position_sub(self, view: str):
        self.position[view] += 1
        if self.position[view] > self.size[view]:
            self.position[view] = self.size[view]


def ReadNIFTI(file):
    pass


def ReadDICOM(file):
    pass


# def ReadImage(files):
#     if isinstance(files, str):
#         self.image = sitk.ReadImage(files)
#         self.size = self.image.GetSize()  # W, H, D
#         self.origin = self.image.GetOrigin()
#         self.spacing = self.image.GetSpacing()
#         self.dimension = self.image.GetDimension()
#         self.array = sitk.GetArrayFromImage(self.image)
#         self.modality = (
#             self.image.GetMetaData("0008|0060")
#             if self.image.HasMetaDataKey("0008|0060")
#             else "OT"
#         )
#         self.channel = (
#             int(self.image.GetMetaData("0028|0002"))
#             if self.image.HasMetaDataKey("0028|0002")
#             else 1
#         )

#     if isinstance(files, List[str]):
#         files.sort()
#         # 读取第一个文件的图像
#         f_image = sitk.ReadImage(files[0])
#         _images = {}
#         # {"instance_number": {series_instance_uid, row, col, modality, pixel_spacing, slice_thickness, array}}
#         f_info = {
#             "series_instance_uid": f_image.GetMetaData("0020|000e"),
#             "row": f_image.GetMetaData("0028|0010"),
#             "col": f_image.GetMetaData("0028|0011"),
#             "modality": f_image.GetMetaData("0008|0060")
#             if f_image.HasMetaDataKey("0008|0060")
#             else "OT",
#             "pixel_spacing": f_image.GetMetaData("0018|0050")
#             if f_image.HasMetaDataKey("0018|0050")
#             else 1.0,
#             "slice_thickness": (_ for _ in f_image.GetMetaData("0028|0030").split("\\"))
#             if f_image.HasMetaDataKey("0028|0030")
#             else (1.0, 1.0),
#         }

#         _images[f_image.GetMetaData("0020|0013")] = f_info
#         for file in files[1:]:
#             pass

#     files.sort()
#     _images = {}

#     for file in files:
#         _image = sitk.ReadImage(file)
#         series_instance_id = _image.GetMetaData("0020|000e")
#         if series_instance_id in _images:
#             continue
#         _images[series_instance_id] = {
#             "array": sitk.GetArrayFromImage(_image),
#             "row": _image.GetMetaData("0028|0010"),
#             "col": _image.GetMetaData("0028|0011"),
#             "modality": _image.GetMetaData("0008|0060"),
#             "origin": _image.GetOrigin(),
#             "spacing": _image.GetSpacing(),
#             "dimension": _image.GetDimension(),
#         }


# def read_series_image(files):
#     pass


if __name__ == "__main__":
    from glob import glob

    # # dicom - series RGB image
    # files = glob(
    #     r"D:\admin\Desktop\DICOM-Utils\Files\Data\PETCT-FRI\NormalData\015\*.dcm"
    # )
    # series_RGB_image = Image(files)
    # # dicom - CT
    # files = glob(
    #     r"D:\admin\Desktop\DICOM-Utils\Files\Data\PETCT-FRI\NormalData\015\CT\*.dcm"
    # )
    # series_CT_image = Image(files)
    # # dicom - PT
    # files = glob(
    #     r"D:\admin\Desktop\DICOM-Utils\Files\Data\PETCT-FRI\NormalData\015\PET\*.dcm"
    # )
    # series_PT_image = Image(files)
    # dicom - NM
    # files = (
    #     r"D:\admin\Desktop\DICOM-Utils\Files\Data\ThreePhaseBone\hip\004\004_FLOW.dcm"
    # )
    # TPB_image = Image(files)

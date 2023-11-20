from typing import List, Union

import numpy as np
import SimpleITK as sitk


class Image:
    image = None
    array = None
    normlized_array = None
    modality = None
    channel = None

    def __init__(self, files: Union[str, List[str]]) -> None:
        try:
            self.image = sitk.ReadImage(files)  # (H, W) 或 (H, W, C) 或 (D, H, W) 或 (D, H, W, C)
        except:
            self.image = self.read_image(files)

        self.size = self.image.GetSize()  # W, H, D
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.dimension = self.image.GetDimension()
        self.array = sitk.GetArrayFromImage(self.image)

        try:
            self.modality = self.image.GetMetaData("0008|0060")
        except:
            self.modality = "OT"
        # DICOM TAG - Modality
        # CT: Computed Tomography; PT/PET: Positron Emission Tomography; NM: Nuclear Medicine; OT: Other;
        assert self.modality in [
            "OT",
            "NM",
            "CT",
            "PT",
            "PET",
        ], f"modality = {self.modality} is not support."
        try:
            self.channel = int(self.image.GetMetaData("0028|0002"))
        except:
            self.channel = 1
        # 通道: 1(Gray) 或 3(RGB)
        assert self.channel in [1, 3], f"channel = {self.channel} is not support."

        # view
        # s: sagittal; c: coronal; t: transverse
        if self.dimension == 2:
            self.size = {"s": self.size[0], "c": self.size[1], "t": 1}
            self.array = self.array[np.newaxis, ...]
        elif self.dimension == 3 or self.dimension == 4:
            self.size = {"s": self.size[0], "c": self.size[1], "t": self.size[-1]}
        else:
            raise Exception(f"not support {files}.")
        self.position = {"s": 1, "c": 1, "t": 1}

        # 翻转
        self.array = np.ascontiguousarray(np.flip(self.array, 0))
        # 归一化
        self.normlize()

    def normlize(self, amin=None, amax=None):
        if amin is None:
            amin = self.array.min()
        if amax is None:
            amax = self.array.max()
        self.normlized_array = 1.0 * (self.array - amin) / (amax - amin)
        self.normlized_array = np.clip((self.normlized_array * 255), 0, 255)
        self.normlized_array = self.normlized_array.astype(np.uint8)

    def read_image(self, files: Union[List[str], str]):
        if isinstance(files, str):
            self.image = sitk.ReadImage(files)
            self.size = self.image.GetSize()  # W, H, D
            self.origin = self.image.GetOrigin()
            self.spacing = self.image.GetSpacing()
            self.dimension = self.image.GetDimension()
            self.array = sitk.GetArrayFromImage(self.image)
            self.modality = self.image.GetMetaData("0008|0060") if self.image.HasMetaDataKey("0008|0060") else "OT"
            self.channel = int(self.image.GetMetaData("0028|0002")) if self.image.HasMetaDataKey("0028|0002") else 1

        if isinstance(files, List[str]):
            files.sort()
            # 读取第一个文件的图像
            f_image = sitk.ReadImage(files[0])
            _images = {}
            # {"instance_number": {series_instance_uid, row, col, modality, pixel_spacing, slice_thickness, array}}
            f_info = {
                "series_instance_uid": f_image.GetMetaData("0020|000e"),
                "row": f_image.GetMetaData("0028|0010"),
                "col": f_image.GetMetaData("0028|0011"),
                "modality": f_image.GetMetaData("0008|0060") if f_image.HasMetaDataKey("0008|0060") else "OT",
                "pixel_spacing": f_image.GetMetaData("0018|0050") if f_image.HasMetaDataKey("0018|0050") else 1.0,
                "slice_thickness": (_ for _ in f_image.GetMetaData("0028|0030").split("\\")) if f_image.HasMetaDataKey("0028|0030") else (1.0, 1.0),
            }

            _images[f_image.GetMetaData("0020|0013")] = f_info
            for file in files[1:]:
                pass

        files.sort()
        _images = {}

        for file in files:
            _image = sitk.ReadImage(file)
            series_instance_id = _image.GetMetaData("0020|000e")
            if series_instance_id in _images:
                continue
            _images[series_instance_id] = {
                "array": sitk.GetArrayFromImage(_image),
                "row": _image.GetMetaData("0028|0010"),
                "col": _image.GetMetaData("0028|0011"),
                "modality": _image.GetMetaData("0008|0060"),
                "origin": _image.GetOrigin(),
                "spacing": _image.GetSpacing(),
                "dimension": _image.GetDimension(),
            }

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


if __name__ == "__main__":
    from glob import glob

    # dicom - series RGB image
    files = glob(r"D:\admin\Desktop\DICOM-Utils\Files\Data\PETCT-FRI\NormalData\015\*.dcm")
    series_RGB_image = Image(files)
    # dicom - CT
    files = glob(r"D:\admin\Desktop\DICOM-Utils\Files\Data\PETCT-FRI\NormalData\015\CT\*.dcm")
    series_CT_image = Image(files)
    # dicom - PT
    files = glob(r"D:\admin\Desktop\DICOM-Utils\Files\Data\PETCT-FRI\NormalData\015\PET\*.dcm")
    series_PT_image = Image(files)
    # dicom - NM
    files = r"D:\admin\Desktop\DICOM-Utils\Files\Data\ThreePhaseBone\hip\004\004_FLOW.dcm"
    TPB_image = Image(files)
    0

from typing import List, Union

import numpy as np
import SimpleITK as sitk


class Image:
    image = None
    array = None
    normlized_array = None
    modality = None
    channel = None

    def __init__(self, filename: Union[str, List[str]]) -> None:
        self.image = sitk.ReadImage(filename)
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
            self.channel = self.image.GetMetaData("0028|0002")
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
            raise Exception(f"not support {filename}.")
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

    def plane_s(self):
        return self.normlized_array[..., self.position["s"] - 1]

    def plane_c(self):
        return self.normlized_array[..., self.position["c"] - 1, :]

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

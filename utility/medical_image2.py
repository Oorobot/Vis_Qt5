from typing import List, Tuple

import cv2
import numpy as np
import SimpleITK as sitk
from matplotlib.cm import get_cmap

from .common import float_01_to_uint8_0255
from .medical_image import MedicalImage


class MedicalImage2:
    def __init__(
        self,
        array: np.ndarray,
        array_pt: np.ndarray,
        size: Tuple[int, int, int],  # X, Y, Z
        origin: Tuple[int, int, int],  # X, Y, Z
        spacing: Tuple[int, int, int],  # X, Y, Z
        direction: List[int],  # Xx Xy Xz, Yx Yy Yz, Zx Zy Zz
        channel: int,
    ) -> None:
        self.array = array
        self.array_pt = array_pt
        self.size = size
        self.origin = origin
        self.spacing = spacing
        self.direction = direction
        self.modality = "PTCT"
        self.channel = channel

        self.cmap = get_cmap("gray")
        self.cmap_pt = get_cmap("hot")

        self.array_norm = None
        self.array_norm_pt = None
        self.normlize()
        self.normlize_pt()

    def normlize(self, amin: float = None, amax: float = None):
        if self.array.size != 0:
            if amin is None:
                amin = self.array.min()
            if amax is None:
                amax = self.array.max()
            _array = (self.array - amin) / (amax - amin + np.finfo(np.float32).eps)
        else:
            _array = self.array
        self.array_norm = float_01_to_uint8_0255(_array)

    def normlize_pt(self, amax: float = None):
        if self.array_pt.size != 0:
            if amax is None:
                amax = self.array_pt.max()
            _array = self.array_pt / (amax + np.finfo(np.float32).eps)
        else:
            _array = self.array_pt
        self.array_norm_pt = float_01_to_uint8_0255(_array)

    def plane_ct(self, view: str, pos: int):
        _array: np.ndarray = None
        if view == "s":
            _array = self.array_norm[:, :, pos - 1, ...]
        elif view == "c":
            _array = self.array_norm[:, pos - 1, ...]
        elif view == "t":
            _array = self.array_norm[pos - 1, ...]
        else:
            raise Exception(f"not support view = {view}.")
        return _array

    def plane_pt(self, view: str, pos: int):
        _array: np.ndarray = None
        if view == "s":
            _array = self.array_norm_pt[:, :, pos - 1, ...]
        elif view == "c":
            _array = self.array_norm_pt[:, pos - 1, ...]
        elif view == "t":
            _array = self.array_norm_pt[pos - 1, ...]
        else:
            raise Exception(f"not support view = {view}.")
        return _array

    def plane(self, view: str, pos: int, cmap_ct: str = None, cmap_pt: str = None):
        plane_ct = self.plane_ct(view, pos)
        plane_pt = self.plane_pt(view, pos)

        if cmap_ct is not None:
            self.cmap = get_cmap(cmap_ct)
        if cmap_pt is not None:
            self.cmap_pt = get_cmap(cmap_pt)

        plane_ct = float_01_to_uint8_0255(self.cmap(plane_ct))
        plane_pt = float_01_to_uint8_0255(self.cmap_pt(plane_pt))
        return cv2.addWeighted(plane_ct, 0.3, plane_pt, 0.7, 0)

    @staticmethod
    def from_ct_pt(ct: MedicalImage, pt: MedicalImage):
        _ct = ct.to_sitk_image()
        _pt = pt.to_sitk_image()

        array = sitk.GetArrayFromImage(_ct)
        size = _ct.GetSize()
        origin = _ct.GetOrigin()
        spacing = _ct.GetSpacing()
        direction = _ct.GetDirection()
        channel = ct.channel

        # 重采样进行配准
        pt_array = sitk.GetImageFromArray(pt.array)
        pt_array.CopyInformation(_pt)
        pt_respampled = sitk.Resample(pt_array, _ct)
        array_pt = sitk.GetArrayFromImage(pt_respampled)

        return MedicalImage2(array, array_pt, size, origin, spacing, direction, channel)

    def to_sitk_image(self) -> Tuple[sitk.Image, sitk.Image]:
        image_ct = sitk.GetImageFromArray(self.array)
        image_ct.SetOrigin(self.origin)
        image_ct.SetSpacing(self.spacing)
        image_ct.SetDirection(self.direction)
        image_pt = sitk.GetImageFromArray(self.array_pt)
        image_pt.CopyInformation(image_ct)
        return (image_ct, image_pt)

    def __getitem__(self, item):
        if isinstance(item, tuple):
            array = self.array[item]
            array_pt = self.array_pt[item]
        elif isinstance(item, slice):
            array = self.array[item]
            array_pt = self.array_pt[item]
        else:
            array = self.array[item : item + 1]
            array_pt = self.array_pt[item : item + 1]
        return MedicalImage2(array, array_pt, array.shape, self.origin, self.spacing, self.direction, self.channel)

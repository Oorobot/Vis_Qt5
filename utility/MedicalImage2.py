import cv2
import numpy as np
import SimpleITK as sitk
from matplotlib.cm import get_cmap

from utility.common import float_01_to_uint8_0255
from utility.MedicalImage import MedicalImage


class MedicalImage2:
    def __init__(self, ct: MedicalImage, pt: MedicalImage) -> None:
        _ct = ct.to_sitk_image()
        _pt = pt.to_sitk_image()

        self.array = sitk.GetArrayFromImage(_ct)
        self.size = _ct.GetSize()
        self.origin = _ct.GetOrigin()
        self.spacing = _ct.GetSpacing()
        self.direction = _ct.GetDirection()

        self.channel = ct.channel
        self.cmap = ct.cmap
        self.cmap_pt = get_cmap("hot")

        # 重采样进行配准
        _pt_array = sitk.GetImageFromArray(pt.array)
        _pt_array.CopyInformation(_pt)
        _pt_array = sitk.Resample(_pt_array, _ct)
        self.array_pt = sitk.GetArrayFromImage(_pt_array)

        self.array_norm = None
        self.normlize(which="CT")
        self.array_norm_pt = None
        self.normlize(0, 2.5, which="PT")

    def normlize(self, amin: float = None, amax: float = None, which: str = "CT"):
        if which == "CT":
            _array = self.array
        else:
            _array = self.array_pt

        if amin is None:
            amin = _array.min()
        if amax is None:
            amax = _array.max()

        _array = 1.0 * (_array - amin) / (amax - amin)
        _array = np.clip((_array * 255).round(), 0, 255)
        _array = _array.astype(np.uint8)

        if which == "CT":
            self.array_norm = _array
        else:
            self.array_norm_pt = _array

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


if __name__ == "__main__":
    from utility.io import ReadNIFTI

    CT = ReadNIFTI(r"D:\Files\Desktop\chapter5\DATA\001_CT.nii.gz", True)
    CT.modality = "CT"
    PT = ReadNIFTI(r"DATA\001_SUVbw.nii.gz", True)
    PT.modality = "PT"

    PTCT = MedicalImage2(CT, PT)

    plane_fused = PTCT.plane_fused("c", 286)
    plane_fused = plane_fused[:, :, ::-1]
    cv2.imshow("fused", plane_fused)
    cv2.waitKey(0)

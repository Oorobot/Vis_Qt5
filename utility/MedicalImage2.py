import cv2
import numpy as np
import SimpleITK as sitk
from matplotlib.cm import get_cmap

from utility.common import float_01_to_uint8_0255
from utility.MedicalImage import MedicalImage


class MedicalImage2:
    def __init__(self, ct: MedicalImage, pt: MedicalImage) -> None:
        self.size = ct.size
        self.origin = ct.origin
        self.direction = ct.direction
        self.modality = "ptct"
        self.channel = ct.channel

        self.arrat_ct = ct.array
        if ct.size != pt.size:
            _ct = ct.to_sitk_image()
            _pt = pt.to_sitk_image()
            _pt = sitk.Resample(_pt, _ct)
            self.array_pt = sitk.GetArrayFromImage(_pt)
        else:
            self.array_pt = pt.array

        self.array_ct_norm = None
        self.normlize("ct")
        self.array_pt_norm = None
        self.normlize("pt")

    def normlize(self, which: str, amin: float = None, amax: float = None):
        if which == "ct":
            _array = self.arrat_ct
        else:
            _array = self.array_pt

        if amin is None:
            amin = _array.min()
        if amax is None:
            amax = _array.max()

        _array = 1.0 * (_array - amin) / (amax - amin)
        _array = np.clip((_array * 255).round(), 0, 255)
        _array = _array.astype(np.uint8)

        if which == "ct":
            self.array_ct_norm = _array
        else:
            self.array_pt_norm = _array

    def plane_ct(self, view: str, pos: int):
        if view == "s":
            return self.array_ct_norm[:, :, pos - 1, ...]
        elif view == "c":
            return self.array_ct_norm[:, pos - 1, ...]
        elif view == "t":
            return self.array_ct_norm[pos - 1, ...]
        else:
            raise Exception(f"not support view = {view}.")

    def plane_pt(self, view: str, pos: int):
        if view == "s":
            return self.array_pt_norm[:, :, pos - 1, ...]
        elif view == "c":
            return self.array_pt_norm[:, pos - 1, ...]
        elif view == "t":
            return self.array_pt_norm[pos - 1, ...]
        else:
            raise Exception(f"not support view = {view}.")

    def plane_fused(self, view: str, pos: int):
        plane_ct = self.plane_ct(view, pos)
        plane_pt = self.plane_pt(view, pos)

        cmap_ct = get_cmap("gray")
        cmap_pt = get_cmap("hot")

        # self.normlize("CT", -450, 1050)
        # self.normlize("PT", 0, 1.3)

        plane_ct = float_01_to_uint8_0255(cmap_ct(plane_ct))
        plane_pt = float_01_to_uint8_0255(cmap_pt(plane_pt))

        return cv2.addWeighted(plane_ct, 0.5, plane_pt, 0.5, 0)


if __name__ == "__main__":
    from utility.io import ReadNIFTI

    CT = ReadNIFTI(r"D:\Files\Desktop\chapter5\DATA\001_CT.nii.gz", True)
    CT.modality = "CT"
    PT = ReadNIFTI(r"DATA\001_SUVbw.nii.gz", True)
    PT.modality = "PT"

    PTCT = MedicalImage2(CT, PT)

    plane = PTCT.plane_fused("c", 286)
    plane = plane[:, :, ::-1]
    cv2.imshow("fused", plane)
    cv2.waitKey(0)

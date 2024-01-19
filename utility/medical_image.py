from typing import List, Tuple, Union

import numpy as np
import SimpleITK as sitk
from matplotlib.cm import get_cmap

from utility.common import float_01_to_uint8_0255


class MedicalImage:
    def __init__(
        self,
        array: np.ndarray,
        size: Tuple[int, int, int],  # X, Y, Z
        origin: Tuple[int, int, int],  # X, Y, Z
        spacing: Tuple[int, int, int],  # X, Y, Z
        direction: List[int],  # Xx Xy Xz, Yx Yy Yz, Zx Zy Zz
        modality: str,  # PT, CT, NM, OT
        channel: int = None,
        files: Union[List[str], str] = None,
    ):
        self.array = array
        self.files = files
        self.size = size
        self.origin = origin
        self.spacing = spacing
        self.direction = direction
        self.modality = modality
        self.channel = (
            channel if channel is not None else 1 if len(self.array.shape) == len(self.size) else self.array.shape[-1]
        )

        # 映射颜色图
        if self.channel == 1:
            if self.modality == "PT" or self.modality == "NM":
                self.cmap = get_cmap("binary")
            else:  # CT, MR...
                self.cmap = get_cmap("gray")
        elif self.channel == 3:
            self.cmap = None
        else:
            raise Exception(f"not support channel = {self.channel}.")
        assert len(self.size) == 3, f"not support Medical Image's dimension = {len(self.size)}."

        self.array_norm = None
        self.normlize()

    def normlize(self, amin: float = None, amax: float = None):
        if self.channel == 1 and self.array.size != 0:
            if amin is None:
                amin = self.array.min()
            if amax is None:
                amax = self.array.max()
            _array = 1.0 * (self.array - amin) / (amax - amin + np.finfo(np.float32).eps)
            _array = float_01_to_uint8_0255(_array)
        else:
            _array = self.array
        self.array_norm = _array

    def plane_origin(self, view: str, pos: int):
        """
        get the origin plane of Medical Image
        :param view: Sagittal, Coronal, Transverse
        :param pos: the position, range: [1, size]
        """
        if view == "s":
            return self.array[:, :, pos - 1, ...]
        elif view == "c":
            return self.array[:, pos - 1, ...]
        elif view == "t":
            return self.array[pos - 1, ...]
        else:
            raise Exception(f"not support view = {view}.")

    def plane(self, view: str, pos: int, cmap: str = None):
        """
        get the normalized plane of Medical Image
        :param view: Sagittal, Coronal, Transverse
        :param pos: the position, range: [1, size]
        """
        _array: np.ndarray = None
        if view == "s":
            _array = self.array_norm[:, :, pos - 1, ...]
        elif view == "c":
            _array = self.array_norm[:, pos - 1, ...]
        elif view == "t":
            _array = self.array_norm[pos - 1, ...]
        else:
            raise Exception(f"not support view = {view}.")

        if cmap is not None:
            self.cmap = get_cmap(cmap)
        if self.cmap is not None:
            return float_01_to_uint8_0255(self.cmap(_array))
        else:
            return _array

    def to_sitk_image(self) -> sitk.Image:
        if self.files is not None:
            return sitk.ReadImage(self.files)
        else:
            image = sitk.GetImageFromArray(self.array)
            image.SetOrigin(self.origin)
            image.SetSpacing(self.spacing)
            image.SetDirection(self.direction)
            return image

    def __getitem__(self, item):
        if isinstance(item, tuple):
            array = self.array[item]
        elif isinstance(item, slice):
            array = self.array[item]
        else:
            array = self.array[item : item + 1]
        return MedicalImage(array, array.shape, self.spacing, self.origin, self.direction, self.modality)

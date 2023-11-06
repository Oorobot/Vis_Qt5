from typing import List, Union
import SimpleITK as sitk
import numpy as np


class Image:
    image = None
    array = None
    normlized_array = None
    modality = None  # DICOM TAG - Modality: CT: Computed Tomography; PT/PET: Positron Emission Tomography; NM: Nuclear Medicine; OT: Other;
    channel = None  # 通道数: 1, 3

    def __init__(self, filename: Union[str, List[str]]) -> None:
        self.image = sitk.ReadImage(filename)
        self.size = self.image.GetSize()  # W, H, D
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.dimension = self.image.GetDimension()
        self.array = sitk.GetArrayFromImage(self.image)

        self.x, self.y, self.z = 0, 0, 0  # x, y, z

        try:
            self.modality = self.image.GetMetaData("0008|0060")
        except:
            self.modality = 'OT'
        try:
            self.channel = self.image.GetMetaData("0028|0002")
        except:
            self.channel = 1

        if self.dimension == 2:
            self.size = (*self.size, 1)
            self.array = self.array[..., np.newaxis]
        assert len(self.array.shape) == 3 or len(self.array.shape) == 4, f"not support {filename}."
        self.normlize()

    def normlize(self, amin=None, amax=None):
        if amin is None:
            amin = self.array.min()
        if amax is None:
            amax = self.array.max()
        self.normlized_array = 1.0 * (self.array - amin) / (amax - amin)
        self.normlized_array = np.clip((self.normlized_array * 255), 0, 255)
        self.normlized_array = self.normlized_array.astype(np.uint8)

    def sagittal_plane(self):
        return self.normlized_array[..., self.x]

    def coronal_plane(self):
        return self.normlized_array[..., self.y, :]

    def transverse_plane(self):
        return self.normlized_array[self.z, ...]

    def sagittal_add(self):
        self.x = self.x + 1

    def coronal_point(self):
        self.y = self.y + 1

    def transverse_point(self):
        self.z = self.z + 1

    def convert_to_SUVbw(self):
        pass

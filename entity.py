import os
from glob import glob

import numpy as np
import SimpleITK as sitk
from pydicom import dcmread

from utils import count_seconds

DICOM_TAGS = {
    # General Study
    "0008|0020": "Study Date",
    "0008|0030": "Study Time",
    "0008|1030": "Study Description",
    "0020|000d": "Study Instance UID",  # 研究的唯一标识符
    # General Series
    "0008|0021": "Series Date",
    "0008|0031": "Series Time",
    "0008|0060": "Modality",  # CT: Computed Tomography; PT: Positron Emission Tomography; NM: Nuclear Medicine; OT: Other;
    "0008|103e": "Series Description",
    "0010|2210": "Anatomical Orientation Type",
    "0020|000e": "Series Instance UID",  # 系列的唯一标识符，该系列是Study Instance UID中标识的研究的一部分
    # Patient
    "0010|0010": "Patient's Name",
    "0010|0030": "Patient's Birth Date",
    "0010|0032": "Patient's Birth Time",
    # General Equipment
    "0008|0070": "Manufacturer",
    "0008|0080": "Institution Name",
    "0008|1010": "Station Name",
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
    # PET Isotope
    "0018|1072": "Radiopharmaceutical Start Time",
    "0018|1074": "Radionuclide Total Dose",
    "0018|1075": "Radionuclide Half Life",
}


class MedicalSlice:
    def __init__(self, fileName: str) -> None:
        self.file = fileName
        self.dicom = dcmread(fileName)

        self.suid = "_".join(
            [
                self.dicom.StudyInstanceUID,
                str(self.dicom.PatientName) if hasattr(self.dicom, "PatientName") else "Anonym",
            ]
        )
        self.siuid = "_".join([self.dicom.SeriesInstanceUID, str(self.dicom.Rows), str(self.dicom.Columns)])
        self.origin = (
            self.dicom.ImagePositionPatient if hasattr(self.dicom, "ImagePositionPatient") else [0.0, 0.0, 0.0]
        )
        spacingD = self.dicom.SliceThickness if hasattr(self.dicom, "SliceThickness") else 1.0
        spacingHW = self.dicom.PixelSpacing if hasattr(self.dicom, "PixelSpacing") else [1.0, 1.0]
        self.spacing = [spacingHW[1], spacingHW[0], spacingD]
        directionZ = [0.0, 0.0, 1.0]
        directionXY = (
            [float(_) for _ in self.dicom.ImageOrientationPatient]
            if hasattr(self.dicom, "ImageOrientationPatient")
            else [1.0, 0.0, 0.0, 0.0, 1.0, 0.0]
        )
        self.direction = directionXY + directionZ

        self.modality = self.dicom.Modality
        self.channel = self.dicom.SamplesPerPixel
        self.description = self.dicom.SeriesDescription if hasattr(self.dicom, "SeriesDescription") else "none"
        # Pixel Data
        if self.modality == "PT":
            bw = self.dicom.PatientWeight * 1000
            ris = self.dicom.RadiopharmaceuticalInformationSequence[0]
            decay_time = count_seconds(
                self.dicom.SeriesDate + self.dicom.SeriesTime,
                self.dicom.SeriesDate + ris.RadiopharmaceuticalStartTime,
            )
            actual_activity = float(ris.RadionuclideTotalDose) * (
                2 ** (-(decay_time) / float(ris.RadionuclideHalfLife))
            )
            self.array = (
                (self.dicom.pixel_array * self.dicom.RescaleSlope + self.dicom.RescaleIntercept) * bw / actual_activity
            )
        else:
            if hasattr(self.dicom, "RescaleSlope") and hasattr(self.dicom, "RescaleIntercept"):
                self.array = self.dicom.pixel_array * self.dicom.RescaleSlope + self.dicom.RescaleIntercept
            else:
                self.array = self.dicom.pixel_array


class MedicalImage:
    def __init__(self, image: sitk.Image, modality: str, description: str, channel: int = None):
        # (H, W) 或 (H, W, C) 或 (D, H, W) 或 (D, H, W, C)
        self.image = image
        self.size = self.image.GetSize()
        self.origin = self.image.GetOrigin()
        self.spacing = self.image.GetSpacing()
        self.dimension = self.image.GetDimension()
        self.array = sitk.GetArrayFromImage(self.image)

        self.modality = modality  # PT, CT, NM, OT
        self.description = description
        self.channel = channel  # 1: Gray; 3: RGB
        if self.channel is None:
            if len(self.array.shape) != self.dimension:
                self.channel = self.array.shape[-1]
            else:
                self.channel = 1
        # [view] s: sagittal; c: coronal; t: transverse
        if self.dimension == 2:
            self.size = {"s": self.size[0], "c": self.size[1], "t": 1}
            self.array = self.array[np.newaxis, ...]
        elif self.dimension == 3:
            self.size = {"s": self.size[0], "c": self.size[1], "t": self.size[2]}
        self.position = {"s": 1, "c": 1, "t": 1}

        # 归一化
        self.normlize()
        # 翻转
        # self.array = np.ascontiguousarray(np.flip(self.array, 0))

    def normlize(self, amin: float = None, amax: float = None):
        if self.channel == 3:
            self.normlized_array = self.array.astype(np.uint8)
        else:
            if amin is None:
                amin = self.array.min()
            if amax is None:
                amax = self.array.max()
            self.normlized_array = 1.0 * (self.array - amin) / (amax - amin)
            self.normlized_array = np.clip((self.normlized_array * 255).round(), 0, 255)
            self.normlized_array = self.normlized_array.astype(np.uint8)

    def plane(self, view: str):
        if view == "s" or view == "sagittal":
            return self.normlized_array[:, :, self.position["s"] - 1, ...]
        elif view == "c" or view == "coronal":
            return self.normlized_array[:, self.position["c"] - 1, ...]
        elif view == "t" or view == "transverse":
            return self.normlized_array[self.position["t"] - 1, ...]

    def positionAdd(self, view: str):
        self.position[view] = self.position[view] + 1 if self.position[view] < self.size[view] else self.size[view]

    def positionSub(self, view: str):
        self.position[view] = self.position[view] - 1 if self.position[view] > 1 else 1


def ReadNIFTI(file: str, onlyImage=False):
    fileName = os.path.basename(file)
    image = sitk.ReadImage(file)
    if onlyImage:
        return MedicalImage(image, "OT", "NONE")
    else:
        return {f"suid_{fileName}": {"siuid": MedicalImage(image, "OT", "NONE")}}


def ReadDICOM(file: str):
    fileName, ext = os.path.splitext(file)
    directory = os.path.dirname(fileName)
    files = glob(os.path.join(directory, "*" + ext))
    files.sort()

    slices = {}
    for file in files:
        slice = MedicalSlice(file)
        if slice.suid not in slices:
            slices[slice.suid] = {slice.siuid: [slice]}
        else:
            if slice.siuid not in slices[slice.suid]:
                slices[slice.suid][slice.siuid] = [slice]
            else:
                slices[slice.suid][slice.siuid] += [slice]

    for suid in slices:
        for siuid in slices[suid]:
            # 如果该系列仅有一张切片
            if len(slices[suid][siuid]) == 1:
                image = sitk.ReadImage(slices[suid][siuid][0].file)
                slices[suid][siuid] = MedicalImage(
                    image,
                    modality=slices[suid][siuid][0].modality,
                    description=slices[suid][siuid][0].description,
                    channel=slices[suid][siuid][0].channel,
                )
                continue
            # 如果有很多张
            slicesLeft = []
            skipCount = 0
            for slice in slices[suid][siuid]:
                slice: MedicalSlice
                if hasattr(slice.dicom, "SliceLocation"):
                    slicesLeft.append(slice)
                else:
                    skipCount += 1
            print("skipped, no SliceLocation: {}".format(skipCount))
            if len(slicesLeft) != 0:
                # 根据切片位置进行排序
                slices[suid][siuid] = slicesLeft
                slices[suid][siuid].sort(key=lambda s: s.dicom.SliceLocation)
            else:
                print("no Slice has SliceLocation.")
                # 按照Instance Number排序
                slices[suid][siuid].sort(key=lambda s: s.dicom.InstanceNumber)

            # mutil 2D Slices -> 3D Volume
            volume = np.zeros(
                shape=(len(slices[suid][siuid]), *slices[suid][siuid][0].array.shape),
                dtype=slices[suid][siuid][0].array.dtype,
            )
            for i, slice in enumerate(slices[suid][siuid]):
                slice: MedicalSlice
                volume[i] = slice.array
            image = sitk.GetImageFromArray(volume)
            image.SetOrigin(slices[suid][siuid][0].origin)
            image.SetSpacing(slices[suid][siuid][0].spacing)
            image.SetDirection(slices[suid][siuid][0].direction)
            medicalImage = MedicalImage(
                image,
                modality=slices[suid][siuid][0].modality,
                description=slices[suid][siuid][0].description,
                channel=slices[suid][siuid][0].channel,
            )
            slices[suid][siuid] = medicalImage
    return slices


def ReadImage(file: str):
    _, ext = os.path.splitext(file)
    if file.endswith(".dcm"):
        return ReadDICOM(file)
    elif file.endswith((".nii", ".nii.gz")):
        return ReadNIFTI(file)
    else:
        raise Exception("not support {} format file.".format(ext))


if __name__ == "__main__":
    file = r"DATA\001\ImageFileName000.dcm"
    series_RGB = ReadDICOM(file)
    # file = r"DATA\001\CT\ImageFileName000.dcm"
    # ct = ReadDICOM(file)
    # file = r"DATA\001\PET\ImageFileName000.dcm"
    # pt = ReadDICOM(file)
    # file = r"DATA\ThreePhaseBone_001\001_FLOW.dcm"
    # nm = ReadDICOM(file)
    file = r"DATA\001_CT.nii.gz"
    niigz = ReadNIFTI(file)
    0

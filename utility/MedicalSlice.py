from datetime import datetime

import numpy as np
from pydicom import FileDataset, dcmread
from pydicom.uid import generate_uid


class MedicalSlice(object):
    def __init__(self, file: str) -> None:
        dicom = dcmread(file)

        self.study_uid = dicom.StudyInstanceUID if hasattr(dicom, "StudyInstanceUID") else (generate_uid())
        self.__study_date = dicom.StudyDate if hasattr(dicom, "StudyDate") else "00000000"
        self.__study_time = dicom.StudyTime if hasattr(dicom, "StudyTime") else "000000"

        self.series_uid = dicom.SeriesInstanceUID if hasattr(dicom, "SeriesInstanceUID") else (generate_uid())
        self.series_description = dicom.SeriesDescription if hasattr(dicom, "SeriesDescription") else "none"

        self.patient_name = str(dicom.PatientName) if hasattr(dicom, "PatientName") else "Anonym"

        self.__height, self.__width = int(dicom.Rows), int(dicom.Columns)
        self.__depth = int(dicom.NumberOfFrames) if hasattr(dicom, "NumberOfFrames") else 0

        self.origin = (
            [float(_) for _ in dicom.ImagePositionPatient]
            if hasattr(dicom, "ImagePositionPatient")
            else [0.0, 0.0, 0.0]
        )

        self.__spacing_y, self.__spacing_x = (
            [float(_) for _ in dicom.PixelSpacing] if hasattr(dicom, "PixelSpacing") else [1.0, 1.0]
        )
        self.__spacing_z = float(dicom.SliceThickness) if hasattr(dicom, "SliceThickness") else 1.0

        if hasattr(dicom, "ImageOrientationPatient"):
            self.__direction_x = [float(_) for _ in dicom.ImageOrientationPatient[0:3]]
            self.__direction_y = [float(_) for _ in dicom.ImageOrientationPatient[3:6]]
        else:
            self.__direction_x = [1.0, 0.0, 0.0]
            self.__direction_y = [0.0, 1.0, 0.0]
        self.__direction_z = np.cross(self.__direction_x, self.__direction_y).tolist()

        self.modality = dicom.Modality

        # 跟像素相关的数据
        self.photometric_interpretation = dicom.PhotometricInterpretation
        self.__samples_per_pixel = dicom.SamplesPerPixel
        if self.photometric_interpretation == "RGB":
            self.planar_configuration = dicom.PlanarConfiguration

        self.array = self.convert_array(dicom)

        # 用于一系列 dcm 文件排序用
        self.slice_location = float(dicom.SliceLocation) if hasattr(dicom, "SliceLocation") else None
        self.instance_number = (
            int(dicom.InstanceNumber) if hasattr(dicom, "InstanceNumber") and dicom.InstanceNumber is not None else None
        )

    @property
    def study_datetime(self):
        return self.str2datetime(self.__study_date + self.__study_time).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def size(self):
        return (self.__width, self.__height, self.__depth)

    @property
    def spacing(self):
        return (self.__spacing_x, self.__spacing_y, self.__spacing_z)

    @property
    def direction(self):
        return self.__direction_x + self.__direction_y + self.__direction_z

    @property
    def channel(self):
        return self.__samples_per_pixel

    def convert_array(self, dcm: FileDataset) -> np.ndarray:
        if self.modality == "PT":
            bw = dcm.PatientWeight * 1000
            ris = dcm.RadiopharmaceuticalInformationSequence[0]
            decay_time = self.seconds(
                dcm.SeriesDate + dcm.SeriesTime,
                dcm.SeriesDate + ris.RadiopharmaceuticalStartTime,
            )
            actual_activity = float(ris.RadionuclideTotalDose) * (
                2 ** (-(decay_time) / float(ris.RadionuclideHalfLife))
            )
            return (dcm.pixel_array * dcm.RescaleSlope + dcm.RescaleIntercept) * bw / actual_activity
        else:
            if hasattr(dcm, "RescaleSlope") and hasattr(dcm, "RescaleIntercept"):
                return dcm.pixel_array * dcm.RescaleSlope + dcm.RescaleIntercept
            else:
                return dcm.pixel_array

    def seconds(self, end_time: str, start_time: str) -> float:
        e, s = self.str2datetime(end_time), self.str2datetime(start_time)
        return (e - s).total_seconds()

    @staticmethod
    def str2datetime(s: str) -> datetime:
        try:
            t = datetime.strptime(s, "%Y%m%d%H%M%S")
        except:
            try:
                t = datetime.strptime(s, "%Y%m%d%H%M%S.%f")
            except Exception as e:
                raise e
        return t


if __name__ == "__main__":
    slice1 = MedicalSlice(r"DATA\ThreePhaseBone_001\001_FLOW.dcm")
    slice2 = MedicalSlice(r"DATA\001\ImageFileName0.dcm")
    slice3 = MedicalSlice(r"DATA\001\PET\ImageFileName000.dcm")
    0

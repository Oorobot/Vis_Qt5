from datetime import datetime

import numpy as np
from pydicom import FileDataset, dcmread
from pydicom.uid import generate_uid


class MedicalSlice(object):
    def __init__(self, file: str) -> None:
        dicom = dcmread(file)

        self._study_uid = dicom.StudyInstanceUID if hasattr(dicom, "StudyInstanceUID") else (generate_uid())
        self._study_date = dicom.StudyDate if hasattr(dicom, "StudyDate") else "00000000"
        self._study_time = dicom.StudyTime if hasattr(dicom, "StudyTime") else "000000"

        self._series_uid = dicom.SeriesInstanceUID if hasattr(dicom, "SeriesInstanceUID") else (generate_uid())
        self._series_description = dicom.SeriesDescription if hasattr(dicom, "SeriesDescription") else "none"

        self._patient_name = str(dicom.PatientName) if hasattr(dicom, "PatientName") else "Anonym"

        self._height, self._width = int(dicom.Rows), int(dicom.Columns)
        self._depth = int(dicom.NumberOfFrames) if hasattr(dicom, "NumberOfFrames") else 0

        self._origin = (
            [float(_) for _ in dicom.ImagePositionPatient]
            if hasattr(dicom, "ImagePositionPatient")
            else [0.0, 0.0, 0.0]
        )

        self._spacing_y, self._spacing_x = (
            [float(_) for _ in dicom.PixelSpacing] if hasattr(dicom, "PixelSpacing") else [1.0, 1.0]
        )
        self._spacing_z = float(dicom.SliceThickness) if hasattr(dicom, "SliceThickness") else 1.0

        if hasattr(dicom, "ImageOrientationPatient"):
            self._direction_x = [float(_) for _ in dicom.ImageOrientationPatient[0:3]]
            self._direction_y = [float(_) for _ in dicom.ImageOrientationPatient[3:6]]
        else:
            self._direction_x = [1.0, 0.0, 0.0]
            self._direction_y = [0.0, 1.0, 0.0]
        self._direction_z = np.cross(self._direction_x, self._direction_y).tolist()

        self._modality = dicom.Modality

        self._channel = dicom.SamplesPerPixel

        self._array = self.convert_array(dicom)

        # 用于一系列 dcm 文件排序用
        self._slice_location = float(dicom.SliceLocation) if hasattr(dicom, "SliceLocation") else None
        self._instance_number = (
            int(dicom.InstanceNumber) if hasattr(dicom, "InstanceNumber") and dicom.InstanceNumber is not None else None
        )

    @property
    def array(self):
        return self._array

    @property
    def study_uid(self):
        return self._study_uid

    @property
    def study_datetime(self):
        return self.str2datetime(self._study_date + self._study_time).strftime("%Y-%m-%d %H:%M:%S")

    @property
    def series_uid(self):
        return self._series_uid

    @property
    def series_description(self):
        return self._series_description

    @property
    def patient_name(self):
        return self._patient_name

    @property
    def size(self):
        return (self._width, self._height, self._depth)

    @property
    def origin(self):
        return self._origin

    @property
    def spacing(self):
        return (self._spacing_x, self._spacing_y, self._spacing_z)

    @property
    def direction(self):
        return self._direction_x + self._direction_y + self._direction_z

    @property
    def modality(self):
        return self._modality

    @property
    def channel(self):
        return self._channel

    @property
    def slice_location(self):
        return self._slice_location

    @property
    def instance_number(self):
        return self._instance_number

    def convert_array(self, dcm: FileDataset) -> np.ndarray:
        if self._modality == "PT":
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

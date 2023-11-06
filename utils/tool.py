import os
from datetime import datetime
from glob import glob
import cv2
from typing import List, Tuple

import numpy as np
import pydicom
import SimpleITK as sitk


def count_seconds(time1: str, time2: str) -> float:
    def str2datetime(time: str) -> datetime:
        try:
            t = datetime.strptime(time, "%Y%m%d%H%M%S")
        except:
            try:
                t = datetime.strptime(time, "%Y%m%d%H%M%S.%f")
            except Exception as e:
                raise e
        return t

    return (str2datetime(time1) - str2datetime(time2)).total_seconds()


# -----------------------------------------------------------#
#                      图像转换
# -----------------------------------------------------------#
def normalize(pixel_value: np.ndarray, mi: float, ma: float, to_uint8: bool = False):
    pix = np.clip(pixel_value, mi, ma)
    pix = pix / (ma - mi)
    return pix if not to_uint8 else (pix * 255).astype(np.uint8)


def normalize_window(
    pixel_value: np.ndarray,
    window_center: float,
    window_width: float,
    to_uint8: bool = False,
):
    mi = window_center - window_width * 0.5
    ma = window_center + window_width * 0.5
    return normalize(pixel_value, mi, ma, to_uint8)


# -----------------------------------------------------------#
#               计算单张 PET(Dicom) 的 SUVbw
# -----------------------------------------------------------#
def get_SUVbw(pixel_value: np.ndarray, file: str) -> np.ndarray:
    """来源: https://qibawiki.rsna.org/index.php/Standardized_Uptake_Value_(SUV) 中 "SUV Calculation"。
    \n 不适用于来源于 GE Medical 的 Dicom 文件。
    """
    image = pydicom.dcmread(file)
    if "ATTN" in image.CorrectedImage and "DECY" in image.CorrectedImage and image.DecayCorrection == "START":
        if image.Units == "BQML":
            half_life = float(image.RadiopharmaceuticalInformationSequence[0].RadionuclideHalfLife)
            if image.SeriesDate <= image.AcquisitionDate and image.SeriesTime <= image.AcquisitionTime:
                scan_datetime = image.SeriesDate + image.SeriesTime
            if "RadiopharmaceuticalStartDateTime" in image.RadiopharmaceuticalInformationSequence[0]:
                start_datetime = image.RadiopharmaceuticalInformationSequence[0].RadiopharmaceuticalStartDateTime
            else:
                start_datetime = image.SeriesDate + image.RadiopharmaceuticalInformationSequence[0].RadiopharmaceuticalStartTime
            decay_time = count_seconds(scan_datetime, start_datetime)
            injected_dose = float(image.RadiopharmaceuticalInformationSequence[0].RadionuclideTotalDose)
            decayed_dose = injected_dose * (2 ** (-decay_time / half_life))
            SUVbwScaleFactor = image.PatientWeight * 1000 / decayed_dose
        elif image.Units == "CNTS":
            SUVbwScaleFactor = image.get_item((0x7053, 0x1000))
        elif image.Units == "GML":
            SUVbwScaleFactor = 1.0
    SUVbw = (pixel_value * float(image.RescaleSlope) + float(image.RescaleIntercept)) * SUVbwScaleFactor
    return SUVbw


# -----------------------------------------------------------#
#        计算来源于 GE Medical 的单张 PET(Dicom) 的 SUV
# -----------------------------------------------------------#
def compute_SUVbw(image: sitk.Image):
    patient_weight = image.GetMetaData("0010|1030")
    series_date = image.GetMetaData("0008|0021")
    series_time = image.GetMetaData("0008|0031")
    keys = image.GetMetaDataKeys()
    radiopharmaceutical_info = image.GetMetaData("0054|0016")


def get_SUV_in_GE(pixel_value: np.ndarray, file: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """来源: https://qibawiki.rsna.org/images/4/40/Calculation_of_SUVs_in_GE_Apps_v4_%282%29.doc。
    \n 仅适用于 GE medical
    \n 返回 SUVbw, SUVbsa, SUVlbm
    """
    image = pydicom.dcmread(file)
    try:
        bw = image.PatientWeight * 1000  # g
        bsa = (image.PatientWeight**0.425) * ((image.PatientSize * 100) ** 0.725) * 0.007184 * 10000
        lbm = (
            (1.10 * image.PatientWeight - 120 * ((image.PatientWeight / (image.PatientSize * 100)) ** 2))
            if image.PatientSex == "M"  # 性别为男
            else (1.07 * image.PatientWeight - 148 * ((image.PatientWeight / (image.PatientSize * 100)) ** 2))  # 性别为女
        )
        decay_time = count_seconds(
            image.SeriesDate + image.SeriesTime,
            image.SeriesDate + image.RadiopharmaceuticalInformationSequence[0].RadiopharmaceuticalStartTime,
        )
        actual_activity = float(image.RadiopharmaceuticalInformationSequence[0].RadionuclideTotalDose) * (
            2 ** (-(decay_time) / float(image.RadiopharmaceuticalInformationSequence[0].RadionuclideHalfLife))
        )
    except Exception as e:
        raise e

    SUVbw = pixel_value * bw / actual_activity  # g/ml
    SUVbsa = pixel_value * bsa / actual_activity  # cm2/ml
    SUVlbm = pixel_value * lbm * 1000 / actual_activity  # g/ml
    return SUVbw, SUVbsa, SUVlbm


def read(file, ext):
    if ext == "dcm":
        _image = sitk.ReadImage(file)
        # 获取系列ID和其他属性
        series_instance_id = _image.GetMetaData("0020|000e")
        row = _image.GetMetaData("0028|0010")
        col = _image.GetMetaData("0028|0011")
        isPET = _image.GetMetaData("0008|0060") == "PT"

        # 根据该文件获取该系列所有文件
        series = {}
        dir_path = os.path.dirname(file)
        files = glob(os.path.join(dir_path, "*.dcm"))

        _temp_files = []
        for f in files:
            _i = sitk.ReadImage(f)
            if series_instance_id == _i.GetMetaData("0020|000e") and row == _i.GetMetaData("0028|0010") and col == _i.GetMetaData("0028|0011"):
                series[int(_i.GetMetaData("0020|0013"))] = {"image": _i, "file": f}
                _temp_files.append(f)

        temp_array = sitk.GetArrayFromImage(sitk.ReadImage(_temp_files))
        suvbw = np.zeros_like(temp_array)
        for i in range(temp_array.shape[0]):
            suvbw[i] = get_SUV_in_GE(temp_array[i], _temp_files[i])
            print(f"suvbw max - {np.max(temp_array[i])}")

        keys = sorted(list(series.keys()))

        if isPET:
            # 转换成 SUVbw
            for k in keys:
                suvbw, _, _ = get_SUV_in_GE(sitk.GetArrayFromImage(series[k]["image"]), series[k]["file"])

                dicom_tags = pydicom.dcmread(series[k]["file"])
                bw = dicom_tags.PatientWeight * 1000
                ris = dicom_tags.RadiopharmaceuticalInformationSequence[0]
                decay_time = count_seconds(
                    dicom_tags.SeriesDate + dicom_tags.SeriesTime,
                    dicom_tags.SeriesDate + ris.RadiopharmaceuticalStartTime,
                )
                actual_activity = float(ris.RadionuclideTotalDose) * (2 ** (-(decay_time) / float(ris.RadionuclideHalfLife)))
                series[k]["image"] = series[k]["image"] * bw / actual_activity
                image = series[k]["image"]

                print(f"key: max - {max(image)}, suvbw: max - {np.max(suvbw)}")
            a = normalize(sitk.GetArrayFromImage(series[keys[0]]["image"]), 0, 2.5)
            cv2.imshow("a", a[0])
            cv2.waitKey(0)
        else:
            image = sitk.Compose([series[k]["image"] for k in keys])
        return image
    else:
        return sitk.ReadImage(file)

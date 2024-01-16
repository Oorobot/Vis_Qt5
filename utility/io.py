import os
from glob import glob
from typing import Union

import numpy as np
import SimpleITK as sitk
from pydicom.uid import generate_uid

from utility.MedicalImage import MedicalImage
from utility.MedicalSlice import MedicalSlice


def ReadNIFTI(file: str, only_image=False) -> Union[dict, MedicalImage]:
    filename = os.path.basename(file)
    image = sitk.ReadImage(file)
    medical_image = MedicalImage(
        sitk.GetArrayFromImage(image),
        image.GetSize(),
        image.GetOrigin(),
        image.GetSpacing(),
        image.GetDirection(),
        "OT",
        files=[os.path.abspath(file)],
    )
    if only_image:
        return medical_image
    else:
        study_uid, series_uid = str(generate_uid()), str(generate_uid())
        size_uid = str(medical_image.size)
        return {
            study_uid: {
                "description": filename,
                series_uid: {
                    "description": "none",
                    size_uid: medical_image,
                },
            }
        }


def ReadDICOM(file: str) -> dict:
    filename, ext = os.path.splitext(file)
    directory = os.path.dirname(filename)
    files = glob(os.path.join(directory, "*" + ext))
    files.sort()

    slices = {}
    for file in files:
        slice = MedicalSlice(file)
        size_uid = str(slice.size)
        if slice.study_uid not in slices:
            slices[slice.study_uid] = {
                "description": slice.patient_name + " " + slice.study_datetime,
                slice.series_uid: {
                    "description": slice.series_description,
                    size_uid: [slice],
                },
            }
        else:
            study_slices = slices[slice.study_uid]
            if slice.series_uid not in study_slices:
                study_slices[slice.series_uid] = {
                    "description": slice.series_description,
                    size_uid: [slice],
                }
            else:
                series_slices = study_slices[slice.series_uid]
                if size_uid not in series_slices:
                    series_slices[size_uid] = [slice]
                else:
                    series_slices[size_uid] += [slice]

    for study_uid in slices:
        study_slices = slices[study_uid]
        for series_uid in study_slices:
            if series_uid == "description":
                continue

            series_slices = study_slices[series_uid]
            size_uids = list(series_slices.keys())
            for size_uid in size_uids:
                if size_uid == "description":
                    continue
                size_slices = series_slices[size_uid]
                # Slices -> Volume
                slices_left, skip_count = [], 0
                for slice in size_slices:
                    if slice.slice_location is not None:
                        slices_left.append(slice)
                    else:
                        skip_count += 1
                if len(slices_left) != 0:
                    print("[INFO] compose slices by slice location.")
                    size_slices = slices_left
                    size_slices.sort(key=lambda x: x.slice_location)
                else:
                    print("[INFO] compose slices by instance number.")
                    size_slices.sort(key=lambda x: x.instance_number)
                volume = np.concatenate(
                    [s.array[np.newaxis, ...] if s.size[-1] == 0 else s.array for s in size_slices], axis=0
                )
                # volume -> Medical Image
                w, h, _d = size_slices[0].size
                d = len(size_slices) if _d == 0 else _d
                files = [s.path for s in size_slices]
                medical_image = MedicalImage(
                    volume,
                    (w, h, d),
                    size_slices[0].origin,
                    size_slices[0].spacing,
                    size_slices[0].direction,
                    size_slices[0].modality,
                    size_slices[0].channel,
                    files,
                )
                # replace size_uid and mediacl_image
                series_slices.pop(size_uid)
                series_slices[str(medical_image.size)] = medical_image

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
    file = r"DATA\001\CT\ImageFileName000.dcm"
    ct = ReadDICOM(file)
    file = r"DATA\001\PET\ImageFileName000.dcm"
    pt = ReadDICOM(file)
    file = r"DATA\ThreePhaseBone_001\001_FLOW.dcm"
    nm = ReadDICOM(file)
    file = r"DATA\001_CT.nii.gz"
    niigz = ReadNIFTI(file)
    0

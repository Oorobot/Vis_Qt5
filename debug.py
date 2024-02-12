from glob import glob

import cv2
import numpy as np
import SimpleITK as sitk

from utility import MedicalImage2, get_body_mask, read_dicom

# ct = read_dicom("DATA/001/CT/ImageFileName000.dcm")
# pt = read_dicom("DATA/001/PET/ImageFileName000.dcm")
# ct = ct["1.2.840.113619.2.55.3.514614471.286.1480382290.357"]["1.2.840.113619.2.55.3.514614471.286.1480382290.361.3"][
#     "(512, 512, 263)"
# ]
# pt = pt["1.2.840.113619.2.55.3.514614471.286.1480382290.357"]["1.2.840.113619.2.131.514614471.1480467840.308697"][
#     "(128, 128, 263)"
# ]

# ptct = MedicalImage2.from_ct_pt(ct, pt)

# body = get_body_mask(*ptct.to_sitk_image())
# resampled_body_array = sitk.GetArrayFromImage(body)
# x1 = 1000
# y1 = 1000
# x2 = -1
# y2 = -1
# z1 = 0
# z2 = len(resampled_body_array)
# for z, slice in enumerate(resampled_body_array):
#     contours, _ = cv2.findContours(slice.astype(np.uint8), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
#     if len(contours) == 0:
#         z1 = z
#         continue
#     for contour in contours:
#         contour = np.squeeze(contour, axis=1)
#         _x1, _y1 = np.min(contour, axis=0)
#         _x2, _y2 = np.max(contour, axis=0)
#         x1 = _x1 if _x1 < x1 else x1
#         y1 = _y1 if _y1 < y1 else y1
#         x2 = _x2 if _x2 > x2 else x2
#         y2 = _y2 if _y2 > y2 else y2
# # 裁剪的区域
# crop_index = np.array([x1, y1, z1 + 1]).tolist()
# crop_size = np.array([x2 - x1 + 1, y2 - y1 + 1, z2 - z1 - 1]).tolist()
# print(crop_index)
# print(crop_size)

crop_index = [101, 211, 1, 101, 211, 1]
crop_size = [318, 189, 262, 318, 189, 262]
size = np.array((155, 93, 430, 155, 93, 430))
bbox1 = np.array([21, 30, 246, 58, 52, 325])
bbox2 = np.array([62, 20, 383, 91, 46, 398])
n1 = (bbox1 / size) * crop_size + crop_index
n2 = (bbox2 / size) * crop_size + crop_index
print(n1.astype(np.int32))
print(n2.astype(np.int32))

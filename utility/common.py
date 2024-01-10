import colorsys

import numpy as np
import SimpleITK as sitk

np.random.seed(66)


def get_colors(num):
    assert num > 0
    colors = []
    for i in np.arange(0.0, 360.0, 360.0 / num):
        hue = i / 360
        lightness = (50 + np.random.rand() * 10) / 100.0
        saturation = (90 + np.random.rand() * 10) / 100.0
        colors.append(colorsys.hls_to_rgb(hue, lightness, saturation))
    return colors


def float_01_to_uint8_0255(array: np.ndarray):
    if array.shape[-1] == 4:
        # RGBA -> RGB
        return (np.clip(array[..., 0:3], 0, 1) * 255).round().astype(np.uint8)
    else:
        return (np.clip(array, 0, 1) * 255).round().astype(np.uint8)


# -----------------------------------------------------------#
#                      形态学分割方法
# -----------------------------------------------------------#
def get_max_component(mask_image: sitk.Image) -> sitk.Image:
    # 得到mask中的多个连通量
    cc_filter = sitk.ConnectedComponentImageFilter()
    cc_filter.SetFullyConnected(True)

    output_image = cc_filter.Execute(mask_image)

    # 计算不同连通图的大小
    lss_filter = sitk.LabelShapeStatisticsImageFilter()
    lss_filter.Execute(output_image)

    label_num = cc_filter.GetObjectCount()
    max_label = 0
    max_num = 0

    for i in range(1, label_num + 1):
        num = lss_filter.GetNumberOfPixels(i)
        if num > max_num:
            max_label = i
            max_num = num
    return sitk.Equal(output_image, max_label)


def get_binary_image(image: sitk.Image, threshold: int = -200) -> sitk.Image:
    """
    将图像进行二值化: CT threshold = -200, SUVbw threshold = 3e-2
    """
    return sitk.BinaryThreshold(image, lowerThreshold=threshold, upperThreshold=1e8)


def binary_morphological_closing(mask_image: sitk.Image, kernel_radius=2) -> sitk.Image:
    bmc_filter = sitk.BinaryMorphologicalClosingImageFilter()
    bmc_filter.SetKernelType(sitk.sitkBall)
    bmc_filter.SetKernelRadius(kernel_radius)
    bmc_filter.SetForegroundValue(1)
    return bmc_filter.Execute(mask_image)


def binary_morphological_opening(mask_image: sitk.Image, kernel_radius=2):
    bmo_filter = sitk.BinaryMorphologicalOpeningImageFilter()
    bmo_filter.SetKernelType(sitk.sitkBall)
    bmo_filter.SetKernelRadius(kernel_radius)
    bmo_filter.SetForegroundValue(1)
    return bmo_filter.Execute(mask_image)


def get_body_mask(hu_image: sitk.Image, suv_image: sitk.Image):
    # 忽略其中进行闭操作和最大连通量
    # CT(去除机床) = CT binary ∩ SUV binary; CT(去除伪影) = CT binary(去除机床) ∪ SUV binary;
    # CT(去除伪影) ≈ SUV binary
    hu_binary = get_binary_image(hu_image, -200)
    suv_binary = get_binary_image(suv_image, 3e-2)

    # 对CT进行闭操作，取最大连通量
    hu_binary_closing_max = get_max_component(binary_morphological_closing(hu_binary))
    # 对SUV进行闭操作，取最大连通量
    suv_binary_closing_max = get_max_component(binary_morphological_closing(suv_binary))

    mask_body = sitk.And(hu_binary_closing_max, suv_binary_closing_max)
    # 取最大连通量
    # mask_body_max = get_max_component(mask_body)

    # 使用超大半径的闭操作，消除伪影
    mask_body_closing = binary_morphological_closing(mask_body, 20)
    return mask_body_closing

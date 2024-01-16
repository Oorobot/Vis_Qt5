import colorsys
import json
from typing import List, Tuple

import cv2
import numpy as np
import SimpleITK as sitk
from matplotlib.cm import get_cmap
from vtkmodules.util.vtkImageImportFromArray import vtkImageImportFromArray
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkPiecewiseFunction, vtkPolyData
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkColorTransferFunction,
    vtkPolyDataMapper,
    vtkTextActor3D,
    vtkVolume,
    vtkVolumeProperty,
)
from vtkmodules.vtkRenderingVolume import vtkFixedPointVolumeRayCastMapper

from .constant import LABEL_TO_NAME

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


# -----------------------------------------------------------#
#                      三维可视化方法
# -----------------------------------------------------------#


def volume_ct(array: np.ndarray, origin: tuple, spacing: tuple, body_array: np.ndarray = None) -> vtkVolume:
    # 保留身体部分
    if body_array is not None:
        array = array * body_array + -1000 * (1 - body_array)

    # 创建 vtk 图像
    vtk_image = vtkImageImportFromArray()
    vtk_image.SetArray(array.astype(np.float64))
    vtk_image.SetDataOrigin(origin)
    vtk_image.SetDataSpacing(spacing)
    vtk_image.Update()

    # 体积将通过光线投射alpha合成显示，需要光线投射映射器来进行光线投射
    mapper = vtkFixedPointVolumeRayCastMapper()
    mapper.SetInputConnection(vtk_image.GetOutputPort())

    # 使用颜色转换函数，对不同的值设置不同的函数
    color = vtkColorTransferFunction()
    cmap = get_cmap("gray")
    cmap = cmap(np.linspace(0, 1, cmap.N))
    x = np.linspace(-450, 1050, 256)
    [color.AddRGBPoint(_x, *rgba[:3]) for _x, rgba in zip(x, cmap)]

    # 使用透明度转换函数，用于控制不同组织之间的透明度
    scalar_opacity = vtkPiecewiseFunction()
    scalar_opacity.AddPoint(0, 0.00)
    scalar_opacity.AddPoint(200, 0.25)
    scalar_opacity.AddPoint(500, 0.45)
    scalar_opacity.AddPoint(1000, 0.65)
    scalar_opacity.AddPoint(1150, 0.90)

    # 梯度不透明度函数用于降低体积“平坦”区域的不透明度，同时保持组织类型之间边界的不透明度。梯度是以强度在单位距离上的变化量来测量的。
    gradient_opacity = vtkPiecewiseFunction()
    gradient_opacity.AddPoint(0, 0.00)
    gradient_opacity.AddPoint(90, 0.5)
    gradient_opacity.AddPoint(100, 1.0)

    property = vtkVolumeProperty()
    property.SetColor(color)
    property.SetScalarOpacity(scalar_opacity)
    property.SetGradientOpacity(gradient_opacity)
    property.SetInterpolationTypeToLinear()
    property.ShadeOn()
    # 环境光系数表示各种光线照射到物体材质上，经过很多次发射后最终在环境中的光线强度
    property.SetAmbient(0.4)
    # 漫反射光系数表示光线照射到物体材质上，经过漫反射后形成的光线强度
    property.SetDiffuse(0.6)
    # 镜反射系数表示光线照射到物体材质上，经过镜面反射后形成的光线强度
    property.SetSpecular(0.2)

    volume = vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(property)

    return volume


def volume_pt(
    array: np.ndarray, origin: tuple, spacing: tuple, body_array: np.ndarray = None, ma: float = 5.0
) -> vtkVolume:
    # 保留身体部分
    if body_array is not None:
        array = array * body_array + array * (1 - body_array)

    vtk_image = vtkImageImportFromArray()
    vtk_image.SetArray(array.astype(np.float64))
    vtk_image.SetDataOrigin(origin)
    vtk_image.SetDataSpacing(spacing)
    vtk_image.Update()

    mapper = vtkFixedPointVolumeRayCastMapper()
    mapper.SetInputConnection(vtk_image.GetOutputPort())

    color = vtkColorTransferFunction()
    cmap = get_cmap("hot")
    cmap = cmap(np.linspace(0, 1, cmap.N))
    x = np.linspace(0, ma, 256)
    [color.AddRGBPoint(_x, *rgba[:3]) for _x, rgba in zip(x, cmap)]

    scalar_opacity = vtkPiecewiseFunction()
    scalar_opacity.AddPoint(0, 0.00)
    scalar_opacity.AddPoint(1.0, 0.25)
    scalar_opacity.AddPoint(2.5, 0.45)
    scalar_opacity.AddPoint(0.60 * ma, 0.80)
    scalar_opacity.AddPoint(0.90 * ma, 0.95)

    gradient_opacity = vtkPiecewiseFunction()
    gradient_opacity.AddPoint(0, 0.00)
    gradient_opacity.AddPoint(0.6 * ma, 0.4)
    gradient_opacity.AddPoint(0.9 * ma, 1.0)

    property = vtkVolumeProperty()
    property.SetColor(color)
    property.SetScalarOpacity(scalar_opacity)
    property.SetGradientOpacity(gradient_opacity)
    property.SetInterpolationTypeToLinear()
    property.ShadeOn()
    property.SetAmbient(0.4)
    property.SetDiffuse(0.6)
    property.SetSpecular(0.2)

    volume = vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(property)

    return volume


def bbox(
    point1: List[int],
    point2: List[int],
    origin: Tuple[float],
    spacing: Tuple[float],
    text: str,
    color: Tuple[float],
    opacity: float,
):
    x1, y1, z1 = [o + (p + 1) * s for o, p, s in zip(origin, point1, spacing)]
    x2, y2, z2 = [o + (p + 1) * s for o, p, s in zip(origin, point2, spacing)]
    points = vtkPoints()
    points.SetNumberOfPoints(8)
    points.SetPoint(0, x1, y1, z1)
    points.SetPoint(1, x1, y2, z1)
    points.SetPoint(2, x2, y2, z1)
    points.SetPoint(3, x2, y1, z1)
    points.SetPoint(4, x1, y1, z2)
    points.SetPoint(5, x1, y2, z2)
    points.SetPoint(6, x2, y2, z2)
    points.SetPoint(7, x2, y1, z2)
    # 连接
    lines = vtkCellArray()
    lines.InsertNextCell(5)
    lines.InsertCellPoint(0)
    lines.InsertCellPoint(1)
    lines.InsertCellPoint(2)
    lines.InsertCellPoint(3)
    lines.InsertCellPoint(0)
    lines.InsertNextCell(5)
    lines.InsertCellPoint(4)
    lines.InsertCellPoint(5)
    lines.InsertCellPoint(6)
    lines.InsertCellPoint(7)
    lines.InsertCellPoint(4)
    lines.InsertNextCell(2)
    lines.InsertCellPoint(0)
    lines.InsertCellPoint(4)
    lines.InsertNextCell(2)
    lines.InsertCellPoint(1)
    lines.InsertCellPoint(5)
    lines.InsertNextCell(2)
    lines.InsertCellPoint(2)
    lines.InsertCellPoint(6)
    lines.InsertNextCell(2)
    lines.InsertCellPoint(3)
    lines.InsertCellPoint(7)

    cube = vtkPolyData()  # 多边形
    cube.SetPoints(points)
    cube.SetLines(lines)

    cube_mapper = vtkPolyDataMapper()
    cube_mapper.SetInputData(cube)
    cube_mapper.Update()

    cube_actor = vtkActor()
    cube_actor.SetMapper(cube_mapper)
    cube_actor.GetProperty().SetColor(*color)
    cube_actor.GetProperty().SetOpacity(opacity)

    # 文本
    text_actor = vtkTextActor3D()
    text_actor.SetInput(text)
    text_actor.SetPosition(x2, y1, z2)
    text_actor.RotateX(90)
    text_property = text_actor.GetTextProperty()
    text_property.SetColor(*color)
    text_property.SetFontSize(28)
    text_property.SetOpacity(opacity)
    text_property.SetJustificationToCentered()
    return cube_actor, text_actor


def nifti_to_labels(nifti_path: str):
    """
    读取itk-snap软件标注的数据，转换为边界框标注信息。
    :param array: 三维数组
    :return 类别 [c1, ...] 和 三维边界框 [(x1, y1, z1, x2, y2, z2), ...]\n
    3D Bounding Box
            •------------------•
           /¦                 /¦
          / ¦                / ¦
         /  ¦               /  ¦
        •------------------V2  ¦
        ¦   ¦              ¦   ¦
        ¦   ¦              ¦   ¦
        ¦   ¦              ¦   ¦
        ¦   ¦              ¦   ¦
        ¦   ¦              ¦   ¦           z
        ¦   V1-------------¦---•           ⋮
        ¦  /               ¦  /            o ⋯ x
        ¦ /                ¦ /           ⋰
        ¦/                 ¦/           y
        •------------------•
    """
    array = sitk.GetArrayFromImage(sitk.ReadImage(nifti_path))
    num_classes = array.max()
    classes, points = [], []
    for c in range(1, num_classes + 1):
        c_array = np.where(array == c, 1, 0)
        c_array = c_array.astype(np.uint8)
        # 沿着 z 轴遍历
        for z, a in enumerate(c_array):
            if 0 == np.amax(a):
                continue
            # 在 xy 平面上找标注
            contour_xy, _ = cv2.findContours(a, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            for c_xy in contour_xy:
                c_xy = c_xy[:, 0, :]
                assert len(c_xy) == 4, f"[ERROR] ({c_xy[0, 0]}, {c_xy[0, 1]}, {z})处存在不规整的标注."
                x1, y1 = c_xy[0]
                x2, y2 = c_xy[2]

                # 根据 x1 找到相应的 yz 平面标注
                contour_yz, _ = cv2.findContours(c_array[:, :, x1], cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

                for c_yz in contour_yz:  # 遍历找到的 yz 标注
                    c_yz = c_yz[:, 0, :]
                    assert len(c_yz) == 4, f"[ERROR] ({x1}, {c_yz[0,0]}, {c_yz[0,1]})处存在不规整的标注."

                    y1_, z1 = c_yz[0]
                    y2_, z2 = c_yz[2]

                    if y1 == y1_ and y2 == y2_:
                        classes.append(LABEL_TO_NAME[c])
                        points.append([int(x1), int(y1), int(z1), int(x2), int(y2), int(z2)])
                        # 清除已找到的标注
                        c_array[z1 : z2 + 1, y1 : y2 + 1, x1 : x2 + 1] = 0
                        break
    return classes, points


def json_to_labels(json_path: str):
    print('[INFO] a list should be in json, e.g. [{"class_name": xxx, "bbox": [x1, y1, z1, x2, y2, z2]}]')
    label_json = json.load(open(json_path, "r"))
    classes, points = [], []
    for label in label_json:
        classes.append(label["class_name"])
        points.append(label["bbox"])
    return classes, points


if __name__ == "__main__":
    import SimpleITK as sitk

    labelArray = sitk.GetArrayFromImage(sitk.ReadImage(r"DATA\001_Label_Object.nii.gz"))
    points = nifti_to_labels(labelArray)
    0

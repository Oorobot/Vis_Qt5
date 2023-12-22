from typing import List, Tuple

import cv2
import numpy as np
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


def volumeCT(array: np.ndarray, origin: tuple, spacing: tuple, bodyArray: np.ndarray = None) -> vtkVolume:
    # 保留身体部分
    if bodyArray is not None:
        array = array * bodyArray + -1000 * (1 - bodyArray)

    # 创建 vtk 图像
    vtkImage = vtkImageImportFromArray()
    vtkImage.SetArray(array.astype(np.int16))
    vtkImage.SetDataOrigin(origin)
    vtkImage.SetDataSpacing(spacing)
    vtkImage.Update()

    # 体积将通过光线投射alpha合成显示，需要光线投射映射器来进行光线投射
    mapper = vtkFixedPointVolumeRayCastMapper()
    mapper.SetInputConnection(vtkImage.GetOutputPort())

    # 使用颜色转换函数，对不同的值设置不同的函数
    color = vtkColorTransferFunction()
    cmap = get_cmap("gray")
    cmap = cmap(np.linspace(0, 1, cmap.N))
    x = np.linspace(-450, 1050, 256)
    [color.AddRGBPoint(_x, *rgba[:3]) for _x, rgba in zip(x, cmap)]

    # 使用透明度转换函数，用于控制不同组织之间的透明度
    scalarOpacity = vtkPiecewiseFunction()
    scalarOpacity.AddPoint(0, 0.00)
    scalarOpacity.AddPoint(200, 0.25)
    scalarOpacity.AddPoint(500, 0.45)
    scalarOpacity.AddPoint(1000, 0.65)
    scalarOpacity.AddPoint(1150, 0.90)

    # 梯度不透明度函数用于降低体积“平坦”区域的不透明度，同时保持组织类型之间边界的不透明度。梯度是以强度在单位距离上的变化量来测量的。
    gradientOpacity = vtkPiecewiseFunction()
    gradientOpacity.AddPoint(0, 0.00)
    gradientOpacity.AddPoint(90, 0.5)
    gradientOpacity.AddPoint(100, 1.0)

    property = vtkVolumeProperty()
    property.SetColor(color)
    property.SetScalarOpacity(scalarOpacity)
    property.SetGradientOpacity(gradientOpacity)
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


def volumePT(
    array: np.ndarray, origin: tuple, spacing: tuple, bodyArray: np.ndarray = None, ma: float = 5.0
) -> vtkVolume:
    # 保留身体部分
    if bodyArray is not None:
        array = array * bodyArray + array * (1 - bodyArray)

    vtkImage = vtkImageImportFromArray()
    vtkImage.SetArray(array)
    vtkImage.SetDataOrigin(origin)
    vtkImage.SetDataSpacing(spacing)
    vtkImage.Update()

    mapper = vtkFixedPointVolumeRayCastMapper()
    mapper.SetInputConnection(vtkImage.GetOutputPort())

    color = vtkColorTransferFunction()
    cmap = get_cmap("hot")
    cmap = cmap(np.linspace(0, 1, cmap.N))
    x = np.linspace(0, ma, 256)
    [color.AddRGBPoint(_x, *rgba[:3]) for _x, rgba in zip(x, cmap)]

    scalarOpacity = vtkPiecewiseFunction()
    scalarOpacity.AddPoint(0.10 * ma, 0.00)
    scalarOpacity.AddPoint(0.30 * ma, 0.25)
    scalarOpacity.AddPoint(0.80 * ma, 0.65)
    scalarOpacity.AddPoint(0.95 * ma, 0.80)

    gradientOpacity = vtkPiecewiseFunction()
    gradientOpacity.AddPoint(0, 0.00)
    gradientOpacity.AddPoint(0.6 * ma, 0.5)
    gradientOpacity.AddPoint(0.9 * ma, 1.0)

    property = vtkVolumeProperty()
    property.SetColor(color)
    property.SetScalarOpacity(scalarOpacity)
    property.SetGradientOpacity(gradientOpacity)
    property.SetInterpolationTypeToLinear()
    property.ShadeOn()
    property.SetAmbient(0.4)
    property.SetDiffuse(0.6)
    property.SetSpecular(0.2)

    volume = vtkVolume()
    volume.SetMapper(mapper)
    volume.SetProperty(property)

    return volume


def BoundingBox(
    point1: List[int],
    point2: List[int],
    origin: Tuple[float],
    spacing: Tuple[float],
    color: Tuple[float],
    text: str,
    opacity: float,
):
    x1, y1, z1 = [o + p * s for o, p, s in zip(origin, point1, spacing)]
    x2, y2, z2 = [o + p * s for o, p, s in zip(origin, point2, spacing)]
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

    cubeMapper = vtkPolyDataMapper()
    cubeMapper.SetInputData(cube)
    cubeMapper.Update()

    cubeActor = vtkActor()
    cubeActor.SetMapper(cubeMapper)
    cubeActor.GetProperty().SetColor(*color)
    cubeActor.GetProperty().SetOpacity(opacity)

    # 文本
    textActor = vtkTextActor3D()
    textActor.SetInput(text)
    textActor.SetPosition(x2, y2, z2)
    textProperty = textActor.GetTextProperty()
    textProperty.SetColor(*color)
    textProperty.SetFontSize(28)
    textProperty.SetOpacity(opacity)

    return cubeActor, textActor


def labelToPoints(array: np.ndarray):
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
                        classes.append(c)
                        points.append([(int(x1), int(y1), int(z1)), (int(x2), int(y2), int(z2))])
                        # 清除已找到的标注
                        c_array[z1 : z2 + 1, y1 : y2 + 1, x1 : x2 + 1] = 0
                        break
    return classes, points


if __name__ == "__main__":
    import SimpleITK as sitk

    labelArray = sitk.GetArrayFromImage(sitk.ReadImage(r"DATA\001_Label_Object.nii.gz"))
    points = labelToPoints(labelArray)
    0

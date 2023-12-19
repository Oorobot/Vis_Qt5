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


VIEW_INT = {"s": 0, "c": 1, "t": 2}
VIEW_NAME = {"s": "矢状面", "c": "冠状面", "t": "横截面"}

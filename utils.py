import os
from datetime import datetime
from glob import glob
from typing import Tuple

import cv2
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

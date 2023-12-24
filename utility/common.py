import colorsys

import numpy as np

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
    assert 0 <= array.min() and array.max() <= 1
    if array.shape[-1] == 4:
        # RGBA -> RGB
        return np.clip((array[..., 0:3] * 255).round(), 0, 255).astype(np.uint8)
    else:
        return np.clip((array * 255).round(), 0, 255).astype(np.uint8)

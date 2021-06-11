# Based on https://github.com/gsnedders/wcag-contrast-ratio
# Copyright (c) 2015 Geoffrey Sneddon
# Copyright (c) 2019 Tulir Asokan
# MIT license
from typing import Tuple

RGB = Tuple[float, float, float]


def hex_to_rgb(color: str) -> RGB:
    color = color.lstrip("#")
    if len(color) != 3 and len(color) != 6:
        raise ValueError("Invalid hex length")
    step = 1 if len(color) == 3 else 2
    try:
        r = int(color[0:step], 16)
        g = int(color[step:2 * step], 16)
        b = int(color[2 * step:3 * step], 16)
    except ValueError as e:
        raise ValueError("Invalid hex value") from e
    return r / 255, g / 255, b / 255


def rgb_to_hex(rgb: RGB) -> str:
    r, g, b = rgb
    r = int(r * 255)
    g = int(g * 255)
    b = int(b * 255)
    return f"{r:02x}{g:02x}{b:02x}"


def contrast(rgb1: RGB, rgb2: RGB) -> float:
    for r, g, b in (rgb1, rgb2):
        if not 0.0 <= r <= 1.0:
            raise ValueError(f"r {r} is out of valid range (0.0 - 1.0)")
        if not 0.0 <= g <= 1.0:
            raise ValueError(f"g {g} is out of valid range (0.0 - 1.0)")
        if not 0.0 <= b <= 1.0:
            raise ValueError(f"b {b} is out of valid range (0.0 - 1.0)")

    l1 = _relative_luminance(*rgb1)
    l2 = _relative_luminance(*rgb2)

    if l1 > l2:
        return (l1 + 0.05) / (l2 + 0.05)
    else:
        return (l2 + 0.05) / (l1 + 0.05)


def _relative_luminance(r: float, g: float, b: float) -> float:
    r = _linearize(r)
    g = _linearize(g)
    b = _linearize(b)

    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _linearize(v: float) -> float:
    if v <= 0.03928:
        return v / 12.92
    else:
        return ((v + 0.055) / 1.055) ** 2.4

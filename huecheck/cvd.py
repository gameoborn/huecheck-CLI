"""Simple Machado-style linear RGB simulations of common color vision deficiency."""
from __future__ import annotations

from .contrast import RGB

# Approximate severity-1.0 matrices. Applied in linear-light RGB, then encoded to sRGB.
MATRICES = {
    "protanopia": ((0.152286, 1.052583, -0.204868), (0.114503, 0.786281, 0.099216), (-0.003882, -0.048116, 1.051998)),
    "deuteranopia": ((0.367322, 0.860646, -0.227968), (0.280085, 0.672501, 0.047413), (-0.011820, 0.042940, 0.968881)),
    "tritanopia": ((1.255528, -0.076749, -0.178779), (-0.078411, 0.930809, 0.147602), (0.004733, 0.691367, 0.303900)),
}


def _linear(c: int) -> float:
    x = c / 255
    return x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4


def _srgb(c: float) -> int:
    c = max(0.0, min(1.0, c))
    x = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return round(x * 255)


def simulate(rgb: RGB, deficiency: str) -> RGB:
    """Return an approximate simulated RGB color for a named deficiency."""
    try:
        matrix = MATRICES[deficiency.lower()]
    except KeyError as exc:
        raise ValueError(f"unknown color vision deficiency: {deficiency}") from exc
    source = tuple(_linear(c) for c in rgb)
    return tuple(_srgb(sum(row[i] * source[i] for i in range(3))) for row in matrix)  # type: ignore[return-value]


def delta_e_rgb(a: RGB, b: RGB) -> float:
    """Fast Euclidean distance in CIE Lab (D65), a practical deltaE76 approximation."""
    def lab(rgb: RGB) -> tuple[float, float, float]:
        r, g, bl = (_linear(v) for v in rgb)
        x = (0.4124564*r + 0.3575761*g + 0.1804375*bl) / 0.95047
        y = 0.2126729*r + 0.7151522*g + 0.0721750*bl
        z = (0.0193339*r + 0.1191920*g + 0.9503041*bl) / 1.08883
        def f(t: float) -> float:
            return t ** (1/3) if t > 0.008856 else 7.787*t + 16/116
        fx, fy, fz = f(x), f(y), f(z)
        return (116*fy-16, 500*(fx-fy), 200*(fy-fz))
    la, lb = lab(a), lab(b)
    return sum((x-y)**2 for x, y in zip(la, lb)) ** 0.5

"""Estimación de distancia por la altura del recuadro.

Modelo pinhole: distancia = K / (alto_recuadro / alto_frame)
K se calibra por clase con calibrar.py (una medición a distancia conocida).
Ojo: la relación es INVERSA, por eso no se interpola linealmente entre dos distancias.
"""
import json
import os

import config

_K = {}


def load_calibration() -> dict:
    global _K
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config.CALIBRATION_FILE)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            _K = json.load(f)
    return _K


load_calibration()


def height_ratio(det, frame_h: int) -> float:
    return max(det.y2 - det.y1, 1) / frame_h


def is_truncated(det, frame_h: int, margin: int = 3) -> bool:
    """Recuadro cortado por el borde vertical: su altura real es MAYOR que la medida."""
    return det.y1 <= margin or det.y2 >= frame_h - margin


def estimate_distance(det, frame_h: int):
    """Metros, o None si la clase no está calibrada."""
    k = _K.get(det.name)
    if k is None:
        return None
    return k / height_ratio(det, frame_h)

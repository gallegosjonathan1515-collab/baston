"""Exporta YOLOv8n para la Raspberry Pi. Ejecutar (idealmente en la propia Pi):
    python exportar_modelo.py ncnn     -> carpeta yolov8n_ncnn_model
    python exportar_modelo.py onnx     -> yolov8n.onnx
Luego pon MODEL_PATH en config.py con la ruta resultante y compara FPS de ambos.
"""
import sys

from ultralytics import YOLO

import config

fmt = sys.argv[1] if len(sys.argv) > 1 else "ncnn"
path = YOLO("yolov8n.pt").export(format=fmt, imgsz=config.IMGSZ)
print("Modelo exportado en:", path)

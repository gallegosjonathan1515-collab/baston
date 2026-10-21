"""Calibra la distancia por clase.

Uso:
    python calibrar.py --dist 1.5
1) Coloca el objeto (o ponte tú) a EXACTAMENTE esa distancia de la cámara, de cuerpo/objeto completo
   (el recuadro NO debe tocar los bordes de arriba/abajo).
2) Pulsa  c  para guardar una muestra del objeto más grande detectado. Repite varias veces.
3) Cambia de distancia (cierra y vuelve a abrir con otro --dist) para verificar.
4) Pulsa  q  para guardar calibration.json y salir.
"""
import argparse
import json
import os
import statistics

import cv2

import config
import distance
from camera import CameraStream
from detector import Detector

ap = argparse.ArgumentParser()
ap.add_argument("--dist", type=float, required=True, help="distancia real en metros")
args = ap.parse_args()

cam = CameraStream(config.CAMERA_INDEX, config.FRAME_W, config.FRAME_H).start()
detector = Detector()
samples = {}
last_id = -1
msg = "c = guardar muestra | q = guardar y salir"

try:
    while True:
        fid, frame = cam.read()
        if frame is None or fid == last_id:
            continue
        last_id = fid
        h, w = frame.shape[:2]
        dets = detector.detect(frame)
        target = max(dets, key=lambda d: d.area, default=None)

        for d in dets:
            r = distance.height_ratio(d, h)
            cv2.rectangle(frame, (d.x1, d.y1), (d.x2, d.y2), (255, 255, 0), 2)
            cv2.putText(frame, f"{d.name} alto={r:.2f}", (d.x1, max(d.y1 - 6, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
        cv2.putText(frame, f"dist real = {args.dist} m | {msg}", (8, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.imshow("Calibracion", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("c") and target:
            if distance.is_truncated(target, h):
                msg = "RECUADRO CORTADO por el borde: aleja el objeto"
            else:
                k = args.dist * distance.height_ratio(target, h)
                samples.setdefault(target.name, []).append(k)
                msg = f"{target.name}: K={k:.3f} ({len(samples[target.name])} muestras)"
                print(msg)
        elif key == ord("q"):
            break
finally:
    cam.stop()
    cv2.destroyAllWindows()

if samples:
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config.CALIBRATION_FILE)
    data = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    for name, ks in samples.items():
        data[name] = round(statistics.median(ks), 4)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Guardado en {path}: {data}")
else:
    print("No se guardó ninguna muestra.")

"""Diagnóstico: busca qué índice y backend de cámara funcionan en tu PC.
Ejecuta:  python test_camera.py
"""
import sys
import cv2

backends = [("DSHOW", cv2.CAP_DSHOW), ("MSMF", cv2.CAP_MSMF), ("AUTO", cv2.CAP_ANY)] \
    if sys.platform == "win32" else [("AUTO", cv2.CAP_ANY)]

found = []
for index in range(5):
    for name, backend in backends:
        cap = cv2.VideoCapture(index, backend)
        ok = False
        if cap.isOpened():
            for _ in range(20):
                ok, frame = cap.read()
                if ok and frame is not None:
                    break
        cap.release()
        print(f"índice {index} | {name:5s} | {'FUNCIONA' if ok else 'no'}")
        if ok:
            found.append((index, name))

print()
if found:
    print("Cámaras que funcionan:", found)
    print(f"Pon CAMERA_INDEX = {found[0][0]} en config.py")
else:
    print("Ninguna cámara entregó imagen. Revisa permisos de Windows y apps que usen la cámara.")

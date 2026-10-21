"""Captura de video en un hilo propio: siempre entrega el frame más reciente.

En Windows prueba varios backends (DSHOW, MSMF, automático) porque la cámara
suele fallar con uno y funcionar con otro.
"""
import sys
import threading
import time

import cv2


def _backends():
    if sys.platform == "win32":
        return [("DSHOW", cv2.CAP_DSHOW), ("MSMF", cv2.CAP_MSMF), ("AUTO", cv2.CAP_ANY)]
    return [("AUTO", cv2.CAP_ANY)]


def open_camera(index: int, width: int, height: int):
    for name, backend in _backends():
        cap = cv2.VideoCapture(index, backend)
        if not cap.isOpened():
            cap.release()
            continue
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        # Verifica que realmente entregue imagen (a veces abre pero no da frames)
        for _ in range(20):
            ok, frame = cap.read()
            if ok and frame is not None:
                print(f"[camara] índice {index} abierta con backend {name}")
                return cap
            time.sleep(0.05)
        cap.release()
    raise RuntimeError(
        f"No se pudo abrir la cámara {index}. Corre test_camera.py para ver qué índice funciona."
    )


class CameraStream:
    def __init__(self, index: int, width: int, height: int):
        self.cap = open_camera(index, width, height)
        self._frame = None
        self._frame_id = 0
        self._lock = threading.Lock()
        self._running = False
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self._running = True
        self._thread.start()
        return self

    def _loop(self):
        while self._running:
            ok, frame = self.cap.read()
            if not ok:
                time.sleep(0.01)
                continue
            with self._lock:
                self._frame = frame
                self._frame_id += 1

    def read(self):
        """Devuelve (id_del_frame, frame). El id permite saltarse frames ya procesados."""
        with self._lock:
            return self._frame_id, self._frame

    def stop(self):
        self._running = False
        self._thread.join(timeout=1)
        self.cap.release()

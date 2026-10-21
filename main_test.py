"""Visión sin hardware: cámara + YOLO/ByteTrack + zonas + comando háptico.
Ejecuta:  python main_test.py     (tecla q para salir)
"""
import time

import cv2

import config
import distance
import haptics
import zones
from camera import CameraStream
from detector import Detector
from persistence import DetectionMemory

COLORS = {0: (90, 90, 90), 1: (0, 200, 0), 2: (0, 200, 255), 3: (0, 0, 255)}


def draw(frame, detections, levels, cmd, fps):
    h, w = frame.shape[:2]
    for name, (x1, x2) in zones.zone_bounds(w).items():
        cv2.rectangle(frame, (x1, 0), (x2, h), COLORS[levels[name]], 2)
        cv2.putText(frame, f"{name}:{levels[name]}", (x1 + 8, 24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, COLORS[levels[name]], 2)
    for d in detections:
        dist = distance.estimate_distance(d, h)
        info = f"{dist:.1f}m" if dist is not None else f"area={d.area / (w * h):.2f}"
        tid = f"#{d.track_id}" if d.track_id is not None else ""
        color = (150, 150, 150) if d.ghost else (255, 255, 0)
        cv2.rectangle(frame, (d.x1, d.y1), (d.x2, d.y2), color, 2)
        cv2.putText(frame, f"{d.name}{tid} {d.conf:.2f} {info}", (d.x1, max(d.y1 - 6, 12)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
    cv2.putText(frame, f"FPS {fps:.1f} | CMD {haptics.encode(cmd).strip()}", (8, h - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)


def main():
    cam = CameraStream(config.CAMERA_INDEX, config.FRAME_W, config.FRAME_H).start()
    detector = Detector()
    memory = DetectionMemory()
    smoother = haptics.Smoother()
    last_id, last_cmd, fps = -1, None, 0.0

    try:
        while True:
            frame_id, frame = cam.read()
            if frame is None or frame_id == last_id:
                time.sleep(0.001)
                continue
            last_id = frame_id
            t0 = time.perf_counter()

            h, w = frame.shape[:2]
            detections = memory.update(detector.detect(frame))
            levels = zones.analyze(detections, w, h)
            cmd = smoother.update(haptics.guidance_from_zones(levels))

            if cmd != last_cmd:
                print(haptics.encode(cmd).strip())
                last_cmd = cmd

            fps = 0.9 * fps + 0.1 * (1 / max(time.perf_counter() - t0, 1e-6))
            draw(frame, detections, levels, cmd, fps)
            cv2.imshow("Baston - vision", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        cam.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

"""Sistema completo: cámara -> YOLO -> zonas -> háptico -> serial.
Uso:
    python main.py --port COM3            (Windows)
    python main.py --port /dev/ttyUSB0    (Linux / Raspberry Pi)
    python main.py --no-serial            (solo visión, sin hardware)
    python main.py --port COM3 --no-display   (sin ventana, para la Raspberry Pi)
"""
import argparse
import time

import cv2

import config
import haptics
import zones
from camera import CameraStream
from detector import Detector
from persistence import DetectionMemory
from main_test import draw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", help="puerto serial del Arduino/ESP32")
    ap.add_argument("--no-serial", action="store_true")
    ap.add_argument("--no-display", action="store_true")
    args = ap.parse_args()

    link = None
    if not args.no_serial:
        if not args.port:
            ap.error("indica --port o usa --no-serial")
        from serial_link import SerialLink
        link = SerialLink(args.port).start()

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

            if link:
                link.send(haptics.encode(cmd))
            if cmd != last_cmd:
                print(haptics.encode(cmd).strip())
                last_cmd = cmd

            fps = 0.9 * fps + 0.1 * (1 / max(time.perf_counter() - t0, 1e-6))
            if not args.no_display:
                draw(frame, detections, levels, cmd, fps)
                cv2.imshow("Baston - vision", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except KeyboardInterrupt:
        pass
    finally:
        cam.stop()
        if link:
            link.stop()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

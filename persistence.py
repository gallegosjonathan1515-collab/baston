"""Memoria corta de objetos: si el modelo pierde un objeto UN instante, se conserva
unos frames como "fantasma". (ByteTrack mantiene IDs, pero no devuelve cajas de objetos
no detectados en el frame actual; esto cubre ese hueco.)"""
import dataclasses

import config


class DetectionMemory:
    def __init__(self, ghost_frames: int = config.GHOST_FRAMES):
        self.ghost_frames = ghost_frames
        self._tracks = {}  # id -> [ultima_deteccion, frames_perdido]

    def update(self, detections):
        out, seen = [], set()
        for d in detections:
            out.append(d)
            if d.track_id is not None:
                seen.add(d.track_id)
                self._tracks[d.track_id] = [d, 0]

        for tid in list(self._tracks):
            if tid in seen:
                continue
            self._tracks[tid][1] += 1
            if self._tracks[tid][1] > self.ghost_frames:
                del self._tracks[tid]
            else:
                out.append(dataclasses.replace(self._tracks[tid][0], ghost=True))
        return out

"""División espacial en 3 zonas y nivel de urgencia por zona."""
import config
import distance


def zone_bounds(frame_w: int) -> dict:
    a = int(frame_w * config.ZONE_SPLIT[0])
    b = int(frame_w * config.ZONE_SPLIT[1])
    return {"L": (0, a), "C": (a, b), "R": (b, frame_w)}


def urgency(det, frame_w: int, frame_h: int) -> int:
    """0 = ignorar, 1 = lejos, 2 = precaución, 3 = peligro.

    Si la clase está calibrada usa DISTANCIA (por altura del recuadro);
    si no, cae al método anterior por porcentaje de área.
    """
    dist = distance.estimate_distance(det, frame_h)
    if dist is not None:
        if config.TRUNCATED_IS_NEAR and distance.is_truncated(det, frame_h):
            return 3
        if dist <= config.NEAR_M:
            return 3
        if dist <= config.MID_M:
            return 2
        if dist <= config.MAX_RANGE_M:
            return 1
        return 0

    ratio = det.area / (frame_w * frame_h)
    if ratio >= config.NEAR_RATIO:
        return 3
    if ratio >= config.MID_RATIO:
        return 2
    return 1


def analyze(detections, frame_w: int, frame_h: int) -> dict:
    """{'L': nivel, 'C': nivel, 'R': nivel}. Un objeto grande puede ocupar varias zonas."""
    levels = {"L": 0, "C": 0, "R": 0}
    bounds = zone_bounds(frame_w)
    for d in detections:
        u = urgency(d, frame_w, frame_h)
        if u == 0:
            continue
        box_w = max(d.x2 - d.x1, 1)
        for zone, (zx1, zx2) in bounds.items():
            overlap = min(d.x2, zx2) - max(d.x1, zx1)
            if overlap > 0 and overlap / box_w >= config.MIN_OVERLAP:
                levels[zone] = max(levels[zone], u)
    return levels

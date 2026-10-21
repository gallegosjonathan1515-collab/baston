"""Traduce zonas ocupadas -> comando háptico (lógica inversa) + anti-parpadeo.

Protocolo serial (texto, una línea por comando):
    L:<0-3>,R:<0-3>,C:<0-3>\n
  L = intensidad del motor izquierdo, R = motor derecho, C = alerta frontal
  0 = apagado, 1 = aviso, 2 = precaución, 3 = peligro / detenerse
El PATRÓN de vibración lo ejecuta el microcontrolador.
"""
import config


def guidance_from_zones(levels: dict) -> dict:
    l, c, r = levels["L"], levels["C"], levels["R"]

    # Todo ocupado: no hay por dónde esquivar -> detenerse (solo alerta frontal).
    if l and c and r:
        return {"L": 0, "R": 0, "C": max(l, c, r, 2)}

    # Ambos lados ocupados pero el centro LIBRE: se puede avanzar de frente.
    # Una guía lateral sería contradictoria, así que se cancela.
    if l and r and not c:
        return {"L": 0, "R": 0, "C": config.NARROW_PASSAGE_C_LEVEL}

    # Caso normal: lógica inversa (izquierda -> motor derecho, derecha -> motor izquierdo)
    return {"L": r, "R": l, "C": c}


class Smoother:
    """Evita vibraciones por falsos positivos de un solo frame."""

    def __init__(self, rise=config.FRAMES_TO_RISE, fall=config.FRAMES_TO_FALL):
        self.rise, self.fall = rise, fall
        self.out = {"L": 0, "C": 0, "R": 0}
        self._cand = dict(self.out)
        self._count = dict(self.out)

    def update(self, raw: dict) -> dict:
        for k, v in raw.items():
            if v == self.out[k]:
                self._count[k] = 0
                continue
            if v == self._cand[k]:
                self._count[k] += 1
            else:
                self._cand[k], self._count[k] = v, 1
            needed = self.rise if v > self.out[k] else self.fall
            if self._count[k] >= needed:
                self.out[k], self._count[k] = v, 0
        return dict(self.out)


def encode(cmd: dict) -> str:
    return f"L:{cmd['L']},R:{cmd['R']},C:{cmd['C']}\n"

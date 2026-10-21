"""Configuración central del módulo de visión del Bastón Inteligente."""

# --- Cámara ---
CAMERA_INDEX = 0
FRAME_W = 640
FRAME_H = 480

# --- Modelo ---
MODEL_PATH = "yolov8n.pt"   # luego: exportar a NCNN para la Raspberry Pi
IMGSZ = 320                 # más chico = más FPS (320 o 416 son buenos puntos de partida)
CONF = 0.45

# Clases COCO relevantes para obstáculos (ajústalas a tu entorno)
ALLOWED_CLASSES = [
    0,   # person
    1,   # bicycle
    2,   # car
    3,   # motorcycle
    5,   # bus
    7,   # truck
    9,   # traffic light
    10,  # fire hydrant
    11,  # stop sign
    13,  # bench
    16,  # dog
    56,  # chair
    57,  # couch
    58,  # potted plant
    59,  # bed
    60,  # dining table
    62,  # tv
]

# --- Zonas ---
ZONE_SPLIT = (1 / 3, 2 / 3)  # límites entre Izquierda | Centro | Derecha
MIN_OVERLAP = 0.25           # fracción del ancho del objeto que debe caer en la zona

# --- Urgencia (proporción del área del frame que ocupa el objeto) ---
# Estimador barato de cercanía. Calíbralo con pruebas reales.
MID_RATIO = 0.08
NEAR_RATIO = 0.25

# --- Anti-parpadeo (frames consecutivos necesarios) ---
FRAMES_TO_RISE = 2
FRAMES_TO_FALL = 4

# --- Política para obstáculos a AMBOS lados con el centro libre ("paso estrecho") ---
# 0 = silencio total, 1 = aviso suave frontal. A definir con el equipo y probar con usuarios.
NARROW_PASSAGE_C_LEVEL = 1

# --- Serial ---
SERIAL_BAUD = 115200
HEARTBEAT_S = 0.25   # reenvía el último comando aunque no cambie (el Arduino tiene watchdog de 1 s)

# --- Tracking y persistencia ---
USE_TRACKING = True
TRACKER = "bytetrack.yaml"
GHOST_FRAMES = 5          # frames que se "recuerda" un objeto que el modelo dejó de ver

# --- Distancia estimada por la ALTURA del recuadro (requiere calibrar con calibrar.py) ---
CALIBRATION_FILE = "calibration.json"
NEAR_M = 1.0              # <= peligro (nivel 3)
MID_M = 2.0               # <= precaución (nivel 2)
MAX_RANGE_M = 4.0         # más lejos que esto se ignora
TRUNCATED_IS_NEAR = True  # recuadro tocando el borde superior/inferior = muy cerca

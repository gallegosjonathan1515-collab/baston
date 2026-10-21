/*
  Firmware de ejemplo - Bastón Inteligente (Arduino Nano / ESP32)
  Recibe por serial:  L:<0-3>,R:<0-3>,C:<0-3>\n   (115200 baudios)

  Niveles -> patrón (no bloqueante, con millis()):
    0 apagado | 1 pulso lento (~1 Hz) | 2 pulso rápido (~4 Hz) | 3 continuo

  Seguridad:
  - Watchdog: si pasan > 1 s sin recibir un comando válido, se activa el patrón de FALLA
    (L y R alternando, lento). Apagar los motores sería indistinguible de "camino libre".
  - El sensor ultrasónico frontal actúa de forma INDEPENDIENTE de Python:
    < 50 cm -> nivel 3 frontal, < 100 cm -> nivel 2, aunque la cámara/PC fallen.
  ¡Pines de ejemplo! Ajustar con el compañero de hardware.
*/

// ---------- Pines ----------
const uint8_t PIN_MOTOR_L = 5;
const uint8_t PIN_MOTOR_R = 6;
const uint8_t PIN_MOTOR_C = 9;     // motor frontal (si existe)
const bool    HAS_FRONT_MOTOR = true;  // false -> el aviso frontal hace vibrar L y R a la vez
const uint8_t PIN_TRIG = 7;
const uint8_t PIN_ECHO = 8;

// ---------- Parámetros ----------
const unsigned long WATCHDOG_MS = 1000;
const unsigned long SENSOR_EVERY_MS = 60;
const unsigned int  ECHO_TIMEOUT_US = 12000;   // ~2 m
const int NEAR_CM = 50;
const int MID_CM  = 100;
// Bajar el nivel de la cámara si el ultrasónico no ve nada cerca. PELIGROSO: el sensor tiene un
// cono estrecho y falla con objetos delgados o en ángulo. Dejar en false hasta validar.
const bool DOWNGRADE_VISION_IF_FAR = false;

// ---------- Estado ----------
int lvlL = 0, lvlR = 0, lvlC = 0;
unsigned long lastRx = 0;
bool everReceived = false;
int distCm = -1;                 // -1 = sin eco (lejos o sin lectura)
unsigned long lastSensor = 0;
char buf[40];
uint8_t blen = 0;

// Cadencias (ms). Nivel 1 ~1 pulso/s, nivel 2 ~4 pulsos/s. Los motores de disco tardan
// ~50-100 ms en arrancar: si el pulso rápido no se siente, sube P2_ON/P2_PERIOD.
const unsigned int P1_PERIOD = 1000, P1_ON = 200;
const unsigned int P2_PERIOD = 250,  P2_ON = 125;

bool pulse(int level, unsigned long now) {
  switch (level) {
    case 1: return (now % P1_PERIOD) < P1_ON;
    case 2: return (now % P2_PERIOD) < P2_ON;
    case 3: return true;
    default: return false;
  }
}

void readUltrasonic() {
  digitalWrite(PIN_TRIG, LOW);  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH); delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);
  unsigned long us = pulseIn(PIN_ECHO, HIGH, ECHO_TIMEOUT_US);
  distCm = (us == 0) ? -1 : (int)(us / 58);
}

void parseLine(const char* s) {
  int l, r, c;
  if (sscanf(s, "L:%d,R:%d,C:%d", &l, &r, &c) == 3 &&
      l >= 0 && l <= 3 && r >= 0 && r <= 3 && c >= 0 && c <= 3) {
    lvlL = l; lvlR = r; lvlC = c;
    lastRx = millis();
    everReceived = true;
  }
}

void readSerial() {
  while (Serial.available()) {
    char ch = Serial.read();
    if (ch == '\n') { buf[blen] = 0; parseLine(buf); blen = 0; }
    else if (ch != '\r' && blen < sizeof(buf) - 1) buf[blen++] = ch;
    else if (blen >= sizeof(buf) - 1) blen = 0;   // línea corrupta: descartar
  }
}

void setup() {
  pinMode(PIN_MOTOR_L, OUTPUT); pinMode(PIN_MOTOR_R, OUTPUT); pinMode(PIN_MOTOR_C, OUTPUT);
  pinMode(PIN_TRIG, OUTPUT);    pinMode(PIN_ECHO, INPUT);
  Serial.begin(115200);
}

void loop() {
  unsigned long now = millis();
  readSerial();

  if (now - lastSensor >= SENSOR_EVERY_MS) { readUltrasonic(); lastSensor = now; }

  bool fault = (!everReceived) || (now - lastRx > WATCHDOG_MS);
  int l = fault ? 0 : lvlL, r = fault ? 0 : lvlR, c = fault ? 0 : lvlC;

  // Ultrasónico independiente de la IA (solo puede SUBIR el nivel frontal)
  if (distCm > 0 && distCm < NEAR_CM)      c = 3;
  else if (distCm > 0 && distCm < MID_CM)  c = max(c, 2);
  else if (DOWNGRADE_VISION_IF_FAR && distCm == -1 && c > 1) c = 1;

  bool outL, outR, outC;
  if (fault && c == 0) {
    // Patrón de FALLA: izquierda y derecha alternan lento (distinto a cualquier nivel normal)
    outL = ((now % 1600) < 400);
    outR = ((now % 1600) >= 800 && (now % 1600) < 1200);
    outC = false;
  } else {
    outL = pulse(l, now);
    outR = pulse(r, now);
    outC = pulse(c, now);
  }

  digitalWrite(PIN_MOTOR_L, (outL || (!HAS_FRONT_MOTOR && outC)) ? HIGH : LOW);
  digitalWrite(PIN_MOTOR_R, (outR || (!HAS_FRONT_MOTOR && outC)) ? HIGH : LOW);
  digitalWrite(PIN_MOTOR_C, (HAS_FRONT_MOTOR && outC) ? HIGH : LOW);
}

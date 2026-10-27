/*
  AI Traffic Light - a desk status lamp for Claude Code.
  Runs unchanged on an Arduino Nano and on an ESP32 DevKit V1.

  Serial protocol, 9600 baud, one line per message:
    G <project>   WORKING   steady green
    Y <project>   WAITING   breathing yellow (Claude Code needs you)
    R <project>   READY     steady red (finished, your turn)
    O             IDLE      ring off
  Example: "Y athlete paper". Lowercase letters are accepted too.
  The board answers "OK <letter> <project>" or "ERR <line>" for debugging.

  Libraries (Arduino IDE Library Manager):
    Adafruit NeoPixel, Adafruit GFX Library, Adafruit SSD1306
*/

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_NeoPixel.h>

// ---------- Settings ----------
#if defined(ESP32)
const uint8_t  RING_PIN  = 13;   // GPIO 13
const uint16_t RING_LEDS = 12;   // change to match your ring
const int      I2C_SDA   = 21;
const int      I2C_SCL   = 22;
#else
const uint8_t  RING_PIN  = 6;    // D6
const uint16_t RING_LEDS = 16;   // change to match your ring
#endif

const long    BAUD            = 9600;  // keep at 9600: faster can drop characters on the Nano
const uint8_t RING_BRIGHTNESS = 80;    // 0..255
const uint8_t OLED_ADDR       = 0x3C;
const uint8_t MAX_NAME        = 21;    // characters that fit on one OLED line at text size 1

// ---------- Devices ----------
Adafruit_NeoPixel ring(RING_LEDS, RING_PIN, NEO_GRB + NEO_KHZ800);
Adafruit_SSD1306  oled(128, 64, &Wire, -1);
bool oledOk = false;

// ---------- State ----------
char state = 'O';
char project[MAX_NAME + 1] = "";
unsigned long stateSince = 0;

char    lineBuf[48];
uint8_t lineLen = 0;

uint32_t lastRingColor = 0xFFFFFFFF;   // forces the first ring update
unsigned long lastRingMs = 0;
unsigned long lastScreenMs = 0;

const char* stateLabel(char s) {
  switch (s) {
    case 'G': return "WORKING";
    case 'Y': return "WAITING";
    case 'R': return "READY";
    default:  return "IDLE";
  }
}

void baseColor(char s, uint8_t &r, uint8_t &g, uint8_t &b) {
  switch (s) {
    case 'G': r = 0;   g = 200; b = 0; break;
    case 'Y': r = 255; g = 150; b = 0; break;
    case 'R': r = 255; g = 0;   b = 0; break;
    default:  r = 0;   g = 0;   b = 0; break;
  }
}

void printDuration(unsigned long secs) {
  if (secs < 60) {
    oled.print(secs); oled.print("s");
  } else if (secs < 3600) {
    oled.print(secs / 60); oled.print("m");
  } else {
    oled.print(secs / 3600); oled.print("h ");
    oled.print((secs % 3600) / 60); oled.print("m");
  }
}

void drawScreen() {
  if (!oledOk) return;
  oled.clearDisplay();
  oled.setTextColor(SSD1306_WHITE);

  oled.setTextSize(2);
  oled.setCursor(0, 4);
  oled.print(stateLabel(state));

  oled.setTextSize(1);
  oled.setCursor(0, 32);
  oled.print(project);

  if (state != 'O') {
    oled.setCursor(0, 52);
    oled.print("for ");
    printDuration((millis() - stateSince) / 1000UL);
  }
  oled.display();
}

void drawRing() {
  uint8_t r, g, b;
  baseColor(state, r, g, b);

  uint32_t level = 255;
  if (state == 'Y') {                       // breathing, about 3 s per cycle
    uint32_t t   = (millis() / 6UL) % 512UL;
    uint32_t tri = t < 256 ? t : 511 - t;
    level = 30 + (tri * 225UL) / 255UL;
  }

  uint32_t color = ring.Color((uint32_t)r * level / 255,
                              (uint32_t)g * level / 255,
                              (uint32_t)b * level / 255);
  if (color == lastRingColor) return;       // only push data to the ring when it changes
  lastRingColor = color;
  ring.fill(color);
  ring.show();
}

void applyLine(char *line) {
  while (*line == ' ' || *line == '\t') line++;
  if (*line == '\0') return;

  char s = toupper(*line);
  if (s != 'G' && s != 'Y' && s != 'R' && s != 'O') {
    Serial.print("ERR "); Serial.println(line);
    return;
  }

  char *name = line + 1;
  while (*name == ' ' || *name == '\t') name++;

  char newName[MAX_NAME + 1];
  strncpy(newName, name, MAX_NAME);
  newName[MAX_NAME] = '\0';
  for (int i = strlen(newName) - 1; i >= 0 && newName[i] == ' '; i--) newName[i] = '\0';

  if (s != state || strcmp(newName, project) != 0) stateSince = millis();
  state = s;
  strcpy(project, newName);

  Serial.print("OK "); Serial.print(state); Serial.print(' '); Serial.println(project);
  drawRing();
  drawScreen();
}

void readSerial() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n' || c == '\r') {
      if (lineLen > 0) {
        lineBuf[lineLen] = '\0';
        applyLine(lineBuf);
        lineLen = 0;
      }
    } else if (lineLen < sizeof(lineBuf) - 1) {
      lineBuf[lineLen++] = c;
    }
  }
}

void setup() {
  Serial.begin(BAUD);

#if defined(ESP32)
  Wire.begin(I2C_SDA, I2C_SCL);
#endif
  oledOk = oled.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR);
  if (!oledOk) Serial.println("WARN OLED not found, ring only");

  ring.begin();
  ring.setBrightness(RING_BRIGHTNESS);
  ring.clear();
  ring.show();

  stateSince = millis();
  drawRing();
  drawScreen();
  Serial.println("READY FOR COMMANDS: G|Y|R|O <project>");
}

void loop() {
  readSerial();

  unsigned long now = millis();
  if (now - lastRingMs >= 20) {      // 50 updates per second for the breathing effect
    lastRingMs = now;
    drawRing();
  }
  if (now - lastScreenMs >= 1000) {  // refresh the "for 3m" timer once per second
    lastScreenMs = now;
    drawScreen();
  }
}

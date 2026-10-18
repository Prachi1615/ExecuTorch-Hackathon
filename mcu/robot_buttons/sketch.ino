// Pip robot head: STM32H5 microcontroller sketch (Arduino App Lab, VENTUNO Q).
//
// Reads the Modulino Buttons over Qwiic and exposes two Bridge functions
// that the Linux side calls through the Arduino Router:
//   take_buttons() -> bitmask of presses since the last call (A=1, B=2, C=4)
//   set_leds(mask) -> button LEDs on/off (A=1, B=2, C=4)
//   ping()         -> 2 = bridge + buttons OK, 1 = bridge only
//
// IMPORTANT: the sketch waits ~40 s before registering its functions.
// Right after flashing (and at power-up) the MCU starts before the Linux
// Router has (re)opened the serial link; anything registered earlier is lost
// and Linux sees "method not available". The fast-blinking built-in LED shows
// the wait; start recognize.py only after it stops.

#include <Arduino_RouterBridge.h>
#include <Modulino.h>

ModulinoButtons buttons;
uint8_t latched = 0;   // presses since Linux last asked
bool buttons_ok = false;

int ping() { return buttons_ok ? 2 : 1; }

int take_buttons() {
  uint8_t v = latched;
  latched = 0;
  return v;            // bit 0 = A, bit 1 = B, bit 2 = C
}

void set_leds(int mask) {
  if (buttons_ok) buttons.setLeds(mask & 1, mask & 2, mask & 4);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  // wait for the Router to (re)open the link before registering
  for (int i = 0; i < 400; i++) {
    digitalWrite(LED_BUILTIN, (i % 2) ? LOW : HIGH);
    delay(100);
  }
  digitalWrite(LED_BUILTIN, HIGH);   // off (active-low)

  if (!Bridge.begin()) {
    while (true) {}
  }
  Bridge.provide("ping", ping);
  Bridge.provide_safe("take_buttons", take_buttons);
  Bridge.provide_safe("set_leds", set_leds);

  Modulino.begin();
  buttons_ok = buttons.begin();
}

void loop() {
  if (buttons_ok && buttons.update()) {
    for (int i = 0; i < 3; i++) {
      if (buttons.isPressed(i)) latched |= (1 << i);
    }
  }
}

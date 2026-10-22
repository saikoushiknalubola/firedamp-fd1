// FD-1 Borehole Sentinel, node firmware (Stage 2 baseline)
// Team Chakra / Firedamp Dynamics, Vishwakarma Awards 2026-27, VK26-IITH-SM-0008
//
// Loop: SENSE -> VALIDATE -> CORRECT -> CLASSIFY -> ACT + LOG, once per second.
// Sensor drivers are thin wrappers; bring-up values are checked against datasheets
// on the bench before any threshold is trusted.

#include <Arduino.h>
#include <Wire.h>
#include <math.h>
#include "pins.h"
#include "config.h"

enum class State : uint8_t { BOOT, MONITOR, THROTTLE, ISOLATE, FAULT };
enum class GasMode : uint8_t { METHANE, CO2_SURROGATE };   // bench runs use CO2_SURROGATE

struct Reading {
  float ch4_ndir_pct = NAN;   // MH-440D
  float o2_pct = NAN;         // SEN0322
  float dp_pa = NAN;          // SDP810
  float p_abs_kpa = NAN;      // MPX5100AP
  float t_c = NAN;            // SHT40
  uint32_t ms = 0;
};

struct Totals {               // MRV accumulators, persisted to microSD every minute
  double ch4_drained_nm3 = 0;
  double ch4_routed_nm3 = 0;
  uint32_t isolated_s = 0;
};

static State state = State::BOOT;
static GasMode mode = GasMode::CO2_SURROGATE;
static Reading r;
static Totals tot;
static uint32_t bootMs, throttleSinceMs;
static float throttlePos = 1.0f;   // 1 = fully open

// ---------------------------------------------------------------- sensor wrappers
// MH-440D analog output: 0.4 V = 0 %vol, 2.0 V = full scale (Winsen product page).
float readNdirAnalogPct() {
  float v = analogReadMilliVolts(PIN_NDIR_AN) / 1000.0f;
  return constrain((v - 0.4f) / 1.6f * 100.0f, 0.0f, 100.0f);
}

// MPX5100AP behind a 10k/18k divider: Vout = Vs*(0.009*P - 0.095), Vs = 5.0 V.
float readPressureKpa() {
  float vadc = analogReadMilliVolts(PIN_P_ADC) / 1000.0f;
  float vout = vadc * (10.0f + 18.0f) / 18.0f;
  return (vout / 5.0f + 0.095f) / 0.009f;
}

// SEN0322 and SDP810 are read through their vendor libraries in the bring-up build
// (DFRobot_OxygenSensor, Sensirion SDP). Stubs keep the control logic testable.
float readO2Pct();
float readDpPa();
float readTempC();

// ---------------------------------------------------------------- physics
float o2DerivedFraction(float o2) {          // binary mixture of air + one other gas
  return constrain(1.0f - o2 / O2_IN_AIR_PCT, 0.0f, 1.0f);
}

float mixtureDensity(float x) {              // x = fraction of seam gas (or surrogate)
  float rhoGas = (mode == GasMode::METHANE) ? RHO_CH4_20C : RHO_CO2_20C;
  return x * rhoGas + (1.0f - x) * RHO_AIR_20C;
}

float orificeFlowM3s(float dp, float rho) {  // ISO 5167 form, Cd from rig calibration
  if (dp <= 0) return 0;
  const float a = PI * ORIFICE_BORE_M * ORIFICE_BORE_M / 4.0f;
  const float beta = ORIFICE_BORE_M / PIPE_ID_M;
  return ORIFICE_CD * a * sqrtf(2.0f * dp / rho) / sqrtf(1.0f - powf(beta, 4));
}

float toNormal(float q, float pKpa, float tC) { // to 0 C, 101.325 kPa
  return q * (pKpa / 101.325f) * (273.15f / (273.15f + tC));
}

// ---------------------------------------------------------------- actuators
void setIsolation(bool open) { digitalWrite(PIN_SOLENOID, open ? HIGH : LOW); }
void setThrottle(float pos) {                 // 0..1 -> 500..2500 us at 50 Hz (14-bit)
  throttlePos = constrain(pos, 0.15f, 1.0f);
  uint32_t us = 500 + (uint32_t)(throttlePos * 2000);
  ledcWrite(PIN_SERVO, (us * 16383UL) / 20000UL);
}
void lamp(bool R, bool A, bool G) {
  digitalWrite(PIN_LAMP_R, R); digitalWrite(PIN_LAMP_A, A); digitalWrite(PIN_LAMP_G, G);
}

// ---------------------------------------------------------------- state machine
void step(float now_s) {
  float ndir = r.ch4_ndir_pct;
  float o2x = o2DerivedFraction(r.o2_pct) * 100.0f;
  // In surrogate mode the O2-derived value IS the gas fraction; NDIR is span-checked separately.
  float gas = (mode == GasMode::METHANE) ? ndir : o2x;

  bool stale = (millis() - r.ms) > SENSOR_TIMEOUT_MS || isnan(gas) || isnan(r.o2_pct);
  bool implausible = (mode == GasMode::METHANE) && fabsf(ndir - o2x) > PLAUSIBILITY_PTS;

  if (state != State::BOOT && state != State::ISOLATE && (stale || implausible)) state = State::FAULT;
  if (state != State::BOOT && state != State::FAULT && r.o2_pct > O2_ISOLATE_PCT) state = State::ISOLATE;

  switch (state) {
    case State::BOOT:
      setIsolation(false); lamp(false, true, false);
      if ((millis() - bootMs) > NDIR_WARMUP_S * 1000UL && !stale) state = State::MONITOR;
      break;
    case State::MONITOR:
      setIsolation(true); setThrottle(throttlePos + 0.002f); lamp(false, false, true);  // reopen slowly
      if (gas < CH4_ROUTE_MIN_PCT) { state = State::THROTTLE; throttleSinceMs = millis(); }
      break;
    case State::THROTTLE:                      // reduce suction on this hole to cut air ingress
      setIsolation(true); lamp(false, true, false);
      setThrottle(throttlePos - 0.02f);
      if (gas >= CH4_ROUTE_MIN_PCT + CH4_ROUTE_HYST_PCT) state = State::MONITOR;
      else if (gas < CH4_ISOLATE_PCT || millis() - throttleSinceMs > THROTTLE_RECOVERY_S * 1000UL)
        state = State::ISOLATE;
      break;
    case State::ISOLATE:                       // latched; cleared by operator over Modbus/button
      setIsolation(false); lamp(true, false, false); digitalWrite(PIN_BUZZER, HIGH);
      tot.isolated_s++;
      break;
    case State::FAULT:
      setIsolation(false); lamp(true, true, false);
      break;
  }

  // MRV: count drained gas while the valve is open
  if (state == State::MONITOR || state == State::THROTTLE) {
    float x = gas / 100.0f;
    float q = orificeFlowM3s(r.dp_pa, mixtureDensity(x));
    float qn = toNormal(q, r.p_abs_kpa, r.t_c);
    tot.ch4_drained_nm3 += qn * x;                         // 1 s step
    if (gas >= CH4_ROUTE_MIN_PCT) tot.ch4_routed_nm3 += qn * x;
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_I2C_SDA, PIN_I2C_SCL, 100000);
  pinMode(PIN_SOLENOID, OUTPUT); setIsolation(false);     // fail-closed from first instruction
  pinMode(PIN_LAMP_R, OUTPUT); pinMode(PIN_LAMP_A, OUTPUT); pinMode(PIN_LAMP_G, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  ledcAttach(PIN_SERVO, 50, 14);
  analogReadResolution(12);
  bootMs = millis();
}

void loop() {
  static uint32_t last = 0;
  if (millis() - last < 1000) return;
  last = millis();
  r.ch4_ndir_pct = readNdirAnalogPct();
  r.o2_pct = readO2Pct();
  r.dp_pa = readDpPa();
  r.p_abs_kpa = readPressureKpa();
  r.t_c = readTempC();
  r.ms = millis();
  step(millis() / 1000.0f);
  Serial.printf("st=%u ch4=%.1f o2=%.2f dp=%.1f p=%.1f thr=%.2f drained=%.4f\n", (unsigned)state,
                r.ch4_ndir_pct, r.o2_pct, r.dp_pa, r.p_abs_kpa, throttlePos, tot.ch4_drained_nm3);
}

// --- bring-up stubs (replaced by vendor-library reads on the bench build) ---
float readO2Pct() { return 20.9f; }
float readDpPa() { return 0.0f; }
float readTempC() { return 25.0f; }

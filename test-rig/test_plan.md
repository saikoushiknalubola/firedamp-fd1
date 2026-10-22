# FD-1 bench test plan (Stage 3)

All tests use CO2 (non-flammable) as the seam-gas stand-in. Vent to outdoors. Two people present, emergency stop within reach.

| # | Test | Method | Pass criterion (target) |
|---|---|---|---|
| T1 | Leak-tightness | Close outlet, pull -30 kPa with the pump, isolate, watch MPX5100AP for 10 min | Pressure rise < 1 kPa in 10 min |
| T2 | Flow calibration | Air at 1, 2, 4, 6 L/min against rotameter; fit Cd | Within +/-5% across range after fit |
| T3 | O2 zero/span | Fresh air (20.9%) and pure CO2 stream (0% O2) | Within +/-0.3 %vol O2 |
| T4 | NDIR span check | 2.5 %vol CH4 certified gas through chamber, 3 min warm-up | Reading within the datasheet tolerance |
| T5 | Leak response | Open air-bleed valve in steps; log purity, throttle, state | Throttle engages below 30%; isolation below 25%, 10/10 runs |
| T6 | Fault injection | Unplug O2 sensor, kill 12 V, freeze firmware (watchdog) | Valve closed in every case |
| T7 | Water slug | 50 mL water injected upstream of trap | No liquid in sensing chamber; reading back within 2 min |
| T8 | Endurance | 72 h continuous with scripted leak events | No resets; MRV totals match integrated rotameter reading within 5% |

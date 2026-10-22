// FD-1 node pin map (ESP32-S3-WROOM-1-N8R8). Mirrors electronics/pinmap.csv.
// GPIO35-37 are reserved for octal PSRAM on N8R8 modules; GPIO19/20 are USB.
#pragma once

#define PIN_I2C_SDA      8
#define PIN_I2C_SCL      9
#define PIN_NDIR_TX     17   // MCU TX -> MH-440D RXD
#define PIN_NDIR_RX     18   // MCU RX <- MH-440D TXD
#define PIN_NDIR_AN      1   // optional: MH-440D analog out (0.4-2.0 V) on ADC1_CH0
#define PIN_P_ADC        4   // MPX5100AP via 10k/18k divider
#define PIN_485_TX      15
#define PIN_485_RX      16
#define PIN_485_DE       7
#define PIN_SOLENOID     6   // IRLZ44N gate, HIGH = valve open (NC valve closes on power loss)
#define PIN_SERVO        5   // throttle servo, LEDC 50 Hz
#define PIN_ROUTER_IN1  10   // DRV8871
#define PIN_ROUTER_IN2  11
#define PIN_LAMP_R      13
#define PIN_LAMP_A      14
#define PIN_LAMP_G      21
#define PIN_BUZZER      12
#define PIN_SD_CS       39
#define PIN_SD_SCK      40
#define PIN_SD_MISO     41
#define PIN_SD_MOSI     42

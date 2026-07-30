# Whirlygigs Wiring Guide (Pi Zero 2 W)

## GPIO / I2C Pin Assignments

| Function | Pi Pin | BCM | Notes |
|---|---:|---:|---|
| ADS1115 SDA | 3 | GPIO2 | I2C1 SDA |
| ADS1115 SCL | 5 | GPIO3 | I2C1 SCL |
| Flow pulses (A1220 OUT) | 11 | GPIO17 | Interrupt input, 10k pull-up to VCC |
| Generator pulses (PC817 collector) | 13 | GPIO27 | Interrupt input, pull-up to 3.3V |
| 5V rail | 2/4 | - | ADS1115 VDD, sensor supplies |
| Ground | 6/9/etc | - | Common ground |

ADS1115 address: `0x48`

## Pressure Transducers (Grundfos RPS 0–16 bar)

| Sensor Pin | Wire Color | Connection |
|---|---|---|
| Pin 4 | Brown | +5V |
| Pin 3 | Green | GND |
| Pin 2 | White | ADS1115 analog input (P1->A0, P2->A1) |
| Pin 1 | Yellow | Temperature (unused) |

## A1220 Hall Sensor (Flow)

- VCC -> +5V
- GND -> common GND
- OUT -> GPIO17
- Add 10k pull-up from OUT to VCC

## PC817 Optocoupler (Generator Frequency)

- LED side: turbine AC + series resistor
- Transistor side: emitter -> GND, collector -> GPIO27
- Pull-up from collector to 3.3V

## Rectifier / DC Bus

```text
Turbine AC -> 1N5819 x4 bridge -> smoothing capacitor -> DC bus
                                                   |- DL24 DC+
                                                   |- DL24 DC-
                                                   `- resistor divider -> ADS1115 A2
```

## DL24 Connection

- Power leads: DC+ and DC- to DC bus
- Data/control: Pi USB OTG -> USB-A to micro-USB -> DL24 micro-USB
- Protocol: Modbus RTU over CH340 serial (`/dev/ttyUSB0`), 9600 baud

## Power Notes

```text
Phone / portable charger (5V USB-C)
  -> USB-C to micro-USB cable
  -> Pi Zero 2 W PWR micro-USB port
```

Use Pi 5V/GND header rails for ADS1115 + sensors and keep all grounds common.

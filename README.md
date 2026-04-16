# Whirlygigs: Turbine Bench Test System

Whirlygigs characterizes small water turbines by measuring **hydraulic power in** versus **electrical power out** over a matrix of flow rates and electrical loads, with logging to CSV on a Raspberry Pi Zero 2 W microSD card.

## Hardware

- Raspberry Pi Zero 2 W (main controller/logger)
- Adafruit ADS1115 (I2C address `0x48`)
  - A0: Grundfos RPS P1 (0–5V)
  - A1: Grundfos RPS P2 (0–5V)
  - A2: Rectified DC bus divider
- Allegro A1220 hall-effect latch (flow pulses)
- PC817 optocoupler (generator frequency pulses)
- 4x 1N5819 Schottky diodes (bridge rectifier)
- Smoothing capacitor across DC bus
- DL24 150W DC electronic load (USB Modbus + DC power leads)
- 2x Grundfos RPS 0–16 bar pressure transducers
- GEMS FT100 flow meter (K = 11.0 Hz/GPM)
- USB-C power pigtail / phone charger and OTG adapter

## System Diagram

```text
Phone 5V -> Pi Zero 2 W PWR micro-USB

Pi Zero 2 W (only brain)
  |- I2C GPIO2/3 -> ADS1115 (A0 P1, A1 P2, A2 Vbus)
  |- GPIO17 <- A1220 flow pulses
  |- GPIO27 <- PC817 generator pulses
  `- USB OTG -> DL24 (CH340 serial, Modbus RTU 9600)

Turbine AC -> Schottky bridge + cap -> DC bus -> DL24
                                  `-> divider -> ADS1115 A2
```

## Wiring

See [WIRING.md](WIRING.md) for full pinout tables and wiring details.

## Quick Start

1. Install Raspberry Pi OS and enable I2C (`raspi-config`).
2. Clone this repo to the Pi.
3. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
4. Connect hardware (ADS1115, GPIO pulse inputs, DL24 on USB).
5. Run:
   ```bash
   python3 whirlygigs.py
   ```

## Test Workflow Overview

The script walks you through:

1. Startup & hardware check (ADS1115/GPIO/DL24)
2. Flow meter selection (`config/flowmeters.csv`)
3. Pressure zero (3s average)
4. Baseline pressure calibration vs flow (or load saved baseline)
5. Turbine selection (`config/turbines.csv` or custom unlisted)
6. Install turbine + detect minimum generating flow (`Vgen > 0.05V`)
7. Automated DL24 resistance sweep over each flow target
8. Save summary and optional next turbine test

Preserved constants:

- Flow targets: `[0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]` GPM
- Resistance values: `[1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000]` Ω
- GEMS FT100 K-factor: `11.0 Hz/GPM`
- Generator threshold: `0.05V`
- ADS1115 gain: `2/3` (±6.144V)
- Calibration/sample rates: ~10 Hz, 10 s per point

## Data Output Format

Files are written to `data/ttest_NNNN.csv`.

Header comments:

```text
# Turbine: [name]
# ID: [letter]
# Flow meter: GEMS FT100
# Min start flow GPM: [value]
```

Columns:

```text
timestamp_s,flow_gpm,gen_freq_hz,R_ohm,V_gen_V,I_meas_A,P_elec_W,dP_raw_PSI,dP_baseline_PSI,dP_corrected_PSI,flow_m3s,dP_Pa,P_hydro_W
```

## Configuration

- `config/flowmeters.csv`: `name,k_hz_per_gpm`
- `config/turbines.csv`: `id,name,type`

## Unit Conversions

- `flow_m3s = GPM * 6.30902e-5`
- `dP_Pa = dP_PSI * 6894.76`
- Pressure transducer conversion:
  - `bar = (voltage / 5.0) * 16.0`
  - `psi = bar * 14.5038`

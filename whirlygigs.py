#!/usr/bin/env python3
"""Whirlygigs: Raspberry Pi Zero 2 W turbine bench test workflow."""

from __future__ import annotations

import csv
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

from dl24 import DL24
from sensors import SensorSuite

FLOW_TARGETS_GPM = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0]
RESISTANCE_SWEEP_OHM = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000]
GPM_TO_M3S = 6.30902e-5
PSI_TO_PA = 6894.76
GEN_MIN_VOLTAGE_V = 0.05

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
CALIBRATION_FILE = BASE_DIR / "calibration" / "baseline_dp.csv"
DATA_DIR = BASE_DIR / "data"


@dataclass
class FlowMeter:
    name: str
    k_hz_per_gpm: float


@dataclass
class Turbine:
    tid: str
    name: str
    ttype: str


def load_flowmeters(path: Path = CONFIG_DIR / "flowmeters.csv") -> List[FlowMeter]:
    meters: List[FlowMeter] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or row[0].strip().startswith("#"):
                continue
            meters.append(FlowMeter(row[0].strip(), float(row[1])))
    return meters


def load_turbines(path: Path = CONFIG_DIR / "turbines.csv") -> List[Turbine]:
    turbines: List[Turbine] = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or row[0].strip().startswith("#"):
                continue
            turbines.append(Turbine(row[0].strip(), row[1].strip(), row[2].strip()))
    return turbines


def choose_from_list(options: Sequence, label: str) -> int:
    print(f"\nSelect {label}:")
    for idx, item in enumerate(options, start=1):
        print(f"  {idx}. {item}")
    raw = input(f"Choice [1-{len(options)}] (default 1): ").strip()
    if not raw:
        return 0
    choice = max(1, min(len(options), int(raw))) - 1
    return choice


def read_baseline_calibration(path: Path = CALIBRATION_FILE) -> Dict[float, float]:
    baseline: Dict[float, float] = {}
    if not path.exists():
        return baseline
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row or row[0].strip().startswith("#"):
                continue
            baseline[float(row[0])] = float(row[1])
    return baseline


def save_baseline_calibration(baseline: Dict[float, float], path: Path = CALIBRATION_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["# flow_gpm", "dp_baseline_psi"])
        for flow in sorted(baseline):
            writer.writerow([flow, baseline[flow]])


def interpolate_baseline_dp(flow_gpm: float, baseline: Dict[float, float]) -> float:
    if not baseline:
        return 0.0
    points = sorted(baseline.items())
    if flow_gpm <= points[0][0]:
        return points[0][1]
    if flow_gpm >= points[-1][0]:
        return points[-1][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= flow_gpm <= x1:
            if x1 == x0:
                return y0
            ratio = (flow_gpm - x0) / (x1 - x0)
            return y0 + ratio * (y1 - y0)
    return 0.0


def pressure_zero(sensor: SensorSuite) -> Tuple[float, float]:
    input("\nStep 3: Close valves/no flow. Press Enter to zero pressures.")
    p1_zero, p2_zero = sensor.sample_pressures(seconds=3.0, hz=10.0)
    print(f"Zero offsets: P1={p1_zero:.3f} PSI, P2={p2_zero:.3f} PSI")
    return p1_zero, p2_zero


def flow_hz_to_gpm(flow_hz: float, k_hz_per_gpm: float) -> float:
    return flow_hz / k_hz_per_gpm if k_hz_per_gpm > 0 else 0.0


def calibration_step(sensor: SensorSuite, meter: FlowMeter, zero_p1: float, zero_p2: float) -> Dict[float, float]:
    print("\nStep 4: Pressure calibration")
    baseline = read_baseline_calibration()
    if baseline:
        if input("Load existing baseline calibration? (y/n): ").strip().lower() == "y":
            print(f"Loaded calibration from {CALIBRATION_FILE}")
            return baseline

    input("Remove turbine from test section. Press Enter to begin calibration.")
    baseline = {}
    for target in FLOW_TARGETS_GPM:
        flow_hz, _ = sensor.pulse_rates_hz()
        current_gpm = flow_hz_to_gpm(flow_hz, meter.k_hz_per_gpm)
        input(
            f"Set flow to {target:.1f} GPM (current ~{current_gpm:.2f} GPM). "
            "Press Enter when stable."
        )
        p1, p2 = sensor.sample_pressures(seconds=10.0, hz=10.0)
        dp = (p1 - zero_p1) - (p2 - zero_p2)
        baseline[target] = dp
        print(f"  Baseline dP @ {target:.1f} GPM = {dp:.3f} PSI")

    save_baseline_calibration(baseline)
    print(f"Saved calibration to {CALIBRATION_FILE}")
    return baseline


def choose_turbine() -> Turbine:
    print("\nStep 5: Select turbine")
    turbines = load_turbines()
    for idx, t in enumerate(turbines, start=1):
        print(f"  {idx}. [{t.tid}] {t.name} ({t.ttype})")
    print(f"  {len(turbines) + 1}. Unlisted")
    raw = input("Choice: ").strip()
    try:
        choice = int(raw)
    except ValueError:
        choice = 1
    if choice == len(turbines) + 1:
        tid = input("Custom turbine letter ID (single capital): ").strip().upper()[:1] or "U"
        name = input("Turbine name: ").strip() or "Unlisted"
        ttype = input("Turbine type: ").strip() or "Unknown"
        return Turbine(tid, name, ttype)
    choice = max(1, min(len(turbines), choice)) - 1
    return turbines[choice]


def find_min_start_flow(sensor: SensorSuite, meter: FlowMeter) -> float:
    print("\nStep 6: Install turbine and raise flow until generator produces voltage.")
    print("Watching for generator DC voltage > 0.05 V...")
    min_flow_gpm = 0.0
    while True:
        flow_hz, _ = sensor.pulse_rates_hz()
        flow_gpm = flow_hz_to_gpm(flow_hz, meter.k_hz_per_gpm)
        _, _, v_gen = sensor.read_pressures_psi()
        print(f"\rFlow={flow_gpm:6.2f} GPM  Vgen={v_gen:6.3f} V", end="", flush=True)
        if v_gen > GEN_MIN_VOLTAGE_V:
            min_flow_gpm = flow_gpm
            print("\nGENERATING!")
            break
        time.sleep(0.5)
    input("Press Enter to confirm and continue.")
    return min_flow_gpm


def next_data_file(data_dir: Path = DATA_DIR) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)
    nums = []
    for p in data_dir.glob("ttest_*.csv"):
        stem = p.stem.split("_")[-1]
        if stem.isdigit():
            nums.append(int(stem))
    n = (max(nums) + 1) if nums else 1
    return data_dir / f"ttest_{n:04d}.csv"


def write_header_comments(path: Path, turbine: Turbine, meter: FlowMeter, min_start_flow_gpm: float) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        f.write(f"# Turbine: {turbine.name}\n")
        f.write(f"# ID: {turbine.tid}\n")
        f.write(f"# Flow meter: {meter.name}\n")
        f.write(f"# Min start flow GPM: {min_start_flow_gpm:.4f}\n")
        f.write(
            "timestamp_s,flow_gpm,gen_freq_hz,R_ohm,V_gen_V,I_meas_A,P_elec_W,"
            "dP_raw_PSI,dP_baseline_PSI,dP_corrected_PSI,flow_m3s,dP_Pa,P_hydro_W\n"
        )


def resistance_sweep(
    sensor: SensorSuite,
    dl24: DL24,
    meter: FlowMeter,
    zero_p1: float,
    zero_p2: float,
    baseline: Dict[float, float],
    outfile: Path,
) -> Tuple[int, Tuple[float, float, float]]:
    best_global = (0.0, 0.0, 0.0)  # flow, resistance, power
    total_rows = 0
    start_t = time.monotonic()

    with outfile.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        print("\nStep 7: Automated resistance sweep")
        dl24.set_resistance_mode()
        dl24.load_on()

        for target_flow in FLOW_TARGETS_GPM:
            input(f"\nSet flow to {target_flow:.1f} GPM and press Enter when stable.")
            best_for_flow = (0.0, 0.0)  # resistance, power
            for resistance in RESISTANCE_SWEEP_OHM:
                dl24.set_resistance(float(resistance))
                time.sleep(2.0)
                try:
                    v_gen = dl24.read_voltage()
                    i_meas = dl24.read_current()
                except Exception:
                    v_gen = 0.0
                    i_meas = 0.0

                p1, p2, _ = sensor.read_pressures_psi()
                flow_hz, gen_freq = sensor.pulse_rates_hz()
                flow_gpm = flow_hz_to_gpm(flow_hz, meter.k_hz_per_gpm)
                dp_raw = (p1 - zero_p1) - (p2 - zero_p2)
                dp_baseline = interpolate_baseline_dp(flow_gpm, baseline)
                dp_corrected = dp_raw - dp_baseline
                p_elec = v_gen * i_meas
                flow_m3s = flow_gpm * GPM_TO_M3S
                dp_pa = dp_corrected * PSI_TO_PA
                p_hydro = flow_m3s * dp_pa

                writer.writerow(
                    [
                        round(time.monotonic() - start_t, 3),
                        round(flow_gpm, 5),
                        round(gen_freq, 5),
                        resistance,
                        round(v_gen, 6),
                        round(i_meas, 6),
                        round(p_elec, 6),
                        round(dp_raw, 6),
                        round(dp_baseline, 6),
                        round(dp_corrected, 6),
                        round(flow_m3s, 9),
                        round(dp_pa, 6),
                        round(p_hydro, 6),
                    ]
                )
                total_rows += 1

                if p_elec > best_for_flow[1]:
                    best_for_flow = (float(resistance), p_elec)
                if p_elec > best_global[2]:
                    best_global = (flow_gpm, float(resistance), p_elec)

            print(
                f"Flow target {target_flow:.1f} GPM best -> "
                f"R={best_for_flow[0]:.0f} ohm, P={best_for_flow[1]:.3f} W"
            )

        dl24.load_off()
    return total_rows, best_global


def startup(sensor: SensorSuite, dl24: DL24) -> None:
    print("Step 1: Startup & hardware check")
    status = sensor.initialize()
    dl24_ok = True
    try:
        dl24.connect()
    except Exception as exc:
        dl24_ok = False
        print(f"DL24 not available: {exc}")

    print("\nSystem status:")
    print(f"  ADS1115 @0x48: {'OK' if status['ads1115'] else 'NOT FOUND'}")
    print(f"  GPIO pulse interrupts: {'OK' if status['gpio'] else 'NOT READY'}")
    print(f"  DL24 serial (/dev/ttyUSB0): {'OK' if dl24_ok else 'NOT FOUND'}")


def select_flow_meter() -> FlowMeter:
    print("\nStep 2: Select flow meter")
    meters = load_flowmeters()
    for idx, meter in enumerate(meters, start=1):
        print(f"  {idx}. {meter.name} (K={meter.k_hz_per_gpm} Hz/GPM)")
    raw = input("Choice (default 1): ").strip()
    idx = int(raw) - 1 if raw.isdigit() else 0
    idx = max(0, min(len(meters) - 1, idx))
    return meters[idx]


def run_once() -> None:
    sensor = SensorSuite(flow_pin=17, gen_pin=27, ads_address=0x48)
    dl24 = DL24(port="/dev/ttyUSB0", baud=9600, address=0x01)

    try:
        startup(sensor, dl24)
        meter = select_flow_meter()
        zero_p1, zero_p2 = pressure_zero(sensor)
        baseline = calibration_step(sensor, meter, zero_p1, zero_p2)
        turbine = choose_turbine()
        min_start_flow = find_min_start_flow(sensor, meter)

        outfile = next_data_file()
        write_header_comments(outfile, turbine, meter, min_start_flow)
        rows, best = resistance_sweep(sensor, dl24, meter, zero_p1, zero_p2, baseline, outfile)

        print("\nStep 8: Save & summary")
        print(f"Saved: {outfile}")
        print(f"Rows logged: {rows}")
        print(
            f"Best operating point: flow={best[0]:.3f} GPM, "
            f"R={best[1]:.0f} ohm, P={best[2]:.3f} W"
        )
    finally:
        try:
            dl24.close()
        except Exception:
            pass
        sensor.cleanup()


def main() -> None:
    print("Whirlygigs: Turbine Bench Test System")
    while True:
        run_once()
        again = input("\nTest another turbine? (y/n): ").strip().lower()
        if again != "y":
            break


if __name__ == "__main__":
    main()

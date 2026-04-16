"""Sensor module for Whirlygigs Raspberry Pi Zero 2 W bench."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Dict, Tuple

try:
    import RPi.GPIO as GPIO
except Exception:  # pragma: no cover - non-Pi environments
    GPIO = None

try:
    import board
    import busio
    import adafruit_ads1x15.ads1115 as ADS
    from adafruit_ads1x15.analog_in import AnalogIn
except Exception:  # pragma: no cover - non-Pi environments
    board = None
    busio = None
    ADS = None
    AnalogIn = None

PRESSURE_SENSOR_MAX_BAR = 16.0
BAR_TO_PSI = 14.5038
ADS1115_GAIN_TWOTHIRDS = 2 / 3  # ±6.144V full-scale range


@dataclass
class PulseCounter:
    pin: int
    edge: int = 1

    def __post_init__(self) -> None:
        self._lock = threading.Lock()
        self._count = 0
        self._last_snapshot_count = 0
        self._last_snapshot_time = time.monotonic()

    def on_pulse(self, channel: int) -> None:
        del channel
        with self._lock:
            self._count += 1

    def snapshot_hz(self) -> float:
        now = time.monotonic()
        with self._lock:
            new_count = self._count
            old_count = self._last_snapshot_count
            old_time = self._last_snapshot_time
            self._last_snapshot_count = new_count
            self._last_snapshot_time = now
        dt = max(now - old_time, 1e-9)
        return max(0.0, (new_count - old_count) / dt)


class SensorSuite:
    """ADS1115 analog reads + GPIO pulse counting for flow/gen frequency."""

    def __init__(self, flow_pin: int = 17, gen_pin: int = 27, ads_address: int = 0x48) -> None:
        self.flow_pin = flow_pin
        self.gen_pin = gen_pin
        self.ads_address = ads_address
        self.flow_counter = PulseCounter(flow_pin)
        self.gen_counter = PulseCounter(gen_pin)
        self._ads = None
        self._chan0 = None
        self._chan1 = None
        self._chan2 = None

    def initialize(self) -> Dict[str, bool]:
        status = {
            "gpio": False,
            "ads1115": False,
        }
        if GPIO is not None:
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(self.flow_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.gen_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.add_event_detect(self.flow_pin, GPIO.RISING, callback=self.flow_counter.on_pulse)
            GPIO.add_event_detect(self.gen_pin, GPIO.RISING, callback=self.gen_counter.on_pulse)
            status["gpio"] = True

        if all(module is not None for module in (board, busio, ADS, AnalogIn)):
            i2c = busio.I2C(board.SCL, board.SDA)
            self._ads = ADS.ADS1115(i2c, address=self.ads_address)
            self._ads.gain = ADS1115_GAIN_TWOTHIRDS
            self._chan0 = AnalogIn(self._ads, ADS.P0)
            self._chan1 = AnalogIn(self._ads, ADS.P1)
            self._chan2 = AnalogIn(self._ads, ADS.P2)
            _ = self._chan0.voltage
            status["ads1115"] = True

        return status

    def read_ads_voltages(self) -> Tuple[float, float, float]:
        if not self._chan0 or not self._chan1 or not self._chan2:
            raise RuntimeError("ADS1115 not initialized or unavailable")
        return (self._chan0.voltage, self._chan1.voltage, self._chan2.voltage)

    @staticmethod
    def voltage_to_psi(voltage: float) -> float:
        bar = (voltage / 5.0) * PRESSURE_SENSOR_MAX_BAR
        return bar * BAR_TO_PSI

    def read_pressures_psi(self) -> Tuple[float, float, float]:
        v0, v1, v2 = self.read_ads_voltages()
        return (self.voltage_to_psi(v0), self.voltage_to_psi(v1), v2)

    def pulse_rates_hz(self) -> Tuple[float, float]:
        return self.flow_counter.snapshot_hz(), self.gen_counter.snapshot_hz()

    def sample_pressures(self, seconds: float = 3.0, hz: float = 10.0) -> Tuple[float, float]:
        interval = 1.0 / hz
        p1_vals = []
        p2_vals = []
        end_time = time.monotonic() + seconds
        while time.monotonic() < end_time:
            p1, p2, _ = self.read_pressures_psi()
            p1_vals.append(p1)
            p2_vals.append(p2)
            time.sleep(interval)
        if not p1_vals:
            raise RuntimeError("No pressure samples collected")
        return (sum(p1_vals) / len(p1_vals), sum(p2_vals) / len(p2_vals))

    def cleanup(self) -> None:
        if GPIO is not None:
            GPIO.cleanup()

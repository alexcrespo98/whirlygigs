"""DL24 Modbus RTU helper.

Register addresses and scaling can vary by DL24 firmware version.
Verify addresses with your specific unit/documentation.
"""

from __future__ import annotations

import struct
from typing import Iterable, List

try:
    import serial
except Exception:  # pragma: no cover - environments without pyserial
    serial = None


class DL24:
    REG_MODE = 0x0001
    REG_RESISTANCE_CENTIOHM = 0x0002
    REG_LOAD_ENABLE = 0x0003
    REG_VOLTAGE_MV = 0x0010
    REG_CURRENT_MA = 0x0011

    MODE_CONSTANT_RESISTANCE = 0x0002
    MIN_RESISTANCE_CENTIOHM = 1  # 0.01 Ω; verify effective minimum for your firmware/hardware

    def __init__(self, port: str = "/dev/ttyUSB0", baud: int = 9600, address: int = 0x01) -> None:
        self.port = port
        self.baud = baud
        self.address = address
        self.serial = None

    @staticmethod
    def crc16_modbus(data: bytes) -> int:
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc & 0xFFFF

    @classmethod
    def append_crc(cls, frame: bytes) -> bytes:
        crc = cls.crc16_modbus(frame)
        return frame + struct.pack("<H", crc)

    def connect(self) -> None:
        if serial is None:
            raise RuntimeError("pyserial is not installed")
        self.serial = serial.Serial(self.port, self.baud, timeout=1)
        _ = self.read_voltage()

    def close(self) -> None:
        if self.serial and self.serial.is_open:
            self.serial.close()

    def _exchange(self, frame: bytes, expected_min_response: int) -> bytes:
        if not self.serial or not self.serial.is_open:
            raise RuntimeError("DL24 serial port is not connected")
        self.serial.reset_input_buffer()
        self.serial.write(frame)
        response = self.serial.read(256)
        if len(response) < expected_min_response:
            raise RuntimeError("No/short response from DL24")
        payload, recv_crc = response[:-2], response[-2:]
        calc_crc = struct.pack("<H", self.crc16_modbus(payload))
        if recv_crc != calc_crc:
            raise RuntimeError("DL24 CRC check failed")
        if response[1] & 0x80:
            raise RuntimeError(f"DL24 Modbus exception code {response[2]}")
        return response

    def read_holding_registers(self, start_reg: int, count: int) -> List[int]:
        req = struct.pack(">BBHH", self.address, 0x03, start_reg, count)
        response = self._exchange(self.append_crc(req), expected_min_response=5 + 2 * count)
        byte_count = response[2]
        data = response[3 : 3 + byte_count]
        return list(struct.unpack(">" + "H" * (byte_count // 2), data))

    def write_multiple_registers(self, start_reg: int, values: Iterable[int]) -> None:
        vals = list(values)
        byte_count = len(vals) * 2
        body = struct.pack(">BBHHB", self.address, 0x10, start_reg, len(vals), byte_count)
        for value in vals:
            body += struct.pack(">H", value)
        _ = self._exchange(self.append_crc(body), expected_min_response=8)

    def read_voltage(self) -> float:
        mv = self.read_holding_registers(self.REG_VOLTAGE_MV, 1)[0]
        return mv / 1000.0

    def read_current(self) -> float:
        ma = self.read_holding_registers(self.REG_CURRENT_MA, 1)[0]
        return ma / 1000.0

    def set_resistance_mode(self) -> None:
        self.write_multiple_registers(self.REG_MODE, [self.MODE_CONSTANT_RESISTANCE])

    def set_resistance(self, ohms: float) -> None:
        centiohm = max(self.MIN_RESISTANCE_CENTIOHM, int(round(ohms * 100)))
        self.write_multiple_registers(self.REG_RESISTANCE_CENTIOHM, [centiohm])

    def load_on(self) -> None:
        self.write_multiple_registers(self.REG_LOAD_ENABLE, [1])

    def load_off(self) -> None:
        self.write_multiple_registers(self.REG_LOAD_ENABLE, [0])

import tempfile
import unittest
from pathlib import Path

from dl24 import DL24
from sensors import SensorSuite
from whirlygigs import interpolate_baseline_dp, next_data_file


class TestCoreMath(unittest.TestCase):
    def test_voltage_to_psi(self):
        psi = SensorSuite.voltage_to_psi(2.5)
        self.assertAlmostEqual(psi, 116.0304, places=3)

    def test_interpolate_baseline_dp(self):
        baseline = {0.5: 1.0, 1.0: 3.0, 2.0: 7.0}
        self.assertAlmostEqual(interpolate_baseline_dp(0.75, baseline), 2.0)
        self.assertAlmostEqual(interpolate_baseline_dp(0.1, baseline), 1.0)
        self.assertAlmostEqual(interpolate_baseline_dp(3.0, baseline), 7.0)


class TestFileNumbering(unittest.TestCase):
    def test_next_data_file(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "ttest_0001.csv").write_text("\n", encoding="utf-8")
            (d / "ttest_0009.csv").write_text("\n", encoding="utf-8")
            out = next_data_file(d)
            self.assertEqual(out.name, "ttest_0010.csv")


class TestDL24CRC(unittest.TestCase):
    def test_crc_append(self):
        base = bytes([0x01, 0x03, 0x00, 0x10, 0x00, 0x01])
        framed = DL24.append_crc(base)
        self.assertEqual(framed.hex(), "01030010000185cf")


if __name__ == "__main__":
    unittest.main()

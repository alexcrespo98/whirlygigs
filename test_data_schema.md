# Whirlygigs Turbine Test — Raw Data Schema

This document defines the fields for every bench test record. All data is stored in a structured format (CSV or database) so that cost functions, reward curves, and efficiency calculations can be recomputed at any time without baking assumptions into the raw data.

---

## Test Session Metadata (once per session)

| Field | Type | Unit | Notes |
|---|---|---|---|
| session_id | string | | Unique identifier, e.g. "ZurnP6900-2026-05-13" |
| turbine_id | string | | From catalogue (e.g. "zurn-p6900", "m6", "dh24") |
| test_date | date | YYYY-MM-DD | |
| tester | string | | Name |
| rig_version | string | | Test rig hardware version |
| turbine_notes | string | | Physical condition, any mods, serial if available |
| fluid | string | | Default: "water" |
| fluid_temp_C | float | °C | Measured at start of session |

---

## Per-Run Record (one row per flow rate × load resistance combination)

| Field | Type | Unit | Notes |
|---|---|---|---|
| session_id | string | | Foreign key to session |
| run_id | integer | | Sequential within session |
| flow_rate_gpm | float | GPM | Target flow rate for this run |
| load_resistance_ohm | float | Ω | Load resistor value; use "OC" (open circuit) for no-load runs |
| proximal_pressure_psi | float | PSI | Upstream of turbine |
| distal_pressure_psi | float | PSI | Downstream of turbine |
| delta_p_psi | float | PSI | Computed: proximal − distal. This is the turbine's hydraulic cost. |
| calibration_pressure_psi | float | PSI | Pressure drop across the same section with NO turbine installed, at same flow. Subtract from delta_p to isolate turbine-only ΔP from plumbing losses. |
| voltage_v | float | V | Measured across load (RMS for AC, mean for DC) |
| current_ma | float | mA | Measured in series with load |
| ac_frequency_hz | float | Hz | Output frequency; proportional to RPM. Null if load is OC and no frequency measurement available. |
| hall_frequency_hz | float | Hz | Hall pulse frequency if sensor is fitted; null otherwise |
| fluid_temp_c | float | °C | Temperature at time of run (affects viscosity) |
| notes | string | | Anomalies, observations |

---

## Computed Columns (derived, not measured — recompute from raw)

| Field | Formula | Notes |
|---|---|---|
| power_mw | (voltage_v^2 / load_resistance_ohm) × 1000 | Electrical output power |
| hydraulic_power_mw | delta_p_psi × 6894.76 × (flow_rate_gpm × 6.309e-5) × 1000 | ΔP [Pa] × Q [m³/s] |
| efficiency_pct | power_mw / hydraulic_power_mw × 100 | |
| net_delta_p_psi | delta_p_psi − calibration_pressure_psi | Turbine-only hydraulic cost |

---

## Catalogue Entry (summary per turbine, populated from bench data)

| Field | Notes |
|---|---|
| turbine_id | |
| r_coil_ohm | DC coil resistance, measured with multimeter |
| q_start_loaded_gpm | Minimum flow producing output voltage under load |
| q_start_oc_gpm | Minimum flow producing output voltage open-circuit (OC sensing threshold) |
| r_eff_ohm | Peak-efficiency fixed load (if interior sweet spot found) |
| q_eff_gpm | Flow rate at peak efficiency |
| r_max_ohm | Asymptotic optimal resistance (if no interior sweet spot) |
| peak_power_mw | At R_eff or R_max, at Q_eff or operating point |
| peak_delta_p_psi | At rated flow under load |
| peak_efficiency_pct | |
| stator_claw_type | single-sided / dual-sided symmetric / dual-sided asymmetric / belt / spoke |
| coil_count | Number of independent coil circuits |
| output_type | raw AC / unregulated DC / regulated DC |
| integration_status | as-is / needs PCB / needs housing mod / needs coil tap |
| battery_capacitor_rec | Recommendation: supercap / LiPo / none + sizing notes |
| unit_cost_usd | |
| source | Where it was acquired |
| application_notes | Which fixtures and environments it is best suited for |
| tested_date | |

---

## Notes on Calibration Pressure

Always run a calibration pass at each target flow rate with the turbine removed (or bypassed with a straight section of equal length and diameter). Record the pressure drop. This isolates plumbing and fitting losses from the turbine's actual hydraulic cost. Baking this into the raw data allows the Cost/Reward curves to show true turbine ΔP, not rig ΔP.

---

## Notes on Testing Rig (Future — DH)

Testing rig design is a separate work item related to the DH turbine acquisition. Rig should include:
- Calibrated flow meter (GEMS 238600 or equivalent, upstream of test section)
- Proximal and distal pressure taps with calibrated transducers
- Removable turbine section (allows calibration pass without turbine)
- Adjustable load resistance bank (decade box or switched resistor array)
- Temperature sensor on inlet line
- Data acquisition: voltage, current, AC frequency, Hall pulse all logged simultaneously
- Controlled pressure source (pressure regulator on building supply)
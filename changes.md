# Pending Changes to `flowsense_iot.md`

This file tracks all corrections and additions to be applied by an agent.
Each item has a location, type, and exact description of the change needed.
Items are ordered by section. Check off items as they are applied.

---

## 🔴 Critical Corrections

### C1 — Fix pole count / RPM claim in §3.4 coil configuration table
**Location:** Section 3.4, "Flux Types" table, last row ("Cycles per revolution")
**Type:** Factual correction

**Current text:**
> Cycles per revolution: Magnet pole pairs × claw-pole pairs | Magnet pole pairs

**Replace with:**
> Cycles per revolution: Magnet pole pairs (claw count must match both pole sets for correct flux alternation, but does not multiply cycle count) | Magnet pole pairs

**Add a note below the Flux Types table:**
> **Note on stator claws:** Stator claws are soft-iron flux guides, not additional pole pairs. They redirect the axial field from above and below the rotor through the coil, causing the field seen by the coil to swap polarity with each half-revolution of the magnet. The claw count must be aligned with both sets of magnet poles so that the field swap occurs cleanly — misalignment wastes flux coupling. RPM is a purely mechanical quantity (rotor speed) and is unrelated to pole or claw count.

---

### C2 — Expand stator claw subtypes in §3.4
**Location:** Section 3.4, "Coil Configurations" table and surrounding text
**Type:** New content + factual correction

The paper currently treats "claw pole" as a single category. There are at least three distinct physical variants. Replace the single "Claw pole" row with the following three rows, and update the surrounding prose:

| Our Name | Flux | Description | Example |
|---|---|---|---|
| **Claw pole — single-sided** | Axial | One claw piece contacts the top of a single pancake coil; claws are evenly spaced and point downward. Coil sits above the rotor. | Toto EDV (each of the two coils has one single-sided claw) |
| **Claw pole — dual-sided symmetric** | Axial | Two claw pieces (one above, one below the coil) with alternating interleaved teeth; the classic flux redirector. | Toto 10s Dynamo (EDV462 / EDV561) |
| **Claw pole — dual-sided asymmetric** | Axial | Coil sits entirely above the rotor; both claw sets reach downward on either side of the coil. Geometrically inverted vs. symmetric, but functionally equivalent flux-redirect. | Zurn P6900 |

**Also update the Toto rows in the Belt Sub-Categories subsection:**
- Toto EcoPower → belt/wrapped, single coil (no change needed)
- Toto EDV → **claw pole, dual coil. Each of the two coils has one single-sided claw.** Remove from Belt category.
- Toto 10s Dynamo (EDV462/EDV561) → **claw pole, dual coil. Each coil has a full dual-sided symmetric claw assembly.** Remove from Belt category if currently listed there.

---

### C3 — Fix broken Table of Contents anchor links
**Location:** Table of Contents, Appendix entries
**Type:** Typo / broken link

**Current:**
```
- [Appendix A: Catalogue: Flow Meters](#appendix-b-catalogue-flow-meters)
- [Appendix B: Catalogue: Generators](#appendix-c-catalogue-generators)
```

**Replace with:**
```
- [Appendix A: Catalogue: Flow Meters](#appendix-a-catalogue-flow-meters)
- [Appendix B: Catalogue: Generators](#appendix-b-catalogue-generators)
```

---

## 🟠 Major Additions

### A1 — Add MPPT IC section to §4.2 (alongside lookup-table dynamic load)
**Location:** Section 4.2, after the "Pre-Programmed Dynamic Load (Optional)" paragraph
**Type:** New subsection

Add the following subsection:

---

#### Real-Time MPPT (Maximum Power Point Tracking) ICs

Pre-programmed lookup tables require bench data and add firmware complexity. A simpler alternative is a dedicated energy harvesting IC that performs real-time impedance tracking automatically. These chips already exist and are designed exactly for this use case:

| IC | Approach | Cold-start Voltage | Output | Notes |
|---|---|---|---|---|
| **TI BQ25570** | MPPT: samples Voc, sets load to ~80% Voc | ~330 mV | Regulated + LiPo charge | Most commonly cited for kinetic harvesters |
| **e-peas AEM10941** | MPPT, dual output | ~380 mV | Two regulated rails | Good for split always-on / shed-able architecture |
| **Analog Devices LTC3588** | Fixed internal bridge + LDO | ~1.8 V (no cold-start assist) | Adjustable DC | Lower complexity, less suitable for ultra-low-flow |

For products where the extra ~$2–4 BOM cost is acceptable, these chips make the static vs. dynamic load question largely moot. For cost-constrained products, the static Reff approach captures the majority of available power (demonstrated to be ~86% of theoretical max on the Zurn P6900 at the tested operating range).

**Decision rule:**
- Cost-sensitive / simple load: use static Reff or Rmax from bench data.
- Mid-tier: pre-programmed lookup table (§ above), ~$2–5 BOM.
- Performance-sensitive or wide operating range: MPPT IC, ~$2–4, automatic.

---

### A2 — Expand §6.3 to include MOSFET load-disconnect design pattern
**Location:** Section 6.3 "Open-Circuit Sensing Mode"
**Type:** Expand existing section with new design pattern

Replace or augment §6.3 with the following:

---

### 6.3 Open-Circuit Sensing Mode & MOSFET Load Disconnect

With no load (R_load = ∞), electromagnetic braking is removed and the turbine spins more freely, pushing minimum detectable flow below the loaded Q_start. Flow is read from AC frequency or Hall pulse count.

This can be implemented in hardware with a **logic-controlled MOSFET on the load path**:

- A low-power comparator (~1–10 μA quiescent) monitors the Hall signal or raw AC.
- When flow drops below a threshold Q_threshold, the MCU (or comparator directly) opens the MOSFET, disconnecting the load. The turbine now spins freely and sensing accuracy is maximized at low flow.
- When flow rises above Q_threshold (with hysteresis to avoid chattering), the MOSFET closes and the turbine begins generating.

**Three-state operating model:**

| State | Condition | MOSFET | Power Source | Notes |
|---|---|---|---|---|
| **Sleep** | No flow detected | Open | Battery only | MCU in deep sleep; comparator watching for pulse |
| **Sense-only** | Flow below Q_threshold | Open | Battery | Braking removed; maximum low-flow sensitivity |
| **Generate + Sense** | Flow above Q_threshold | Closed | Turbine + battery | Turbine charges battery; Hall or frequency used for sensing |

Hysteresis band should be set per turbine based on bench data for Q_start (loaded) vs. Q_start (open-circuit). This prevents the system from toggling at the threshold boundary.

> This pattern is architecturally equivalent to Config 4 in §7.1 (Generator + internal Hall + battery) but makes the load-disconnect state explicit as a design choice rather than a passive fallback.

---

### A3 — Add coil resistance / application fit subsection to §3.5 or §3.4
**Location:** Section 3.5 (Physics), or as a new §3.4.x after coil configurations table
**Type:** New subsection

Add the following:

---

#### Coil Resistance and Application Fit

Coil DC resistance (R_coil) is a quick indicator of a generator's electrical character and helps predict what applications and load types it is best suited for.

**How R_coil is set by construction:**

- More turns of wire → proportionally higher open-circuit voltage (V_oc = N·B·A·ω), but also higher resistance (more wire length).
- Thinner wire → higher resistance per unit length, compounding the effect of more turns.
- Result: high-turn / thin-wire coils have high R_coil and high voltage-per-RPM; low-turn / thick-wire coils have low R_coil and low voltage-per-RPM but can deliver more current.

**Important caveat — inductive reactance:** The optimal load resistance measured on the bench (R_eff or R_max) is always higher than R_coil, often significantly so. This is because inductive reactance (ωL) adds to the source impedance at the AC frequencies produced by these turbines. R_coil alone does not predict optimal load; it must be measured. However, R_coil is still a fast qualitative indicator.

| | High R_coil (many turns, thin wire) | Low R_coil (few turns, thick wire) |
|---|---|---|
| **Voltage at low RPM** | Higher — turns compensate for slow rotation | Lower — needs faster spin |
| **Current delivery** | Lower | Higher |
| **Optimal load impedance** | High | Low |
| **Best flow range** | Low-flow fixtures (faucet, sink) | Higher-flow / higher-pressure (shower, bottle filler) |
| **Energy storage pairing** | Boost converters, higher-voltage rails | Direct supercap, low-voltage LDO |
| **Example** | M6 propeller (R_coil = 161.6 Ω) | Zurn P6900 (R_coil = 3.6 Ω) |

This is one of the columns that will be populated in the generator catalogue (Appendix B) as bench testing proceeds.

---

### A4 — Tighten power tier table in §8.1
**Location:** Section 8.1, "Power tier menu" table
**Type:** Correction + expansion

Replace the current power tier table with:

| Tier | Avg. Continuous Power | Notes |
|---|---|---|
| **Sensor only (wake-on-flow)** | ~0.05–0.2 mW | MCU in deep sleep; wakes on Hall pulse; duty cycle is very low |
| **Sensor only (always-on MCU)** | ~1–5 mW | MCU polling Hall continuously; no radio |
| **Sensor + solenoid / proximity** | ~5–15 mW | Add solenoid drive or IR hand-detect; bursty current spikes |
| **Low-power display** | ~10–20 mW | Adds LCD or e-ink; e-ink is near-zero in hold state |
| **BLE / radio connectivity** | ~20–50 mW peak (bursty) | Needs energy storage to buffer transmit bursts; average may be 2–5 mW with low duty cycle |

**Also add a price tier table** (placeholder values — fill in with actual component/unit cost data):

| Price Tier | Target Unit Cost | Characteristic |
|---|---|---|
| **Sensor-only budget** | < $5 | Turbine + Hall only; no radio |
| **Mid-tier** | $5–$15 | Turbine + MCU + BLE SoC + small battery |
| **IoT full** | $15–$35 | Above + MPPT IC + cloud connectivity |
| **Replace existing** | < $17.33 | Haws PID cost-reduction target (Digiflow benchmark) |

---

### A5 — Add sensing accuracy vs. cumulative volume section (new §8.x or within §9)
**Location:** New subsection, either §8.3 or within §9 application examples
**Type:** New content

Add a subsection that explicitly connects sensing method to cumulative volume accuracy, particularly for NSF-regulated applications:

Key points to cover:
- Voltage-at-load sensing (Method 3 from §6.2) is affected by inlet pressure variation — same flow rate at different pressures produces different voltage. Cumulative volume calculated from voltage will drift with building pressure.
- Frequency-based sensing (Method 2) and Hall pulse counting (Method 1) are load-independent and pressure-independent — they are the correct methods for certified cumulative volume tracking.
- For Haws / NSF compliance: the PID must track "actual water volume by physical displacement." This means Hall pulse count or AC frequency integration is required — voltage-based sensing is not compliant for this application.
- Recommend calling out explicitly in §9.2 (Haws) that Config 3 (power at fixed load) is not suitable for the PID function; Configs 4 or 5 with Hall sensing are required.

---

## 🟡 Narrative / Focus Improvements

### N1 — Shorten §3.5 physics derivation
**Location:** Section 3.5
**Type:** Trim / restructure

The EMF equation and efficiency formula are immediately undermined by the conclusion that bench testing is needed anyway. Suggest:
- Keep the equation block as a callout or collapsed section.
- Lead with the practical takeaway: "Output scales with ω² and therefore roughly with Q². But friction, bearing losses, and electromagnetic saturation create a practical sweet spot that cannot be calculated from geometry — it must be measured."
- Move the full derivation to an appendix or footnote for reference.

### N2 — Consolidate ΔP_oc footnote in §4.1
**Location:** Section 4.1, the block quote on ΔP_oc
**Type:** Trim

The note on why ΔP_oc is optional is correct but defensive. Condense to one sentence in a footnote: "ΔP at open circuit is optional; because efficiencies are typically under 10%, the loaded ΔP curve is nearly identical and sufficient for system pressure budget calculations."

### N3 — Add explicit deliverable statement to §1 Overview
**Location:** Section 1, end of opening paragraph or as a new bullet
**Type:** Addition

Add: "The concrete output of this work is a populated turbine catalog with bench-validated Cost/Reward curves, a selection framework that maps application profiles to turbine choices, and reference architectures for each power tier — sufficient for a product team to specify a turbine and circuit topology without re-running the underlying analysis."

### N4 — Rectification table in §6.1 can be moved to Appendix B
**Location:** Section 6.1
**Type:** Restructure suggestion

The rectification table (single-coil → bridge, 3-phase → 6-diode, dual-coil → separate) is useful but interrupts the sensing narrative. Consider moving it to Appendix B as a catalog column, or to a short "Electrical Interface" section in the appendix. Flag for review — do not move automatically without confirming it doesn't break the flow of §6.

---

## 📋 Catalogue / Data Gaps (Not Text Changes — Track for Testing Roadmap)

- Appendix B (Generators) needs these columns populated from bench data for each turbine:
  - R_coil (Ω)
  - Q_start (GPM, open-circuit and loaded)
  - R_eff or R_max (Ω)
  - Peak power (mW) at R_eff/R_max
  - Peak ΔP (PSI) at rated flow
  - Stator claw subtype (single-sided / dual-sided symmetric / dual-sided asymmetric / belt / spoke)
  - Price (unit cost)
  - Application notes

- Turbines pending bench characterization (not yet in results):
  - Toto EcoPower
  - Toto EDV (single-sided claw variant)
  - Toto 10s Dynamo (dual-sided symmetric)
  - F50 (spoke/hub — deferred, out of scope for now)
  - Any additional candidates identified in §8 selection process

---

*Last updated: 2026-05-05. Add new items above the catalogue gap section.*

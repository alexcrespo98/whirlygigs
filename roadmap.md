# Whirlygigs Project Roadmap

**Goal:** Deliver a complete turbine selection framework for Watts Water Technologies and acquired brands (Bradley, Haws) covering rotary flow sensing and micro-hydro power generation in the 0–4 GPM range. Output is a populated turbine catalogue with bench-validated Cost/Reward curves, a data-driven selection tool, and reference architectures per power tier.

**Scope:** 0–4 GPM fixtures (faucets, bottle fillers, kitchen sinks, showers). Higher flow rates (>4 GPM) and continuous-flow industrial applications are explicitly out of scope for this phase.

---

## Phase 1 — Framework and Documentation (current)

- [x] Technology survey: flow sensing methods, turbine types, coil configurations
- [x] Bench characterization methodology defined (R_eff / R_max rule, Cost/Reward chart)
- [x] Two turbines fully characterized: Zurn P6900 (R_eff case) and M6 Axial Propeller (R_max case)
- [x] Selection framework defined (§8 of flowsense_iot.md)
- [x] Two application examples worked: Bradley commercial faucet, Haws bottle filler PID
- [x] Fixture usage profiles defined with data-driven energy tiers (§8.4)
- [x] Factual corrections applied: claw pole cycle count, stator claw subtypes, TOC anchors
- [x] New content added: MPPT ICs, MOSFET load-disconnect pattern, coil resistance application fit
- [ ] Apply narrative improvements N1, N2, N4 (shorten §3.5, consolidate ΔP note, move rectification table)
- [ ] A1171 Hall sensor bench validation against live GEMS 238600

---

## Phase 2 — Catalogue Completion

For each remaining turbine, run the full bench protocol (see test_data_schema.md):

| Turbine | Status | Notes |
|---|---|---|
| Zurn P6900 | Done | R_eff = 80 Ω, Q_eff = 0.33 GPM |
| M6 Axial Propeller | Done | R_max ≈ 275 Ω, no interior peak |
| Toto EcoPower | Not started | Belt, single coil |
| Toto EDV | Not started | Claw pole, dual coil, single-sided claws |
| Toto 10s Dynamo (EDV462/EDV561) | Not started | Claw pole, dual coil, dual-sided symmetric |
| DH24 (or similar) | Not started | Acquired — confirm model name; schedule bench session |
| F50 | Deferred | Spoke/hub, out of scope for now |

Per-turbine deliverable: Cost/Reward chart (ΔP vs Q and Power vs Q), Q_start loaded, Q_start OC, R_coil, R_eff or R_max, integration status, battery/cap recommendation.

---

## Phase 3 — Selection Tool

Build an AI-accessible or interactive tool that:

1. Takes inputs: fixture type, usage environment (low/medium/high), function tier (sense only / sense + solenoid / sense + display / IoT), pressure budget, price budget
2. Assigns an energy tier from §8.4
3. Filters catalogue by Q_start vs fixture flow rate, ΔP vs pressure budget
4. Returns ranked turbine candidates with Cost/Reward match rationale
5. Asks clarifying questions if inputs are ambiguous (retrofit vs new design; regulated vs raw AC output needed)

Data source: populated catalogue entries from Phase 2.

---

## Phase 4 — Test Rig (Future — Blocked on DH)

Design and build a calibrated bench test rig:
- Calibrated flow meter upstream
- Proximal and distal pressure taps
- Removable turbine section (calibration pass without turbine)
- Switched resistor load bank
- Simultaneous logging: voltage, current, AC frequency, Hall pulse, temperature
- Controlled pressure source

This rig enables faster, more consistent characterization of new turbines as they are acquired.

---

## Key Open Questions

1. What is the minimum startup flow of each remaining turbine vs. the 0.35 GPM faucet threshold?
2. Does the A1171 Hall sensor reliably trigger at 100 G from the GEMS 238600?
3. Which turbines can be used as-is vs. which require a custom PCB, housing, or coil tap?
4. For the Haws PID application: which turbine clears the NSF physical-displacement requirement and fits inline in the bottle filler supply line?

---

## Presentation (Meeting — 2026-05-14)

Target: Watts stakeholders. Goal is for a product team to identify their fixture and see a defensible turbine recommendation.

Outline:
1. Problem — Watts has fixture lines that need sensing or self-powered IoT with no systematic turbine selection process
2. Framework — Cost/Reward methodology, selection axes (fixture profile × function tier)
3. Live examples — Bradley faucet, Haws PID
4. Catalogue status — two turbines done, four pending
5. Selection tool — what it will do and what it needs to work (populated catalogue)
6. Roadmap — Phase 2 (catalogue completion), Phase 3 (tool), Phase 4 (test rig)
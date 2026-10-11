# Haris Zafar | Renewable Energy & Power Systems Engineer

Electrical Engineer specializing in power system numerical analysis, renewable integration, battery energy storage electro-thermal dynamics, and microgrid inverter control.

---

## Featured Engineering Simulation Solvers

| Project Repository | Technical Domain | Key Engineering Capabilities | Stack |
| :--- | :--- | :--- | :--- |
| ⚡ **[Power Systems Newton-Raphson Solver](https://github.com/hariszafar740-lang/power-systems-newton-raphson-solver)** | Power Systems | $N$-bus admittance matrix ($Y_{bus}$), Jacobian construction, power mismatch convergence | Python, NumPy, pytest |
| ☀️ **[Solar PV Dynamic MPPT Solver](https://github.com/hariszafar740-lang/solar-pv-mppt-dynamic-solver)** | Photovoltaics | Single-diode PV dynamics, P&O MPPT control loops, $I\text{--}V$ / $P\text{--}V$ characteristic engines | Python, NumPy, Matplotlib |
| 🔋 **[BESS SoC Dynamics Solver](https://github.com/hariszafar740-lang/bess-soc-dynamics-solver)** | Energy Storage | 1RC equivalent-circuit model, Coulomb-counted SoC, illustrative lumped thermal balance (not a safety prediction) | Python, NumPy, Matplotlib |
| 🌐 **[Grid-Forming Inverter Control Solver](https://github.com/hariszafar740-lang/inverter-grid-control-solver)** | Power Electronics | $P\text{--}\omega$ / $Q\text{--}V$ droop loops, virtual inertia/impedance, current-limited sag-response scenario (not certification) | Python, NumPy, pytest |
| 🌱 **[Energy Transition Model](https://github.com/hariszafar740-lang/energy-transition-model)** | Energy Systems | PyPSA capacity expansion with synthetic representative-day availability and stated annualization assumptions | Python, PyPSA, HiGHS, pandas |

---

📌 **Central Portfolio Repository:** [ee-portfolio-master](https://github.com/hariszafar740-lang/ee-portfolio-master)

## Validation scope

The linked repositories contain independent models and tools; their outputs do not represent one coupled physical system. Tests verify the documented software scenarios; they are not evidence of hardware behavior, standards compliance, or engineering certification. The PV and energy-transition examples use stated model/profile assumptions that require validated project-specific data before real-world interpretation.

This profile repository contains documentation only. Its regression suite checks the project links and claims in this README:

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q tests/
```

# Haris Zafar, power systems, storage and energy-transition modelling

Renewable-energy and power-systems engineer.
Six Python repositories, 899 tests, and every published number reproduced by a test or a committed dataset.

I write the solvers, the tests that pin their numbers, and the pages that show the results, and a number that cannot be rerun seems to me not worth publishing.

[Open the energy-transition workbench](https://hariszafar740-lang.github.io/energy-transition-model/workbench/) · [grid explorer](https://hariszafar740-lang.github.io/power-systems-newton-raphson-solver/) · [portfolio dashboard](https://hariszafar740-lang.github.io/ee-portfolio-master/)

## Verified results

| Repository | Verified result | Tests |
| --- | --- | --- |
| [Energy Transition Model](https://github.com/hariszafar740-lang/energy-transition-model) | LP strong-duality LCOE 28.0555 $/MWh, duality gap 7.45e-09 | 285 |
| [Power Systems Newton-Raphson Solver](https://github.com/hariszafar740-lang/power-systems-newton-raphson-solver) | IEEE 14-bus against pandapower to < 5e-7 p.u.; IEEE 30-bus to < 5e-6 p.u. | 72 |
| [Solar PV Dynamic MPPT Solver](https://github.com/hariszafar740-lang/solar-pv-mppt-dynamic-solver) | CEC extraction < 1e-8 A against pvlib Lambert-W; EN 50530 Sera dP-P&O 99.94 % | 230 |
| [BESS SoC Dynamics Solver](https://github.com/hariszafar740-lang/bess-soc-dynamics-solver) | OCV and dU/dT tables < 5 uV against PyBaMM 26.10.1.1 | 185 |
| [Grid-Forming Inverter Control Solver](https://github.com/hariszafar740-lang/inverter-grid-control-solver) | 47.95 A peak under a 0.15 p.u. sag, inside the 48 A limit | 116 |
| [Central Portfolio Repository](https://github.com/hariszafar740-lang/ee-portfolio-master) | Re-runs every number above, then gates on ruff, bandit, zizmor, pip-audit | 11 |

## Scope

The six repositories are independent models; they do not represent one coupled physical system.
Passing tests verify the documented software scenarios and are not evidence of hardware behavior, standards compliance, or engineering certification.
The BESS thermal model is not a safety prediction and the inverter fault ride-through scenario is not certification.

## Local checks

python -m pip install -r requirements-dev.txt python -m pytest -q tests/

Issues and discussions are open on all six repositories.
This page is checked by its own test suite on every push.

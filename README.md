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
| [Central Portfolio Repository](https://github.com/hariszafar740-lang/ee-portfolio-master) | Re-runs the test suites behind every number above on Python 3.10 and 3.11, then deploys the dashboard | 11 |

**All five in one environment:** [energy-systems-benchmarks](https://github.com/hariszafar740-lang/energy-systems-benchmarks) installs every package from PyPI and re-checks the headline number in each README.

**Engineering note:** [what each number rests on, and where it breaks](notes/five-packages.md)

**Close-out:** [what exists, what it does not claim, and the one command that re-checks it](notes/close-out.md)

<!-- verify:start -->

## Verify it yourself

The table above is built by running these commands against the published
wheels, and the comment after each line is what it printed.

Versions today: nr-powerflow-solver 1.0.2, pv-mppt-solver 1.0.1,
bess-soc-dynamics-solver 1.0.0, inverter-grid-control-solver 1.0.0,
energy-transition-model 1.0.0.

```bash
pip install nr-powerflow-solver pv-mppt-solver bess-soc-dynamics-solver \
            inverter-grid-control-solver energy-transition-model

nr-powerflow solve --case ieee14 --format json  # mismatch 5.98e-08 p.u. in 3 iterations
pv-mppt iv -g 1000 -t 25 --json                 # P_mpp 300.115 W, fill factor 74.8 pct
bess-sim pulse --json                           # min V 3.181 V, peak 30.97 C, SoC 0.25
gfm-sim triad --json                            # largest real eigenvalue -3.030 1/s
etm-sim --duality-report                        # LCOE 28.0555, gap -7.45e-09
```

Every number is re-checked on each push by [energy-systems-benchmarks](https://github.com/hariszafar740-lang/energy-systems-benchmarks),
on two Python versions, installing from PyPI rather than from a source tree.

<!-- verify:end -->

## Scope

The six repositories are independent models; they do not represent one coupled physical system.
Passing tests verify the documented software scenarios and are not evidence of hardware behavior, standards compliance, or engineering certification.
The BESS thermal model is not a safety prediction and the inverter fault ride-through scenario is not certification.

## Local checks

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q tests/
```

Issues and discussions are open on all six repositories.
This page is checked by its own test suite on every push.

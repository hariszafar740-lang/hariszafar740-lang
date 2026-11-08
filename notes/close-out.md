# Close-out

Five Python packages for power systems, one benchmark that installs all five
from PyPI and re-checks them, and the pages that say what the numbers do and
do not mean. Every figure below is read from those repositories when this file
is rebuilt, and one command re-derives all of it.

## The five packages

| Package | Version | The number it defends | The command that prints it |
|:--- |:--- |:--- |:--- |
| [nr-powerflow-solver](https://github.com/hariszafar740-lang/power-systems-newton-raphson-solver) - sparse Newton-Raphson load flow | 1.0.2 | mismatch 5.98e-08 p.u. in 3 iterations | `nr-powerflow solve --case ieee14 --format json` |
| [pv-mppt-solver](https://github.com/hariszafar740-lang/solar-pv-mppt-dynamic-solver) - single-diode PV with global MPPT | 1.0.1 | P_mpp 300.115 W, fill factor 74.8 pct | `pv-mppt iv -g 1000 -t 25 --json` |
| [bess-soc-dynamics-solver](https://github.com/hariszafar740-lang/bess-soc-dynamics-solver) - a 1RC battery cell with a thermal layer | 1.0.0 | min V 3.181 V, peak 30.97 C, SoC 0.25 | `bess-sim pulse --json` |
| [inverter-grid-control-solver](https://github.com/hariszafar740-lang/inverter-grid-control-solver) - a grid-forming inverter model | 1.0.0 | largest real eigenvalue -3.030 1/s | `gfm-sim triad --json` |
| [energy-transition-model](https://github.com/hariszafar740-lang/energy-transition-model) - a capacity-expansion LP | 1.0.0 | LCOE 28.0555, gap -7.45e-09 | `etm-sim --duality-report` |

All five are on PyPI under MIT, each with a public release: nr-powerflow-solver v1.0.2, pv-mppt-solver v1.0.1, bess-soc-dynamics-solver v1.0.0, inverter-grid-control-solver v1.0.0, energy-transition-model v1.0.0.

## What holds those numbers

1. Each repository runs its own tests on every push, and the headline number in
   its README is asserted there.
2. [energy-systems-benchmarks](https://github.com/hariszafar740-lang/energy-systems-benchmarks) installs the five published distributions
   from PyPI, runs the same commands, and asserts the same figures on Python 3.11
   and 3.12. A release that stops matching its README fails there rather than in
   somebody else's notebook.
3. `tools/check_launch.py` re-reads the check table and fails if the launch kit
   has drifted from it, on every push that touches the kit and every Monday.

## What is not claimed

- No hardware validation. These are software results at stated operating points.
- No certification, and no standards or grid-code compliance.
- The five are independent models, not one coupled physical system, and nothing
  here claims they compose into one.
- Model output is only as good as the assumptions in it. [The engineering
  note](https://github.com/hariszafar740-lang/hariszafar740-lang/blob/main/notes/five-packages.md) says, for each model, which assumption would break its number first.

Passing tests show the software does what the documentation says. They are not
evidence about a machine, a site or a grid.

## What is not done

Nothing here has been announced. No Show HN, Reddit, X or LinkedIn post has been
made, and nothing in these repositories claims one was. The text for those posts is
written, length-checked against each platform's limit and regenerated from the
check table every time the launch box runs: `notes/launch.md`. If you are reading
this before that morning, that page is the honest state of it.

This paragraph is the one thing on the page that no machine keeps true for you.
When a post goes out, rebuild this file and delete it - and the guard will fail
until you do, which is the point.

## Check it yourself, in one command

The numbers above come from the published packages, not from a source tree:

```bash
pip install nr-powerflow-solver pv-mppt-solver bess-soc-dynamics-solver inverter-grid-control-solver energy-transition-model

nr-powerflow solve --case ieee14 --format json  # mismatch 5.98e-08 p.u. in 3 iterations
pv-mppt iv -g 1000 -t 25 --json  # P_mpp 300.115 W, fill factor 74.8 pct
bess-sim pulse --json  # min V 3.181 V, peak 30.97 C, SoC 0.25
gfm-sim triad --json  # largest real eigenvalue -3.030 1/s
etm-sim --duality-report  # LCOE 28.0555, gap -7.45e-09
```

And the claims about those numbers, from a clean clone, with no token:

```bash
git clone https://github.com/hariszafar740-lang/hariszafar740-lang.git
cd hariszafar740-lang
python tools/verify_release.py
```

It reads PyPI, the five repositories, the releases, the check table and the files
in that clone, prints one line per claim, and exits non-zero if any of them has
stopped being true.

## Where everything is

| What | Where |
|:--- |:--- |
| the check table, rebuilt by CI | https://github.com/hariszafar740-lang/energy-systems-benchmarks |
| what each number rests on, and where it breaks | https://github.com/hariszafar740-lang/hariszafar740-lang/blob/main/notes/five-packages.md |
| paste-ready launch text, and the guard over it | https://github.com/hariszafar740-lang/hariszafar740-lang/blob/main/notes/launch.md |
| the command that re-checks this page | https://github.com/hariszafar740-lang/hariszafar740-lang/blob/main/tools/verify_release.py |

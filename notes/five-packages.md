# Five packages, and the number each one has to defend

I published five Python packages over the last few weeks. Each came out of a problem I
kept re-solving by hand: a load flow I wanted to invert quickly, a shading curve I did
not want to derive again, a battery pulse I wanted to replay with a different chemistry,
an inverter model to put grid-forming control next to grid-following, and a capacity
expansion run I wanted to hang a risk layer on.

What decided whether each one got published was not the model. It was whether I could
write a test that fails when the number in the README stops being true. Below is what
each package claims, what the check actually asserts, and the assumption most likely to
break it. Every figure is copied from the check table, so it cannot drift from the code.

## Load flow: nr-powerflow-solver 1.0.2

`nr-powerflow solve --case ieee14 --format json` prints **mismatch 5.98e-08 p.u. in 3 iterations**.

The check asserts: mismatch below 1e-6 p.u. in at most 6 iterations.

The two case files are pinned to MATPOWER's `case14` and `case_ieee30`, so a solver bug
shows up as a mismatch instead of a plausible-looking voltage profile. The sparsity
figures only mean something for the ordering used here, so read them as a property of
this implementation and not of the network.

## Solar: pv-mppt-solver 1.0.1

`pv-mppt iv -g 1000 -t 25 --json` prints **P_mpp 300.115 W, fill factor 74.8 pct**.

The check asserts: P_mpp 300.115 W within 0.05 W.

The diode parameters sit close to the CEC module data and the extraction is compared
against pvlib's Lambert-W solution. Partial shading is where these numbers stop being
transferable: the bypass diodes here are ideal, and a real module adds mismatch,
thermal gradients and cell-to-cell variation that this does not represent.

## Batteries: bess-soc-dynamics-solver 1.0.0

`bess-sim pulse --json` prints **min V 3.181 V, peak 30.97 C, SoC 0.25**.

The check asserts: voltage inside the cell window, SoC ends at 0.25.

The open-circuit and entropic tables are cross-checked against PyBaMM's
parameterisations, which is a strong check on the tables and no check at all on the
pack. The convective coefficient is the weakest input in the thermal model, and the
aging law is semi-empirical.

## Inverters: inverter-grid-control-solver 1.0.0

`gfm-sim triad --json` prints **largest real eigenvalue -3.030 1/s**.

The check asserts: largest real eigenvalue below zero.

This is a small-signal result at one operating point, with averaged models. It says the
linearisation is stable there. It says nothing about switching behaviour, nothing about
a fault elsewhere on the curve, and nothing about compliance with a grid code.

## Transition: energy-transition-model 1.0.0

`etm-sim --duality-report` prints **LCOE 28.0555, gap -7.45e-09**.

The check asserts: LCOE 28.0555 /MWh and abs(gap) below 1e-6.

The duality residual is the useful part: it ties the LCOE the model reports to the
prices it solves for, so a mis-specified constraint tends to show up as a non-zero gap
rather than as a slightly different answer. The inputs are the soft spot. The profiles
are synthetic, the annualisation is stated, and the cost assumptions are mine.

## Why the five are checked in one place

Each repository runs its own tests, and that only proves a package is consistent with
itself. The sixth repository, [energy-systems-benchmarks](https://github.com/hariszafar740-lang/energy-systems-benchmarks),
installs the five published distributions from PyPI into a throwaway directory, calls
each one, and asserts the sentence in the table above. It runs on two Python versions
and keeps the raw JSON it produced.

That is the check I care about most, because it fails for the reason a user would hit: a
release that no longer does what its README says. It installs from PyPI rather than from
the source tree, so the version that gets tested is the version a stranger downloads.

## What I am not claiming

No certification, no hardware prediction, no standards compliance. The tests verify the
software behaviour described here. Model output is only as good as the assumptions
listed above, and the two I would look at first are the convective coefficient in the
battery model and the cost inputs in the transition model.

If a number here is wrong, or the reasoning behind it is thin, open an issue on the
repository. I would rather fix it than defend it.

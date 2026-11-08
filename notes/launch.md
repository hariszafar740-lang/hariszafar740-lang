# Launch kit

Paste-ready text for the four places this gets announced. Nothing here
has been posted, and nothing in this profile links to it.

Every number below is copied from the check table in

  https://github.com/hariszafar740-lang/energy-systems-benchmarks

at the time this file was built, so if a package releases, rebuild it
with the launch box rather than editing a number by hand.

Licence on all five repositories: MIT.

Declared dependencies across the five, from the PyPI metadata: highspy, matplotlib, numpy, pandas, pypsa, scipy.

## 1. Hacker News - Show HN

Title (70 chars, limit 80):

```
Show HN: Five power-systems solvers, each pinned to a number by a test
```

Body:

```
I write power-systems models - load flow, solar, batteries, grid-forming inverters, capacity expansion - and the thing I kept getting wrong was trusting a number in a README that no longer matched the code.

So each of the five is a small Python package (MIT, on PyPI) with one headline number, pinned by a test in its own repository:

  load flow       mismatch 5.98e-08 p.u. in 3 iterations
  solar PV        P_mpp 300.115 W, fill factor 74.8 pct
  battery cell    min V 3.181 V, peak 30.97 C, SoC 0.25
  inverter        largest real eigenvalue -3.030 1/s
  expansion       LCOE 28.0555, gap -7.45e-09

A sixth repository installs all five from PyPI and asserts those numbers on Python 3.11 and 3.12. A release that stops doing what its README says fails there, rather than in somebody else's notebook.

What this is not: no hardware validation, no standards compliance, no certification. Every model has an assumption that would break it first, and the note below names that assumption for each one.

  code:  https://github.com/hariszafar740-lang/hariszafar740-lang
  note:  https://github.com/hariszafar740-lang/hariszafar740-lang/blob/main/notes/five-packages.md
```

## 2. Reddit

Title (73 chars, limit 300):

```
Five power-systems packages where every README number is pinned by a test
```

Body (1532 chars, limit 40000):

```
I have been building small power-systems solvers in Python and got tired of README numbers that quietly stop being true, so each package now has one headline figure that a test asserts, and a sixth repository installs all five from PyPI and re-checks them on Python 3.11 and 3.12.

What is in it, with the number each one defends:

- **Load flow** (nr-powerflow-solver 1.0.2) - `nr-powerflow solve --case ieee14 --format json` prints mismatch 5.98e-08 p.u. in 3 iterations.
- **Solar PV** (pv-mppt-solver 1.0.1) - `pv-mppt iv -g 1000 -t 25 --json` prints P_mpp 300.115 W, fill factor 74.8 pct.
- **Battery cell and thermal** (bess-soc-dynamics-solver 1.0.0) - `bess-sim pulse --json` prints min V 3.181 V, peak 30.97 C, SoC 0.25.
- **Grid-forming inverter** (inverter-grid-control-solver 1.0.0) - `gfm-sim triad --json` prints largest real eigenvalue -3.030 1/s.
- **Capacity expansion** (energy-transition-model 1.0.0) - `etm-sim --duality-report` prints LCOE 28.0555, gap -7.45e-09.

All MIT, on PyPI. Declared dependencies, across the five: highspy, matplotlib, numpy, pandas, pypsa, scipy.

What I would find useful from this sub: which of these numbers you would have checked differently, and where the assumption is too generous. The note below says which assumption I think is weakest in each model - I would rather be told now than after I have quoted a figure at someone.

  https://github.com/hariszafar740-lang/hariszafar740-lang
  https://github.com/hariszafar740-lang/hariszafar740-lang/blob/main/notes/five-packages.md
```

## 3. X - four posts, in order

Post 1 (215 chars, limit 280):

```
Five power-systems Python packages. One rule: the headline number in each README is pinned by a test, or it does not ship.

Load flow, solar, battery, grid-forming inverter, capacity expansion. All MIT, all on PyPI.
```

Post 2 (223 chars, limit 280):

```
The numbers, as the check table prints them:

mismatch 5.98e-08 p.u. in 3 iterations
P_mpp 300.115 W, fill factor 74.8 pct
min V 3.181 V, peak 30.97 C, SoC 0.25
largest real eigenvalue -3.030 1/s
LCOE 28.0555, gap -7.45e-09
```

Post 3 (173 chars, limit 280):

```
A sixth repository installs all five from PyPI and asserts those numbers on Python 3.11 and 3.12. A release that stops matching its README fails there, not in your notebook.
```

Post 4 (213 chars, limit 280):

```
No hardware validation, no certification, no grid-code compliance. The note says which assumption is weakest in each model:
https://github.com/hariszafar740-lang/hariszafar740-lang/blob/main/notes/five-packages.md
```

## 4. LinkedIn

Body (1545 chars, limit 3000):

```
Five Python packages, one rule.

I build power-systems models: sparse Newton-Raphson load flow, single-diode PV with global MPPT, a 1RC battery cell with a thermal layer, a grid-forming inverter model, and a capacity-expansion LP. Each is published on PyPI under MIT.

The rule is that every one of them has one headline number in its README, and a test in that repository fails when the number stops being true:

- **Load flow** (nr-powerflow-solver 1.0.2) - `nr-powerflow solve --case ieee14 --format json` prints mismatch 5.98e-08 p.u. in 3 iterations.
- **Solar PV** (pv-mppt-solver 1.0.1) - `pv-mppt iv -g 1000 -t 25 --json` prints P_mpp 300.115 W, fill factor 74.8 pct.
- **Battery cell and thermal** (bess-soc-dynamics-solver 1.0.0) - `bess-sim pulse --json` prints min V 3.181 V, peak 30.97 C, SoC 0.25.
- **Grid-forming inverter** (inverter-grid-control-solver 1.0.0) - `gfm-sim triad --json` prints largest real eigenvalue -3.030 1/s.
- **Capacity expansion** (energy-transition-model 1.0.0) - `etm-sim --duality-report` prints LCOE 28.0555, gap -7.45e-09.

A sixth repository installs the five published packages from PyPI and asserts those same numbers on Python 3.11 and 3.12, so release drift is caught where a user would hit it.

What I am not claiming: no hardware validation, no certification, no standards compliance. The engineering note linked below says, for each model, which assumption would break its number first.

Code: https://github.com/hariszafar740-lang/hariszafar740-lang

#powersystems #python #energy #simulation
```

## Answers bank

Short, honest replies for the questions this will attract. Answer in your
own words; these are the facts to keep to.

**Why five repositories instead of one?**

They are independent models, not one coupled system, and each has its own release cycle and its own test suite. The benchmark repository is the only place they are installed together, and that is the only claim it makes.

**Has any of this been validated against real hardware?**

No. Every number is a software result. The profile page says so, the note says so, and no post claims otherwise.

**Why not just use pandapower, PyPSA or pvlib?**

For the parts they solve better, use them. The load flow is checked against MATPOWER's case files, the PV extraction against pvlib's Lambert-W solution, and the battery tables against PyBaMM's parameterisations. These packages exist because I wanted the specific decomposition and the specific test, not because the references are wrong.

**What happens when a number changes?**

The test in that repository fails first, then the benchmark repository fails when it installs the published package. The note and the launch kit are both generated from the check table, and the launch check compares them every time the kit is rebuilt, so a stale figure is caught rather than copied.

**Is any of it certified or grid-code compliant?**

No. Nothing here is certification, hardware prediction or standards compliance, and the pages say that in those words.

**Where are the tests?**

In each repository under tests/, run on every push. The numbers you see in the tables come from the check table in energy-systems-benchmarks, which installs the five published distributions from PyPI and asserts the same figures on Python 3.11 and 3.12. The table is rewritten by `python bench.py --update-readme`.

## Every claim, and where it is checked

| Package | The number | Command | Checked by |
|:--- |:--- |:--- |:--- |
| `nr-powerflow-solver` 1.0.2 | mismatch 5.98e-08 p.u. in 3 iterations | `nr-powerflow solve --case ieee14 --format json` | the check table row, asserted by power-systems-newton-raphson-solver's own tests and by energy-systems-benchmarks |
| `pv-mppt-solver` 1.0.1 | P_mpp 300.115 W, fill factor 74.8 pct | `pv-mppt iv -g 1000 -t 25 --json` | the check table row, asserted by solar-pv-mppt-dynamic-solver's own tests and by energy-systems-benchmarks |
| `bess-soc-dynamics-solver` 1.0.0 | min V 3.181 V, peak 30.97 C, SoC 0.25 | `bess-sim pulse --json` | the check table row, asserted by bess-soc-dynamics-solver's own tests and by energy-systems-benchmarks |
| `inverter-grid-control-solver` 1.0.0 | largest real eigenvalue -3.030 1/s | `gfm-sim triad --json` | the check table row, asserted by inverter-grid-control-solver's own tests and by energy-systems-benchmarks |
| `energy-transition-model` 1.0.0 | LCOE 28.0555, gap -7.45e-09 | `etm-sim --duality-report` | the check table row, asserted by energy-transition-model's own tests and by energy-systems-benchmarks |

| Claim | Where it is checked |
|:--- |:--- |
| all five install together from PyPI | https://github.com/hariszafar740-lang/energy-systems-benchmarks, on Python 3.11 and 3.12 |
| every page shows how to install it | each repository's README, re-read every time this file is built |
| every repository carries a public release | the GitHub releases API, unauthenticated |
| the dependency list above is what the packages declare | each package's PyPI metadata, read when this file was built |
| the note explains each model's weakest assumption | https://github.com/hariszafar740-lang/hariszafar740-lang/blob/main/notes/five-packages.md |
| nothing is claimed about hardware, certification or grid codes | the profile page's own tests, in https://github.com/hariszafar740-lang/hariszafar740-lang/blob/main/tests/test_profile_readme.py |

## Before you paste

The limits above are the platforms' rules. The list below is judgement, not
rule - yours to overrule.

1. Post one place first and stay with it for an hour. Four at once means
   four threads you are not answering.
2. Answer the first critical comment in public and without a defence first.
   "You are right, that is not covered" is the strongest thing you can
   write on launch day.
3. Keep the note link out of the first paragraph. Let the numbers earn the
   click, then send the note to whoever asks why five repositories.
4. Do not ask for upvotes anywhere. It reads as exactly what it is.
5. If a number in a post is ever wrong, correct it in the thread, not by
   editing the post and hoping.
6. Choose the subreddit before the title: read its self-promotion rule
   first. The text assumes a technical audience.

## What this file is not

It is not a post. Nothing has been submitted to Hacker News, Reddit, X or
LinkedIn, and no page in this profile links to it. It exists so the text is
ready when you decide to spend the morning on the replies.

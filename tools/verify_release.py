#!/usr/bin/env python3
"""Re-derive every public claim in this profile, in one command.

Nothing here is a secret and nothing here needs a token: it reads the published
metadata from PyPI and GitHub, and reads the files in this checkout, and then
says whether they still agree with each other.

    python tools/verify_release.py            the full report card
    python tools/verify_release.py --quiet    failures and the total only

What it checks

    1  five distributions on PyPI at the versions the check table names
    2  five repositories public, not archived, carrying a licence
    3  five public releases whose tag is the version in the table
    4  the check table itself: five rows, six cells each
    5  the engineering note carries every number, with its version
    6  the launch kit still matches the table (runs tools/check_launch.py)
    7  this page and the note are linked from the README, and the kit is not
    8  the guard, its tests and its workflow are where the README says they are

Exit 0 means every claim still holds.  1 means one of them does not, and says
which.  Inside GitHub Actions the workflow-conclusion checks are skipped: the
run doing the checking is itself one of the runs.

Standard library only.
"""
import base64
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

OWNER = "hariszafar740-lang"
BENCH = "energy-systems-benchmarks"
ROOT = Path(__file__).resolve().parents[1]
QUIET = "--quiet" in sys.argv

PACKAGES = [
    ("nr-powerflow-solver", "power-systems-newton-raphson-solver",
     "nr-powerflow solve --case ieee14 --format json"),
    ("pv-mppt-solver", "solar-pv-mppt-dynamic-solver",
     "pv-mppt iv -g 1000 -t 25 --json"),
    ("bess-soc-dynamics-solver", "bess-soc-dynamics-solver", "bess-sim pulse --json"),
    ("inverter-grid-control-solver", "inverter-grid-control-solver",
     "gfm-sim triad --json"),
    ("energy-transition-model", "energy-transition-model", "etm-sim --duality-report"),
]

WORKFLOWS = [
    (BENCH, "Benchmarks", "benchmark, two Python versions"),
    ("ee-portfolio-master", "Master Portfolio Integration Test Sweep", "portfolio matrix"),
    ("hariszafar740-lang", "Profile documentation tests", "profile documentation"),
    ("hariszafar740-lang", "Launch kit guard", "launch kit, weekly"),
]


def api(path, tries=3):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "verify-release/1"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    last = ""
    for attempt in range(tries):
        req = urllib.request.Request("https://api.github.com/" + path.lstrip("/"),
                                     headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.loads(response.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return None
            last = "HTTP %s" % exc.code
        except Exception as exc:
            last = type(exc).__name__
    raise RuntimeError("api.github.com did not answer for %s (%s)" % (path, last))


def text_of(repo, path):
    data = api("repos/%s/%s/contents/%s?ref=main" % (OWNER, repo, path))
    if data is None:
        return None
    return base64.b64decode(str(data.get("content", "")).replace("\n", "")).decode("utf-8")


def pypi(dist):
    with urllib.request.urlopen("https://pypi.org/pypi/%s/json" % dist, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "replace"))["info"]["version"]


def check_table():
    text = text_of(BENCH, "README.md")
    if text is None or "<!-- bench:start -->" not in text:
        raise RuntimeError("the check table is missing from %s" % BENCH)
    block = text.split("<!-- bench:start -->", 1)[-1].split("<!-- bench:end -->", 1)[0]
    rows = {}
    for line in block.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 6:
            raise RuntimeError("a check-table row has %d cells, not 6" % len(cells))
        rows[cells[0].strip("`")] = {"version": cells[1], "command": cells[2].strip("`"),
                                     "measured": cells[3]}
    return rows


def local(rel):
    path = ROOT / rel
    return path.read_text(encoding="utf-8") if path.is_file() else None


def main():
    out = []

    def add(ok, label, detail=""):
        out.append((bool(ok), label, detail))

    try:
        rows = check_table()
    except Exception as exc:
        print("FAIL  %s" % exc)
        return 1

    add(len(rows) == 5, "the check table has five rows", "%d found" % len(rows))
    missing = [d for d, _, _ in PACKAGES if d not in rows]
    add(not missing, "every package the profile names is in the table",
        "missing: %s" % ", ".join(missing) if missing else "")
    if missing:
        for ok, label, detail in out:
            print("%s  %s%s" % ("ok  " if ok else "FAIL", label,
                                (" - " + detail) if detail and not ok else ""))
        return 1

    # 1 - PyPI
    for dist, _, _ in PACKAGES:
        try:
            live = pypi(dist)
        except Exception:
            live = ""
        add(live == rows[dist]["version"], "%s on PyPI is %s" % (dist, rows[dist]["version"]),
            "" if live == rows[dist]["version"] else "PyPI serves %r" % live)

    # 2 - the repositories
    for dist, repo, _ in PACKAGES:
        meta = api("repos/%s/%s" % (OWNER, repo)) or {}
        licence = (meta.get("license") or {}).get("spdx_id")
        ok = bool(meta) and not meta.get("archived") and not meta.get("private") and licence
        add(ok, "%s is public and carries a licence" % repo,
            "" if ok else "archived=%s private=%s licence=%s"
            % (meta.get("archived"), meta.get("private"), licence))

    # 3 - releases
    for dist, repo, _ in PACKAGES:
        rel = api("repos/%s/%s/releases?per_page=1" % (OWNER, repo)) or []
        tag = rel[0].get("tag_name", "") if rel else ""
        draft = rel[0].get("draft") if rel else None
        add(tag.strip("vV") == rows[dist]["version"] and draft is False,
            "%s has a public release %s" % (repo, rows[dist]["version"]),
            "" if tag else "no release")

    # 5 - the engineering note
    note = text_of("hariszafar740-lang", "notes/five-packages.md")
    if note is None:
        add(False, "the engineering note is readable")
    else:
        for dist, _, _ in PACKAGES:
            add(rows[dist]["measured"] in note and "%s %s" % (dist, rows[dist]["version"]) in note,
                "the note carries %s" % dist, "the note has drifted")

    # 6 - the launch kit, through its own guard
    guard = ROOT / "tools" / "check_launch.py"
    if not guard.is_file():
        add(False, "tools/check_launch.py is in this checkout")
    else:
        result = subprocess.run([sys.executable, str(guard), "--quiet"],
                                capture_output=True, text=True, timeout=180)
        said = ""
        for line in ((result.stdout or "") + (result.stderr or "")).splitlines():
            if "checks," in line:
                said = line.strip()
        add(result.returncode == 0, "the launch kit still matches the check table", said)

    # 7 - what the README links
    readme = local("README.md") or ""
    add("notes/five-packages.md" in readme, "the README links the engineering note")
    add("notes/close-out.md" in readme, "the README links this close-out")
    add("launch.md" not in readme,
        "the README does not link the launch kit, which is for pasting from")

    # 8 - the guard is where the README says it is
    for rel in ("tools/check_launch.py", "tests/test_launch_kit.py",
                ".github/workflows/launch-guard.yml"):
        add((ROOT / rel).is_file(), "%s is present" % rel)

    # the kit's own words, read from this checkout
    kit = local("notes/launch.md")
    if kit is None:
        add(False, "notes/launch.md is in this checkout")
    else:
        add("has been posted" in kit and "Nothing here" in kit,
            "the kit still says that nothing has been posted")
        for dist, _, cmd in PACKAGES:
            add(rows[dist]["measured"] in kit and cmd in kit,
                "the kit carries %s, its version and its command" % dist)

    # 9 - the last completed run of each workflow
    if os.environ.get("GITHUB_ACTIONS"):
        add(True, "workflow conclusions are skipped inside CI",
            "the run doing this check is one of them")
    else:
        for repo, name, label in WORKFLOWS:
            runs = (api("repos/%s/%s/actions/runs?per_page=30" % (OWNER, repo)) or {})
            done = [r for r in runs.get("workflow_runs", [])
                    if r.get("name") == name and r.get("status") == "completed"]
            conclusion = done[0].get("conclusion") if done else None
            add(conclusion == "success", "the last completed %s run: %s"
                % (label, conclusion or "none"),
                done[0]["head_sha"][:8] if done else "no completed run")

    if not QUIET:
        for ok, label, detail in out:
            line = "%-4s %s" % ("ok" if ok else "FAIL", label)
            if detail:
                line += "  (%s)" % detail
            print(line)
    failed = [(label, detail) for ok, label, detail in out if not ok]
    for label, detail in failed:
        if QUIET:
            print("FAIL  %s%s" % (label, ("  (%s)" % detail) if detail else ""))
    print("\n%d checks, %d failed" % (len(out), len(failed)))
    if failed:
        print("One of the claims on this page is no longer true. Fix it before it is quoted.")
        return 1
    print("Every claim on this page holds, against the live packages and repositories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
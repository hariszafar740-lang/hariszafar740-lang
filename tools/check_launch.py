#!/usr/bin/env python3
"""Guard the launch kit against the live check table.

The kit in notes/launch.md is generated from the check table in the benchmark
repository. This script re-reads that table now and fails if the kit has drifted:
a number that no longer matches, a command that changed, a post over its
platform's limit, a length the file claims that is not the real length, the
"nothing here has been posted" line going missing, or the profile README
starting to link a file that is meant only for pasting from.

    python tools/check_launch.py            check against the live table
    python tools/check_launch.py --quiet    only print failures and the total

Exit 0 means the kit is current. 1 means it is not, and says on which line.
Standard library only, no token needed (GITHUB_TOKEN is used if it exists).
"""
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

OWNER = "hariszafar740-lang"
BENCH = "energy-systems-benchmarks"
ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "notes" / "launch.md"
README = ROOT / "README.md"
QUIET = "--quiet" in sys.argv

LIMITS = {"hn title": 80, "hn body": 40000, "reddit title": 300, "reddit body": 40000,
          "x": 280, "linkedin": 3000}

# phrases that would make a positive claim the repositories do not support
FORBIDDEN = ["is certified", "is grid-code compliant", "has been validated",
             "hardware-validated", "is a safety prediction", "guarantees",
             "is compliant with"]


REQUIRED = ["no hardware validation", "no certification"]


def api(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "launch-guard/1"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request("https://api.github.com/" + path.lstrip("/"), headers=headers)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def table():
    """The check table, as {dist: {version, command, measured}}."""
    data = api("repos/%s/%s/contents/README.md" % (OWNER, BENCH))
    text = base64.b64decode(str(data.get("content", "")).replace("\n", "")).decode("utf-8")
    if "<!-- bench:start -->" not in text:
        raise SystemExit("the check table markers are gone from %s" % BENCH)
    block = text.split("<!-- bench:start -->", 1)[-1].split("<!-- bench:end -->", 1)[0]
    rows = {}
    for line in block.splitlines():
        if not line.startswith("| `"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        rows[cells[0].strip("`")] = {"version": cells[1], "command": cells[2].strip("`"),
                                     "measured": cells[3]}
    return rows


def fenced(text, start, end):
    """The fenced blocks between two headings, in order."""
    part = text.split(start, 1)[1].split(end, 1)[0]
    return re.findall(r"```\n(.*?)\n```", part, re.S)


def claimed(text, pattern):
    """The character count the file claims for a block."""
    m = re.search(pattern, text)
    return int(m.group(1)) if m else None


def checks(kit, readme, rows):
    out = []

    def add(ok, msg):
        out.append((bool(ok), msg))

    for dist, row in rows.items():
        add(row["measured"] in kit, "kit carries the measured value for %s" % dist)
        add("%s %s" % (dist, row["version"]) in kit,
            "kit names %s at the version the table does" % dist)
        add(row["command"] in kit, "kit carries the command for %s" % dist)

    try:
        hn = fenced(kit, "## 1. Hacker News", "## 2. Reddit")
        red = fenced(kit, "## 2. Reddit", "## 3. X")
        xs = fenced(kit, "## 3. X", "## 4. LinkedIn")
        li = fenced(kit, "## 4. LinkedIn", "## Answers bank")
    except IndexError:
        add(False, "one of the four post sections is missing from the kit")
        return out

    add(len(hn) == 2, "the Hacker News section has a title and a body")
    add(len(red) == 2, "the Reddit section has a title and a body")
    add(len(xs) == 4, "there are four X posts")
    add(len(li) == 1, "the LinkedIn section has a body")
    if len(hn) != 2 or len(red) != 2 or len(xs) != 4 or len(li) != 1:
        return out

    real = [("hn title", hn[0]), ("hn body", hn[1]),
            ("reddit title", red[0]), ("reddit body", red[1]),
            ("x", xs[0]), ("x", xs[1]), ("x", xs[2]), ("x", xs[3]),
            ("linkedin", li[0])]
    for i, (kind, body) in enumerate(real, 1):
        add(len(body) <= LIMITS[kind],
            "%s is %d chars, limit %d" % ("block %d" % i, len(body), LIMITS[kind]))

    for label, body, pattern in (
            ("HN title", hn[0], r"Title \((\d+) chars, limit 80\)"),
            ("HN body", hn[1], None),
            ("Reddit title", red[0], r"Title \((\d+) chars, limit 300\)"),
            ("Reddit body", red[1], r"Body \((\d+) chars, limit 40000\)"),
            ("LinkedIn", li[0], r"Body \((\d+) chars, limit 3000\)")):
        if pattern is None:
            continue
        said = claimed(kit, pattern)
        add(said == len(body), "%s: the file says %s chars, the block is %d"
            % (label, said, len(body)))

    for i, post in enumerate(xs, 1):
        said = claimed(kit, r"Post %d \((\d+) chars, limit 280\)" % i)
        add(said == len(post), "X post %d: the file says %s chars, the post is %d"
            % (i, said, len(post)))

    add("Nothing here\nhas been posted" in kit or "Nothing here has been posted" in kit,
        "the kit still says that nothing has been posted")

    add("launch.md" not in readme,
        "the profile README does not link the launch kit")

    add(kit.count("```") % 2 == 0, "the kit's code fences are balanced")

    low = kit.lower()
    for phrase in FORBIDDEN:
        add(phrase not in low, "the kit does not claim %r" % phrase)
    for phrase in REQUIRED:
        add(phrase in low, "the kit still says %r" % phrase)
    return out


def main():
    if not KIT.is_file():
        print("FAIL  notes/launch.md is missing")
        return 1
    kit = KIT.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8") if README.is_file() else ""
    try:
        rows = table()
    except SystemExit as exc:
        print("FAIL  %s" % exc)
        return 1
    except Exception as exc:
        print("FAIL  the check table could not be read (%s)" % type(exc).__name__)
        return 1

    results = checks(kit, readme, rows)
    if not QUIET:
        for ok, msg in results:
            print("%s  %s" % ("ok  " if ok else "FAIL", msg))
    bad = [msg for ok, msg in results if not ok]
    for msg in bad:
        if QUIET:
            print("FAIL  %s" % msg)
    print("\n%d checks, %d failed" % (len(results), len(bad)))
    if bad:
        print("The launch kit has drifted from the check table. Rebuild it with the "
              "launch box rather than editing it by hand.")
        return 1
    print("The kit matches the live table in every number it quotes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
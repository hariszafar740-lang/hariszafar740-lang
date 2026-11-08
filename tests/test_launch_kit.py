"""Offline checks on notes/launch.md, the launch kit.

The network half of the guard - does every number in the kit still match the
live check table - runs in the Launch kit guard workflow, because a test that
needs GitHub is a test that fails when GitHub is slow or rate-limiting. These
are the checks that can be made from the files in this repository alone, so
they also run in the profile documentation tests on every push.
"""
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
KIT_PATH = ROOT_DIR / "notes" / "launch.md"
README_PATH = ROOT_DIR / "README.md"

LIMITS = {"hn title": 80, "reddit title": 300, "reddit body": 40000,
          "x": 280, "linkedin": 3000}

FORBIDDEN = ["is certified", "is grid-code compliant", "has been validated",
             "hardware-validated", "is a safety prediction", "guarantees",
             "is compliant with"]

REQUIRED = ["no hardware validation", "no certification", "has been posted"]


def kit():
    return KIT_PATH.read_text(encoding="utf-8")


def fenced(text, start, end):
    part = text.split(start, 1)[1].split(end, 1)[0]
    return re.findall(r"```\n(.*?)\n```", part, re.S)


def claimed(text, pattern):
    match = re.search(pattern, text)
    return int(match.group(1)) if match else None


def posts():
    text = kit()
    return {
        "hn title": fenced(text, "## 1. Hacker News", "## 2. Reddit")[0],
        "reddit title": fenced(text, "## 2. Reddit", "## 3. X")[0],
        "reddit body": fenced(text, "## 2. Reddit", "## 3. X")[1],
        "x": fenced(text, "## 3. X", "## 4. LinkedIn"),
        "linkedin": fenced(text, "## 4. LinkedIn", "## Answers bank")[0],
    }


def test_the_kit_exists_and_has_every_post():
    assert KIT_PATH.is_file(), "notes/launch.md is missing"
    text = kit()
    for heading in ("## 1. Hacker News", "## 2. Reddit", "## 3. X",
                    "## 4. LinkedIn", "## Answers bank"):
        assert heading in text, heading
    assert len(fenced(text, "## 3. X", "## 4. LinkedIn")) == 4


def test_claimed_lengths_are_the_lengths_a_reader_sees():
    text = kit()
    p = posts()
    pairs = [("HN title", p["hn title"], r"Title \((\d+) chars, limit 80\)"),
             ("Reddit title", p["reddit title"], r"Title \((\d+) chars, limit 300\)"),
             ("Reddit body", p["reddit body"], r"Body \((\d+) chars, limit 40000\)"),
             ("LinkedIn", p["linkedin"], r"Body \((\d+) chars, limit 3000\)")]
    for label, body, pattern in pairs:
        said = claimed(text, pattern)
        assert said == len(body), "%s claims %s chars, the block is %d" % (
            label, said, len(body))
    for i, post in enumerate(p["x"], 1):
        said = claimed(text, r"Post %d \((\d+) chars, limit 280\)" % i)
        assert said == len(post), "X post %d claims %s chars, it is %d" % (
            i, said, len(post))


def test_every_post_is_inside_its_platform_limit():
    p = posts()
    for key in ("hn title", "reddit title", "reddit body", "linkedin"):
        assert len(p[key]) <= LIMITS[key], "%s is over %d" % (key, LIMITS[key])
    for i, post in enumerate(p["x"], 1):
        assert len(post) <= LIMITS["x"], "X post %d is over 280" % i


def test_the_kit_still_says_that_nothing_was_posted():
    text = kit()
    assert "Nothing here" in text and "has been posted" in text
    assert "linkedin" in text.lower() or "LinkedIn" in text


def test_the_profile_readme_does_not_link_the_kit():
    if not README_PATH.is_file():
        return
    assert "launch.md" not in README_PATH.read_text(encoding="utf-8")


def test_the_kit_makes_no_positive_claim_it_cannot_back():
    low = kit().lower()
    for phrase in FORBIDDEN:
        assert phrase not in low, "the kit claims %r" % phrase
    for phrase in REQUIRED:
        assert phrase in low, "the kit stopped saying %r" % phrase


def test_the_kit_is_well_formed_markdown():
    text = kit()
    assert text.count("```") % 2 == 0
    assert text.startswith("# Launch kit")
    assert "\r" not in text
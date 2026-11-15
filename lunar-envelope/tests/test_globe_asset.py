"""Check visualization asset identity, not scientific accuracy."""
from pathlib import Path
import hashlib


def test_nasa_globe_texture_integrity():
    asset = (
        Path(__file__).resolve().parents[1]
        / "frontend/src/assets/lroc_color_2k.jpg"
    )
    assert hashlib.sha256(asset.read_bytes()).hexdigest() == (
        "f7130a1822681fa7512d7dcfd40db8c10b9ba4f06777910348698260ed7a2170"
    )

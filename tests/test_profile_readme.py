from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
README = ROOT_DIR / "README.md"
PROJECTS = {
    "power-systems-newton-raphson-solver": "Power Systems Newton-Raphson Solver",
    "solar-pv-mppt-dynamic-solver": "Solar PV Dynamic MPPT Solver",
    "bess-soc-dynamics-solver": "BESS SoC Dynamics Solver",
    "inverter-grid-control-solver": "Grid-Forming Inverter Control Solver",
    "energy-transition-model": "Energy Transition Model",
    "ee-portfolio-master": "Central Portfolio Repository",
}


def test_profile_links_all_audited_project_repositories():
    readme = README.read_text(encoding="utf-8")
    for slug, label in PROJECTS.items():
        assert f"https://github.com/hariszafar740-lang/{slug}" in readme
        assert label in readme


def test_profile_does_not_overstate_sparse_jacobian_or_frt_compliance():
    readme = README.read_text(encoding="utf-8").lower()
    assert "sparse jacobian" not in readme
    assert "frt compliance benchmarks" not in readme
    assert "thermal runaway risk" not in readme
    assert "not a safety prediction" in readme
    assert "not certification" in readme
    assert "not evidence of hardware behavior, standards compliance" in readme


def test_profile_documents_independent_models_and_local_test_command():
    readme = README.read_text(encoding="utf-8").lower()
    assert "independent models" in readme
    assert "do not represent one coupled physical system" in readme
    assert "python -m pytest -q tests/" in readme
    assert readme.count("```") % 2 == 0

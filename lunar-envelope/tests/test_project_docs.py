"""Keep recruiter instructions and scientific caveats tied to the project."""
import json
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
REPO = PROJECT.parent

def test_project_explains_challenge_and_access():
    text=(PROJECT/'README.md').read_text(encoding='utf-8')
    assert 'NASA Space Apps Challenge' in text
    assert 'not an official NASA product' in text
    assert 'no public hosted demo yet' in text
    for term in ('GitHub Codespaces','Windows PowerShell','macOS','Linux','Docker'):
        assert term in text
    assert (PROJECT/'docs/workspace.png').is_file()
    assert 'Phase 2 is **not complete**' in text

def test_devcontainer_config_and_lock():
    config=json.loads((REPO/'.devcontainer/lunaris/devcontainer.json').read_text())
    assert 8000 in config['forwardPorts']
    assert config['postCreateCommand'].endswith('lunar-envelope/scripts/setup.sh')
    assert (PROJECT/'backend/requirements.lock').is_file()
    assert (PROJECT/'scripts/setup.sh').is_file()

def test_audit_preserves_scientific_boundaries():
    audit=(PROJECT/'AUDIT.md').read_text(encoding='utf-8')
    assert 'not an independent' in audit
    assert 'not safe EVA windows' in audit
    assert 'LADEE LDEX' in audit
    assert 'No one can honestly guarantee a top-0.1%' in audit


def test_project_identity_and_review_access_are_branch_neutral():
    readme=(PROJECT/'README.md').read_text(encoding='utf-8')
    planner=(PROJECT/'frontend/src/Planner.tsx').read_text(encoding='utf-8')
    workflow=(REPO/'.github/workflows/lunaris-ci.yml').read_text(encoding='utf-8')
    assert 'personal project by **Haris Zafar**' in readme
    assert 'git fetch origin refs/pull/3/head' in readme
    assert 'git checkout --detach FETCH_HEAD' in readme
    assert '/api/provenance/ephemeris' in planner
    assert 'HARIS ZAFAR' in planner
    # The push workflow remains enabled for all branches via its paths filter.
    assert 'branches:' not in workflow.split('  pull_request:',1)[0]

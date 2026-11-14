set -Eeuo pipefail
trap 'echo "A required check failed; neither step is certified complete." >&2' ERR
printf '%s\n' 'No command can guarantee 100% coverage or replace an independent human expert review.'
base="${LUNARIS_WORKDIR_BASE:-$HOME}"
mkdir -p "$base"
work="$(mktemp -d "$base/lunaris-check.XXXXXX")"
mkdir -p "$work/tmp" "$work/npm-cache"
export TMPDIR="$work/tmp" npm_config_cache="$work/npm-cache" PIP_NO_CACHE_DIR=1
git clone --quiet https://github.com/hariszafar740-lang/hariszafar740-lang.git "$work/repo"
git -C "$work/repo" checkout --quiet ba63112cf9ac908aa641bc60c8a3006221442554
cd "$work/repo/lunar-envelope"
bash scripts/setup.sh
.venv/bin/python -m pip install --no-cache-dir pytest httpx
.venv/bin/python -m pytest -q
if .venv/bin/python scripts/fetch_naif_sources.py "$work/naif" >"$work/naif.log" 2>&1; then
  cat "$work/naif.log"
else
  printf 'NAIF source download or hash verification did not pass. See %s/naif.log\n' "$work"
fi
native="${LUNARIS_NATIVE_DEM_DIR:-$HOME/lunaris-terrain.QSYK2V/lola}"
if [ -f "$native/ldem_80s_80m.img" ] && [ -f "$native/ldem_75s_120m.img" ]; then
  export LUNARIS_NATIVE_DEM_DIR="$native"
  .venv/bin/python -m pip install --no-cache-dir 'numpy==2.3.5'
  .venv/bin/python scripts/validate_terrain_sources.py "$native"
  .venv/bin/python scripts/check_native_horizon_regression.py
  printf 'Run with verified native terrain: LUNARIS_NATIVE_DEM_DIR="%s" bash "%s/run.sh"\n' "$native" "$PWD"
else
  printf 'Native LOLA files not found at %s; native source checks were not run.\n' "$native"
  printf 'Download instructions: %s/data/terrain/README.md\n' "$PWD"
fi
printf '\nStep 1: INCOMPLETE — independent expert review and acceptance are outstanding.\n'
printf 'Step 2: INCOMPLETE — independent expert review and acceptance are outstanding.\n'
printf 'Public review request: https://github.com/hariszafar740-lang/hariszafar740-lang/issues/4\n'
printf 'Please identify a qualified independent reviewer; tests and selected comparisons are not global guarantees.\n'
printf 'Evidence: %s/data/ephemeris/README.md and %s/data/terrain/README.md\n' "$PWD" "$PWD"

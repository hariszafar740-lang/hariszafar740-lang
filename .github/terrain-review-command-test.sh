set -Eeuo pipefail
trap 'echo "A required setup or test failed. Phase 2 remains INCOMPLETE." >&2' ERR
base="${LUNARIS_WORKDIR_BASE:-$HOME}"
mkdir -p "$base"
work="$(mktemp -d "$base/lunaris-review.XXXXXX")"
mkdir -p "$work/tmp" "$work/npm-cache"
export TMPDIR="$work/tmp" npm_config_cache="$work/npm-cache" PIP_NO_CACHE_DIR=1
git clone --quiet https://github.com/hariszafar740-lang/hariszafar740-lang.git "$work/repo"
git -C "$work/repo" checkout --quiet ac789c11343580a11f3c48a195e16db04b63e8d6
cd "$work/repo/lunar-envelope"
bash scripts/setup.sh
.venv/bin/python -m pip install --no-cache-dir pytest httpx
.venv/bin/python -m pytest -q
native="${LUNARIS_NATIVE_DEM_DIR:-$HOME/lunaris-terrain.QSYK2V/lola}"
if [ -f "$native/ldem_80s_80m.img" ] && [ -f "$native/ldem_75s_120m.img" ]; then
  export LUNARIS_NATIVE_DEM_DIR="$native"
  .venv/bin/python -m pip install --no-cache-dir 'numpy==2.3.5'
  .venv/bin/python scripts/validate_terrain_sources.py "$native"
  .venv/bin/python scripts/check_native_horizon_regression.py
  printf 'To run with your verified native rasters: LUNARIS_NATIVE_DEM_DIR="%s" bash "%s/run.sh"\n' "$native" "$PWD"
else
  printf 'Native rasters not found at %s; see %s/data/terrain/README.md.\n' "$native" "$PWD"
fi
printf '\nIs Phase 2 complete? NO. A public review request is open, but no independent expert has accepted or reviewed it.\n'
printf 'Review request: https://github.com/hariszafar740-lang/hariszafar740-lang/issues/4\n'
printf 'Please identify a qualified independent reviewer; findings, fixes and written follow-up acceptance remain necessary.\n'
printf 'Review packet: %s/INDEPENDENT_TERRAIN_REVIEW.md\n' "$PWD"
printf 'No independent 10/10 or competition win is claimed.\n'

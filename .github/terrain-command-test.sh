set -Eeuo pipefail
trap 'echo "Setup or a required check failed; Phase 2 remains INCOMPLETE." >&2' ERR
base="${LUNARIS_WORKDIR_BASE:-$HOME}"
mkdir -p "$base"
work="$(mktemp -d "$base/lunaris-terrain.XXXXXX")"
mkdir -p "$work/tmp" "$work/npm-cache"
export TMPDIR="$work/tmp" npm_config_cache="$work/npm-cache" PIP_NO_CACHE_DIR=1
unset LUNARIS_NATIVE_DEM_DIR
git clone --quiet https://github.com/hariszafar740-lang/hariszafar740-lang.git "$work/repo"
git -C "$work/repo" checkout --quiet c892ffda15cf538444970098224bb191e29b2c2a
cd "$work/repo/lunar-envelope"
bash scripts/setup.sh
.venv/bin/python -m pip install --no-cache-dir pytest httpx
.venv/bin/python -m pytest -q
printf '\nAttempting optional NASA LOLA originals (~232 MB)...\n'
if .venv/bin/python scripts/fetch_native_lola.py "$work/lola" >"$work/native-download.log" 2>&1; then
  export LUNARIS_NATIVE_DEM_DIR="$work/lola"
  .venv/bin/python -m pip install --no-cache-dir 'numpy==2.3.5'
  .venv/bin/python scripts/validate_terrain_sources.py "$LUNARIS_NATIVE_DEM_DIR"
  .venv/bin/python scripts/check_native_horizon_regression.py
  printf 'Native rasters verified. To run the app with them: LUNARIS_NATIVE_DEM_DIR="%s" bash "%s/run.sh"\n' "$LUNARIS_NATIVE_DEM_DIR" "$PWD"
else
  printf 'Native rasters not installed; bundled coarse mode remains available. Details: %s/native-download.log\n' "$work"
fi
printf '\nIs Phase 2 complete? NO. Independent expert review, findings and follow-up acceptance are outstanding.\n'
printf 'No independent 10/10 or competition win is claimed; Step 1 also remains independently unaudited.\n'
printf 'NASA source comparisons and selected native-ray checks are documented; results are not global error bounds.\n'
printf 'Please identify an independent planetary-topography/LOLA expert and a contact method.\n'
printf 'Review request: %s/INDEPENDENT_TERRAIN_REVIEW.md\n' "$PWD"
printf 'Evidence and limitations: %s/data/terrain/README.md\n' "$PWD"

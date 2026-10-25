#!/usr/bin/env bash
# Renders everything, several Blender processes at once: one process can't keep the GPU busy, as much of a frame is
# single-threaded posing, fur deforming and image saving. Each job needs up to 6 GB of memory and 3 GB of video
# memory.
#   ./render_all.sh [parallel jobs, default 7] [job ...]
# A job is a line from the list below, e.g. "render.py -- attack worm"; with none given it renders all of them.
set -euo pipefail
cd "$(dirname "$0")"
BLENDER=${BLENDER:-"/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"}
PARALLEL=${1:-7}
shift || true

# longest first, so the short ones fill in at the end
JOBS=(
	"render.py -- run spitter" "render.py -- attack spitter" "render.py -- die spitter"
	"render.py -- run biter" "render.py -- attack biter" "render.py -- die biter"
	"render.py -- attack worm" "nest.py -- biter" "nest.py -- spitter"
	"render.py -- die worm" "render.py -- preparing worm" "render.py -- prepared-alternative worm"
	"render.py -- prepared worm" "render.py -- folded worm"
	"hairball.py" "extras.py -- tufts" "extras.py -- icons"
)
if [ $# -gt 0 ]; then
	JOBS=("$@")
fi

run() {
	local job=$1
	local log
	log=$(mktemp)
	# shellcheck disable=SC2086
	if "$BLENDER" -b --factory-startup -P $job > "$log" 2>&1 && ! grep -q "Traceback" "$log"; then
		echo "done: $job ($(grep -c "stale render" "$log" || true) stale passes redone)"
	else
		echo "FAILED: $job"
		grep -A20 "Traceback" "$log" || tail -20 "$log"
	fi
	rm -f "$log"
}
export -f run
export BLENDER
printf '%s\n' "${JOBS[@]}" | xargs -P "$PARALLEL" -I{} bash -c 'run "$1"' _ {}
echo "all done"

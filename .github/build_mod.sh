#!/usr/bin/env bash
# Zips the tracked files to dist/<name>_<version>.zip under a <name>_<version>/ root, as Factorio loads it. Repository
# files and files the mod doesn't load stay out. Needs jq and zip.
set -euo pipefail
cd "$(dirname "$0")/.."
name=$(jq -r .name info.json)
version=$(jq -r .version info.json)
root="${name}_$version"
rm -rf dist
mkdir -p "dist/$root"
git ls-files -z -- . ':!:.github' ':!:.gitattributes' ':!:.gitignore' ':!:.luacheckrc' ':!:*screenshot*' ':!:blender' \
	| xargs -0 cp --parents -t "dist/$root"
(cd dist && zip -q -X -D -r "$root.zip" "$root")
rm -rf "dist/$root"
echo "dist/$root.zip"

# Renders a cat animation in Factorio's 16 directions and packs its layers into graphics/cat/<family>/:
#   <animation>.png                   the cat with white fur, eyes and nose: drawn as is
#   <animation>-shadow.png
#   <animation>-coat-<pattern>.png    where the coat colour goes, for each pattern set
#   <animation>-marks-<pattern>.png   where the stripe or patch colour goes
# The masks are alpha only; Factorio multiplies the cat by their tint where they cover it ("multiplicative-with-alpha"),
# so they don't overlap.
#   blender -b --factory-startup -P render.py -- <animation> [family]
import math
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
import anim  # noqa: E402
import cat as cat_module  # noqa: E402
import rig  # noqa: E402
import scene  # noqa: E402
import sheet  # noqa: E402

DIRECTIONS = 16
WIDTH, HEIGHT = 512, 448

args = sys.argv[sys.argv.index("--") + 1:]
animation = args[0]
family = args[1] if len(args) > 1 else "biter"
spec = anim.ANIMATIONS[animation]

scene.reset()
sc, ground = scene.setup(WIDTH, HEIGHT, samples=64)
cat = cat_module.build()
scene.catchlight(cat.eyes)
armature = rig.build(cat.body, [cat.nose, *cat.eyes])
root = bpy.data.objects.new("Root", None)
sc.collection.objects.link(root)
armature.parent = root

patterns = list(cat_module.PATTERNS)
tmp = os.path.join(bpy.app.tempdir, "frame.png")
layers = {}
for direction in range(DIRECTIONS):
	root.rotation_euler = (0, 0, -2 * math.pi * direction / DIRECTIONS)
	for frame in range(spec["frames"]):
		spec["pose"](armature, frame / spec["frames"], cat, direction)
		rendered = scene.render_layers(sc, ground, cat, patterns, tmp)
		colour = rendered["colour"]
		layers.setdefault("", []).append(colour)
		layers.setdefault("-shadow", []).append(rendered["shadow"])
		for pattern in patterns:
			coat, marks = rendered[pattern][..., 0], rendered[pattern][..., 1]
			layers.setdefault(f"-coat-{pattern}", []).append(colour[..., 3] * np.clip(coat - marks, 0, 1))
			layers.setdefault(f"-marks-{pattern}", []).append(colour[..., 3] * marks)

out_dir = os.path.join(HERE, "..", "graphics", "cat", family)
for suffix, frames in layers.items():
	kind = "colour" if not suffix else "shadow" if suffix == "-shadow" else "mask"
	sheet.pack(frames, out_dir, animation + suffix, kind)
print("packed", animation, "to", out_dir)

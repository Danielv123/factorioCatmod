# Renders a cat animation in Factorio's 16 directions and packs its layers into graphics/cat/<family>/:
#   <animation>.png                   the cat with white fur, eyes and nose: drawn as is
#   <animation>-shadow.png
#   <animation>-coat-<white>.png      where the coat colour goes, markings included, for each amount of white
#   <animation>-marks-<pattern>.png   where the stripes or patches go, for each pattern set
# The masks are alpha only, at half resolution (a mask only says where a colour goes, and the fur blurs its edges);
# Factorio multiplies the cat by their tint where they cover it ("multiplicative-with-alpha"). The coat mask is shared
# by every pattern with the same white, so markings are multiplied on top of the coat colour (data.lua tints them by
# markings / coat).
# Spitters and worms also get mouth.lua: where in each direction the hairball leaves the mouth, for the stream's start.
#   blender -b --factory-startup -P render.py -- <animation> [biter|spitter|worm]
# The animations are a family's keys in anim.FAMILIES: run, attack and die, or for the worms folded, preparing,
# prepared, prepared-alternative, attack and die.
import math
import os
import sys

import bpy
import numpy as np
from mathutils import Vector

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
import anim  # noqa: E402
import box as box_module  # noqa: E402
import cat as cat_module  # noqa: E402
import rig  # noqa: E402
import scene  # noqa: E402
import sheet  # noqa: E402

DIRECTIONS = 16
WIDTH, HEIGHT = 512, 448

args = sys.argv[sys.argv.index("--") + 1:]
animation = args[0]
family = args[1] if len(args) > 1 else "biter"
spec = anim.ANIMATIONS[anim.FAMILIES[family][animation]]

scene.reset()
sc, ground = scene.setup(WIDTH, HEIGHT, samples=64)
cat = cat_module.build(anim.FAMILIES[family]["style"])
scene.catchlight(cat.eyes)
if anim.FAMILIES[family].get("box"):
	cat.box = box_module.Box()
	cat.add_props(cat.box.parts)
armature = rig.build(cat.body, [cat.nose, *cat.eyes])
root = bpy.data.objects.new("Root", None)
sc.collection.objects.link(root)
armature.parent = root

patterns = list(anim.FAMILIES[family]["patterns"])
tmp = os.path.join(bpy.app.tempdir, "frame.png")
layers = {}
seen = set()


def half(mask):
	"""A mask at half resolution, each pixel the average of four."""
	h, w = mask.shape
	return mask[:h - h % 2, :w - w % 2].reshape(h // 2, 2, w // 2, 2).mean(axis=(1, 3))

mouths = []


def mouth():
	"""The mouth's place on the sheet, in tiles from the entity's position at scale 1: just under the nose."""
	from bpy_extras.object_utils import world_to_camera_view
	bpy.context.view_layer.update()
	nose = cat.nose.matrix_world
	point = nose.translation + nose.to_3x3() @ Vector((0, 0.01, -0.06))
	view = world_to_camera_view(sc, sc.camera, point)
	pixels = ((view.x - 0.5) * WIDTH, (0.5 - view.y) * HEIGHT)
	return tuple(px / scene.PX_PER_TILE for px in pixels)

# an animation with one direction faces the camera
directions = range(DIRECTIONS) if spec.get("directions", DIRECTIONS) == DIRECTIONS else [8]
for direction in directions:
	root.rotation_euler = (0, 0, -2 * math.pi * direction / DIRECTIONS)
	for frame in range(spec["frames"]):
		spec["pose"](armature, anim.phase(spec, frame), cat, direction)
		rendered = scene.render_layers(sc, ground, cat, patterns, tmp)
		colour = rendered["colour"]
		layers.setdefault("", []).append(colour)
		layers.setdefault("-shadow", []).append(rendered["shadow"])
		for pattern in patterns:
			coat, marks = rendered[pattern][..., 0], rendered[pattern][..., 1]
			white = cat_module.PATTERNS[pattern]["white"]
			if f"-coat-{white}" not in seen:
				layers.setdefault(f"-coat-{white}", []).append(half(colour[..., 3] * coat))
				seen.add(f"-coat-{white}")
			layers.setdefault(f"-marks-{pattern}", []).append(half(colour[..., 3] * marks))
		seen.clear()

		if family in ("spitter", "worm") and animation == "attack" and frame == spec["frames"] - 1:
			mouths.append(mouth())

out_dir = os.path.join(HERE, "..", "graphics", "cat", family)
for suffix, frames in layers.items():
	kind = "colour" if not suffix else "shadow" if suffix == "-shadow" else "mask"
	sheet.pack(frames, out_dir, animation + suffix, kind, downscale=2 if kind == "mask" else 1)
if mouths:
	lines = ["-- where the hairball leaves the mouth in each of the 16 directions, in tiles at scale 1", "return", "{"]
	lines += [f"  {{{x:.4f}, {y:.4f}}}," for x, y in mouths]
	lines += ["}", ""]
	with open(os.path.join(out_dir, "mouth.lua"), "w", newline="") as f:
		f.write(chr(10).join(lines))
print("packed", animation, "to", out_dir)

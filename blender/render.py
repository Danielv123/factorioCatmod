# Renders a cat animation in Factorio's 16 directions and packs it, with its shadow, into graphics/.
#   blender -b --factory-startup -P render.py -- <coat> <animation> [density]
# Animations are poses over frames; "stand" is a single frame, for checking the look and calibration in game.
import math
import os
import sys

import bpy

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
import cat  # noqa: E402
import scene  # noqa: E402
import sheet  # noqa: E402

ANIMATIONS = {
	"stand": {"frames": 1},
}
DIRECTIONS = 16
WIDTH, HEIGHT = 512, 448

args = sys.argv[sys.argv.index("--") + 1:]
coat, animation = args[0], args[1]
density = float(args[2]) if len(args) > 2 else 60000
spec = ANIMATIONS[animation]

scene.reset()
sc, ground = scene.setup(WIDTH, HEIGHT, samples=64)
body, parts, fur, eyes = cat.build(coat, density)
scene.catchlight(eyes)
root = bpy.data.objects.new("Root", None)
sc.collection.objects.link(root)
for part in parts:
	part.parent = root

out_dir = os.path.join(HERE, "..", "graphics", "cat", coat)
tmp = os.path.join(bpy.app.tempdir, "frame.png")
colour, shadow = [], []
for direction in range(DIRECTIONS):
	root.rotation_euler = (0, 0, -2 * math.pi * direction / DIRECTIONS)
	for frame in range(spec["frames"]):
		sc.frame_set(frame + 1)
		for is_shadow, frames in ((False, colour), (True, shadow)):
			scene.set_pass(ground, parts + [fur], is_shadow)
			sc.render.filepath = tmp
			bpy.ops.render.render(write_still=True)
			frames.append(sheet.load(tmp))
sheet.pack(colour, out_dir, animation)
sheet.pack(shadow, out_dir, animation + "-shadow", shadow=True)
print("packed", animation, "to", out_dir)

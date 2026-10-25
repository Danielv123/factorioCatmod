# Renders frames of an animation from straight side on (white fur, no tint) as one contact sheet, for checking motion
# without the game's camera angle in the way.
#   blender -b --factory-startup -P sideview.py -- <out.png> <animation> [style] [frames per row]
import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import anim  # noqa: E402
import box as box_module  # noqa: E402
import cat as cat_module  # noqa: E402
import rig  # noqa: E402
import scene  # noqa: E402
import sheet  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
out, animation = args[0], args[1]
style = args[2] if len(args) > 2 else "shorthair"
columns = int(args[3]) if len(args) > 3 else 8

scene.reset()
sc, ground = scene.setup(560, 400, samples=24)
cat = cat_module.build(style, density=25000)
scene.catchlight(cat.eyes)
if animation.startswith("box_"):
	cat.box = box_module.Box()
	cat.add_props(cat.box.parts)
armature = rig.build(cat.body, [cat.nose, *cat.eyes])
root = bpy.data.objects.new("Root", None)
sc.collection.objects.link(root)
armature.parent = root
root.rotation_euler = (0, 0, math.radians(-90))
camera = sc.camera
camera.rotation_euler = (math.radians(90), 0, 0)
camera.location = (-0.2, -20, 0.75)
camera.data.ortho_scale = 3.8
scene.set_pass(ground, cat.subjects, False)

spec = anim.ANIMATIONS[animation]
tiles = []
for frame in range(spec["frames"]):
	spec["pose"](armature, anim.phase(spec, frame), cat, 4)
	scene.set_pass(ground, cat.subjects, False)
	sc.render.filepath = os.path.join(bpy.app.tempdir, "side.png")
	bpy.ops.render.render(write_still=True)
	tiles.append(sheet.load(sc.render.filepath))
h, w = tiles[0].shape[:2]
rows = math.ceil(len(tiles) / columns)
image = np.zeros((rows * h, columns * w, 4), np.float32)
image[..., :3] = 0.82
image[..., 3] = 1
for k, tile in enumerate(tiles):
	r, c = divmod(k, columns)
	a = tile[..., 3:4]
	cell = image[r * h:(r + 1) * h, c * w:(c + 1) * w, :3]
	image[r * h:(r + 1) * h, c * w:(c + 1) * w, :3] = cell * (1 - a) + tile[..., :3] * a
sheet.save(out, image)
print("wrote", out)

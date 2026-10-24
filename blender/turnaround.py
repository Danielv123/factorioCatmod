# Renders the cat standing, in a few directions, to one contact sheet for judging the look.
#   blender -b --factory-startup -P turnaround.py -- <out.png> [coat] [directions] [density]
import math
import os
import sys

import bpy
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import cat  # noqa: E402
import scene  # noqa: E402

args = sys.argv[sys.argv.index("--") + 1:]
out = args[0]
coat = args[1] if len(args) > 1 else "orange-tabby"
directions = int(args[2]) if len(args) > 2 else 8
density = float(args[3]) if len(args) > 3 else 60000

WIDTH, HEIGHT = 320, 288
scene.reset()
sc, ground = scene.setup(WIDTH, HEIGHT, samples=96)
body, parts, fur, eyes = cat.build(coat, density)
scene.catchlight(eyes)
root = bpy.data.objects.new("Root", None)
sc.collection.objects.link(root)
for part in parts:
	part.parent = root
# the camera looks at the cat's middle rather than its feet, for the contact sheet only
sc.camera.location.z += 0.5
sc.camera.location.y += 0.5

frames = []
tmp = os.path.join(os.path.dirname(out), "_turn.png")
for d in range(directions):
	root.rotation_euler = (0, 0, -2 * math.pi * d / directions)
	row = []
	for shadow in (False, True):
		scene.set_pass(ground, parts + [fur], shadow)
		sc.render.filepath = tmp
		bpy.ops.render.render(write_still=True)
		image = bpy.data.images.load(tmp)
		pixels = np.array(image.pixels[:], dtype=np.float32).reshape(HEIGHT, WIDTH, 4)[::-1]
		bpy.data.images.remove(image)
		row.append(pixels)
	colour, shade = row
	# the shadow under the cat on a ground colour, as Factorio composes it
	ground_rgb = np.array([0.36, 0.3, 0.22], dtype=np.float32)
	composed = ground_rgb * (1 - shade[..., 3:4] * 0.6)
	composed = composed * (1 - colour[..., 3:4]) + colour[..., :3] * colour[..., 3:4]
	frames.append(composed)

columns = 4
rows = math.ceil(directions / columns)
sheet = np.ones((rows * HEIGHT, columns * WIDTH, 4), dtype=np.float32)
for i, frame in enumerate(frames):
	r, c = divmod(i, columns)
	sheet[r * HEIGHT:(r + 1) * HEIGHT, c * WIDTH:(c + 1) * WIDTH, :3] = frame
image = bpy.data.images.new("sheet", columns * WIDTH, rows * HEIGHT, alpha=True)
image.pixels = sheet[::-1].ravel()
image.filepath_raw = out
image.file_format = "PNG"
image.save()
os.remove(tmp)
print("wrote", out)

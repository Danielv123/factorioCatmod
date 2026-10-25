# Renders an animation from one direction composed as Factorio would draw it with a sample coat, over a ground colour,
# as numbered frames for a contact sheet or GIF.
#   blender -b --factory-startup -P preview.py -- <out_dir> <animation> [direction 0-15] [coat] [zoom] [style]
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

# sample coats: (pattern set, coat tint, markings tint), as data.lua tints the masks
COATS = {
	"ginger": ("tabby", (1.0, 0.5, 0.14), (0.62, 0.22, 0.05)),
	"grey": ("tabby", (0.62, 0.62, 0.64), (0.22, 0.22, 0.24)),
	"tuxedo": ("tabby-white", (0.1, 0.1, 0.11), (0.1, 0.1, 0.11)),
	"calico": ("patches-white", (1.0, 0.55, 0.18), (0.12, 0.1, 0.1)),
	"cream": ("tabby", (1.0, 0.86, 0.66), (0.88, 0.64, 0.4)),
	"seal-point": ("points", (0.96, 0.9, 0.78), (0.24, 0.16, 0.11)),
	"blue": ("tabby", (0.5, 0.54, 0.62), (0.44, 0.48, 0.56)),
}



def grubby(colour):
	"""As data.lua dulls a coat's colours: a quarter of the way to grey, and a little darker."""
	grey = sum(colour) / 3
	return tuple((c * 0.75 + grey * 0.25) * 0.9 for c in colour)


args = sys.argv[sys.argv.index("--") + 1:]
out_dir, animation = args[0], args[1]
direction = int(args[2]) if len(args) > 2 else 4
coat = args[3] if len(args) > 3 else "ginger"
zoom = float(args[4]) if len(args) > 4 else 1.0
style = args[5] if len(args) > 5 else "shorthair"
pattern, coat_tint, marks_tint = COATS[coat]

WIDTH, HEIGHT = int(448 * zoom), int(384 * zoom)
scene.reset()
sc, ground = scene.setup(WIDTH, HEIGHT, samples=64)
sc.camera.data.ortho_scale /= zoom
cat = cat_module.build(style)
scene.catchlight(cat.eyes)
if animation.startswith("box_"):
	cat.box = box_module.Box()
	cat.add_props(cat.box.parts)
armature = rig.build(cat.body, [cat.nose, *cat.eyes])
root = bpy.data.objects.new("Root", None)
sc.collection.objects.link(root)
armature.parent = root
root.rotation_euler = (0, 0, -2 * math.pi * direction / 16)

os.makedirs(out_dir, exist_ok=True)
spec = anim.ANIMATIONS[animation]
tmp = os.path.join(bpy.app.tempdir, "frame.png")
ground_rgb = np.array([0.36, 0.3, 0.22], dtype=np.float32)
for frame in range(spec["frames"]):
	spec["pose"](armature, anim.phase(spec, frame), cat, direction)
	layers = scene.render_layers(sc, ground, cat, [pattern], tmp)
	colour, shade, mask = layers["colour"], layers["shadow"], layers[pattern]
	# the masks multiply the white cat by their tint where they cover it, and don't overlap
	coat_tint, marks_tint = grubby(coat_tint), grubby(marks_tint)
	rgb = colour[..., :3]
	marks = mask[..., 1]
	for value, tint in ((np.clip(mask[..., 0] - marks, 0, 1), coat_tint), (marks, marks_tint)):
		rgb = rgb * (1 - value[..., None] + value[..., None] * np.array(tint, dtype=np.float32))
	composed = ground_rgb * (1 - np.clip((shade[..., 3:4] - 0.08) / 0.92, 0, 1) * 0.6)
	composed = composed * (1 - colour[..., 3:4]) + rgb * colour[..., 3:4]
	sheet.save(os.path.join(out_dir, f"{animation}-{frame:02d}.png"), np.dstack([composed, np.ones_like(shade[..., :1])]))
print("previewed", animation)

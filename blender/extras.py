# The small things: fur tufts for the puff a cat leaves when it's hit or knocked out (white, tinted to the coat in
# game), and the icons, portraits of each family with coat masks so a tier's icon wears its coat.
#   blender -b --factory-startup -P extras.py -- [tufts|icons]
import math
import os
import random
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

args = sys.argv[sys.argv.index("--") + 1:]
what = args[0] if args else "tufts"
OUT = os.path.join(HERE, "..", "graphics", "cat")


def tufts():
	"""Four wisps of fur, each a bunch of strands fanning out from a point and curling."""
	scene.reset()
	sc, ground = scene.setup(96, 96, samples=64)
	ground.hide_render = True
	material = bpy.data.materials.new("Tuft")
	material.use_nodes = True
	t = cat_module._Tree(material.node_tree)
	t.nodes.clear()
	hair = t.node("ShaderNodeBsdfHairPrincipled", {"Color": (0.92, 0.9, 0.87, 1), "Roughness": 0.4,
		"Radial Roughness": 0.7}, parametrization="COLOR")
	t.links.new(t.out(hair, 0), t.node("ShaderNodeOutputMaterial").inputs["Surface"])
	frames = []
	tmp = os.path.join(bpy.app.tempdir, "tuft.png")
	for variation in range(4):
		random.seed(5 + variation)
		curves = bpy.data.hair_curves.new(f"Tuft{variation}")
		count, points = 180, 6
		curves.add_curves([points] * count)
		bend = Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(0.2, 1))).normalized()
		for c in range(count):
			direction = (Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))) * 0.35 + bend).normalized()
			length = random.uniform(0.12, 0.24)
			curl = Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))) * 0.08
			for i in range(points):
				f = i / (points - 1)
				point = curves.curves[c].points[i]
				point.position = direction * length * f + curl * f * f
				point.radius = 0.004 * (1 - 0.8 * f)
		tuft = bpy.data.objects.new(f"Tuft{variation}", curves)
		curves.materials.append(material)
		sc.collection.objects.link(tuft)
		tuft.location = -direction * 0.09
		sc.render.filepath = tmp
		bpy.ops.render.render(write_still=True)
		frames.append(sheet.load(tmp))
		tuft.hide_render = True
	sheet.pack(frames, os.path.join(OUT, "tuft"), "tuft")


def icons():
	"""Portraits: a cat's face for the biters, a fluffy one for the spitters, a cat in a box for the worms, and a bed
	of kittens for the nests, each with coat masks."""
	size = 64
	families = (("biter", "shorthair", "face"), ("spitter", "longhair", "face"), ("worm", "shorthair", "box"))
	for name, style, setup in families:
		scene.reset()
		sc, ground = scene.setup(size, size, samples=128)
		ground.hide_render = True
		cat = cat_module.build(style)
		scene.catchlight(cat.eyes)
		if setup == "box":
			cat.box = box_module.Box()
			cat.add_props(cat.box.parts)
		armature = rig.build(cat.body, [cat.nose, *cat.eyes])
		root = bpy.data.objects.new("Root", None)
		sc.collection.objects.link(root)
		armature.parent = root
		camera = sc.camera
		if setup == "face":
			# head on, a little from above, turned slightly to the left
			anim.rest(armature)
			root.rotation_euler = (0, 0, math.radians(180 + 20))
			camera.rotation_euler = (math.radians(75), 0, 0)
			camera.location = (0, -20 * math.sin(math.radians(75)), 20 * math.cos(math.radians(75)) + 1.0)
			camera.data.ortho_scale = 1.45
		else:
			root.rotation_euler = (0, 0, math.pi)
			anim.box_prepared(armature, 0.5, cat, 8)
			camera.data.ortho_scale = 2.4
			camera.location.z += 0.55
			camera.location.y += 0.55
		layers = scene.render_layers(sc, ground, cat, list(cat_module.PATTERNS),
			os.path.join(bpy.app.tempdir, "icon.png"))
		colour = layers["colour"]
		out_dir = os.path.join(OUT, "icons")
		os.makedirs(out_dir, exist_ok=True)
		sheet.save(os.path.join(out_dir, f"{name}.png"), colour)
		for pattern in cat_module.PATTERNS:
			coat, marks = layers[pattern][..., 0], layers[pattern][..., 1]
			for layer, value in (("coat", np.clip(coat - marks, 0, 1)), ("marks", marks)):
				sheet.save(os.path.join(out_dir, f"{name}-{layer}-{pattern}.png"),
					np.dstack([colour[..., :3], colour[..., 3] * value]))


if what == "tufts":
	tufts()
else:
	icons()
print("made", what)

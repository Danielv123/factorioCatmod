# Renders the nests: a plush cat bed (biters) or a wicker basket with a blanket (spitters) with three kittens curled
# up asleep in it, in four variations of bed colour and kitten arrangement. The idle loop has them breathing and a
# tail tip flicking; the death has them wake with a start and flop over, knocked out. Each kitten's coat is composited
# in here, so the sheets need no tinting: graphics/cat/<family>-nest/idle-v<n> and die-v<n>.
#   blender -b --factory-startup -P nest.py -- [biter|spitter]
import math
import os
import random
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
from anim import _bump, _ease  # noqa: E402

WIDTH, HEIGHT = 512, 448
KITTEN = 0.5
KITTENS = 3
IDLE_FRAMES, DIE_FRAMES = 7, 18

args = sys.argv[sys.argv.index("--") + 1:]
family = args[0] if args else "biter"
style = "shorthair" if family == "biter" else "longhair"

# per variation: the bed's colour, and each kitten's place (x, y), facing (degrees), coat and which way its tail wraps
COATS = {
	"biter": [("tabby", (1.0, 0.5, 0.14), (0.62, 0.22, 0.05)), ("tabby", (0.62, 0.62, 0.64), (0.22, 0.22, 0.24)),
		("tabby-white", (0.1, 0.1, 0.11), (0.1, 0.1, 0.11)), ("patches-white", (1.0, 0.55, 0.18), (0.12, 0.1, 0.1)),
		("tabby", (1.0, 0.82, 0.55), (0.85, 0.55, 0.3)), ("tabby", (0.62, 0.45, 0.28), (0.22, 0.14, 0.08))],
	"spitter": [("tabby", (1.0, 0.86, 0.66), (0.88, 0.64, 0.4)), ("tabby", (0.5, 0.54, 0.62), (0.44, 0.48, 0.56)),
		("points", (0.96, 0.9, 0.78), (0.24, 0.16, 0.11)), ("tabby", (0.6, 0.42, 0.25), (0.2, 0.12, 0.06)),
		("tabby", (0.97, 0.96, 0.94), (0.97, 0.96, 0.94)), ("patches", (0.5, 0.54, 0.62), (0.95, 0.8, 0.62))],
}[family]
BEDS = {
	"biter": [(0.85, 0.45, 0.55), (0.45, 0.72, 0.62), (0.6, 0.5, 0.8), (0.45, 0.62, 0.86)],
	"spitter": [(0.8, 0.25, 0.25), (0.25, 0.45, 0.7), (0.35, 0.6, 0.35), (0.85, 0.65, 0.25)],
}[family]


def arrangement(variation):
	"""Three kittens curled nose to tail in a ring round the bed's middle."""
	random.seed(17 + variation * 31)
	start = random.uniform(0, 360)
	coats = random.sample(range(len(COATS)), KITTENS)
	kittens = []
	for i in range(KITTENS):
		around = math.radians(start + i * 360 / KITTENS + random.uniform(-12, 12))
		radius = 0.5 + random.uniform(-0.05, 0.05)
		# facing along the ring, anticlockwise, with a little turn in or out
		facing = math.degrees(around) + 180 + random.uniform(-15, 15)
		kittens.append((radius * math.cos(around), radius * math.sin(around), facing, coats[i], random.choice((-1, 1)),
			random.random()))
	return kittens


def fabric(name, colour, plaid=False):
	material = bpy.data.materials.new(name)
	material.use_nodes = True
	t = cat_module._Tree(material.node_tree)
	bsdf = t.nodes["Principled BSDF"]
	p = t.out(t.node("ShaderNodeTexCoord"), "Object")
	fuzz = t.node("ShaderNodeTexNoise", {"Vector": p, "Scale": 60.0, "Detail": 3.0})
	shade = t.math("MULTIPLY_ADD", t.out(fuzz, "Fac"), 0.25, 0.85)
	base = t.node("ShaderNodeMix", {"A": (0, 0, 0, 1), "B": (*colour, 1), "Factor": shade}, data_type="RGBA")
	result = t.out(base, "Result")
	if plaid:
		sep = t.node("ShaderNodeSeparateXYZ", {"Vector": p})
		bands = t.math("ADD", t.math("GREATER_THAN", t.math("SINE", t.math("MULTIPLY", t.out(sep, "X"), 14.0)), 0.55),
			t.math("GREATER_THAN", t.math("SINE", t.math("MULTIPLY", t.out(sep, "Y"), 14.0)), 0.55))
		result = t.out(t.node("ShaderNodeMix", {"A": result, "B": (0.95, 0.92, 0.85, 1),
			"Factor": t.math("MULTIPLY", bands, 0.45)}, data_type="RGBA"), "Result")
	t.links.new(result, cat_module._sock(bsdf.inputs, "Base Color"))
	bsdf.inputs["Roughness"].default_value = 0.95
	cat_module._sock(bsdf.inputs, "Sheen Weight").default_value = 0.8
	return material


def wicker():
	material = bpy.data.materials.new("Wicker")
	material.use_nodes = True
	t = cat_module._Tree(material.node_tree)
	bsdf = t.nodes["Principled BSDF"]
	p = t.out(t.node("ShaderNodeTexCoord"), "Object")
	sep = t.node("ShaderNodeSeparateXYZ", {"Vector": p})
	angle = t.math("ARCTAN2", t.out(sep, "Y"), t.out(sep, "X"))
	# a basket weave: strands going round, crossing upright stakes over and under
	rounds = t.math("SINE", t.math("MULTIPLY", t.out(sep, "Z"), 60.0))
	stakes = t.math("SINE", t.math("MULTIPLY", angle, 24.0))
	weave = t.math("MULTIPLY_ADD", t.math("MULTIPLY", rounds, t.math("SIGN", stakes)), 0.5, 0.5)
	colour = t.node("ShaderNodeMix", {"A": (0.32, 0.2, 0.09, 1), "B": (0.72, 0.52, 0.28, 1), "Factor": weave},
		data_type="RGBA")
	t.links.new(t.out(colour, "Result"), cat_module._sock(bsdf.inputs, "Base Color"))
	bsdf.inputs["Roughness"].default_value = 0.7
	bump = t.node("ShaderNodeBump", {"Height": weave, "Strength": 0.6})
	t.links.new(t.out(bump, "Normal"), cat_module._sock(bsdf.inputs, "Normal"))
	return material


def bed():
	"""A round plush bed: a soft bolster around a cushion; or a round wicker basket with a blanket in it."""
	objects = []
	if family == "biter":
		bpy.ops.mesh.primitive_torus_add(major_radius=1.25, minor_radius=0.36, major_segments=64, minor_segments=24)
		rim = bpy.context.object
		rim.scale = (1, 1, 0.75)
		rim.location.z = 0.27
		bpy.ops.object.shade_smooth()
		bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.05, depth=0.14, location=(0, 0, 0.08))
		cushion = bpy.context.object
		cushion.modifiers.new("Round", "BEVEL").width = 0.05
		bpy.ops.object.shade_smooth()
		objects = [rim, cushion]
	else:
		bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.4, depth=0.55, location=(0, 0, 0.275))
		wall = bpy.context.object
		bpy.ops.object.mode_set(mode="EDIT")
		bpy.ops.mesh.select_all(action="DESELECT")
		bpy.ops.object.mode_set(mode="OBJECT")
		for polygon in wall.data.polygons:
			polygon.select = polygon.normal.z > 0.9
		bpy.ops.object.mode_set(mode="EDIT")
		bpy.ops.mesh.delete(type="FACE")
		bpy.ops.object.mode_set(mode="OBJECT")
		wall.modifiers.new("Wall", "SOLIDIFY").thickness = 0.06
		bpy.ops.object.shade_smooth()
		bpy.ops.mesh.primitive_torus_add(major_radius=1.4, minor_radius=0.07, major_segments=64, minor_segments=12,
			location=(0, 0, 0.55))
		rim = bpy.context.object
		bpy.ops.object.shade_smooth()
		bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.3, depth=0.2, location=(0, 0, 0.12))
		blanket = bpy.context.object
		blanket.modifiers.new("Round", "BEVEL").width = 0.08
		bpy.ops.object.shade_smooth()
		objects = [wall, rim, blanket]
	return objects


def colour_bed(objects, variation):
	if family == "biter":
		rim, cushion = objects
		material = fabric("Bed", BEDS[variation])
		for obj in objects:
			obj.data.materials.clear()
			obj.data.materials.append(material)
		cushion.data.materials[0] = fabric("Cushion", tuple(min(1, c * 1.15 + 0.08) for c in BEDS[variation]))
	else:
		wall, rim, blanket = objects
		weave = wicker()
		for obj in (wall, rim):
			obj.data.materials.clear()
			obj.data.materials.append(weave)
		blanket.data.materials.clear()
		blanket.data.materials.append(fabric("Blanket", BEDS[variation], plaid=True))


scene.reset()
sc, ground = scene.setup(WIDTH, HEIGHT, samples=64)
bed_objects = bed()
kittens = []
for i in range(KITTENS):
	cat = cat_module.build(style)
	armature = rig.build(cat.body, [cat.nose, *cat.eyes])
	holder = bpy.data.objects.new(f"Kitten{i}", None)
	sc.collection.objects.link(holder)
	armature.parent = holder
	holder.scale = (KITTEN,) * 3
	kittens.append((cat, armature, holder))
scene.catchlight([eye for cat, _, _ in kittens for eye in cat.eyes])
subjects = [obj for cat, _, _ in kittens for obj in cat.subjects] + bed_objects

tmp = os.path.join(bpy.app.tempdir, "nest.png")


def render(path=tmp):
	sc.render.filepath = path
	bpy.ops.render.render(write_still=True)
	return sheet.load(path)


def frame(layout):
	"""The composed colour (every kitten in its coat) and the shadow of the current pose."""
	for cat, _, _ in kittens:
		cat.look("colour")
	for obj in subjects:
		obj.visible_camera = True
	ground.visible_camera, ground.is_shadow_catcher = False, False
	colour = render()
	scene.set_pass(ground, subjects, True)
	shadow = render()
	scene.set_pass(ground, subjects, False)
	settings = (sc.view_settings.view_transform, sc.cycles.samples, sc.cycles.use_denoising)
	sc.view_settings.view_transform, sc.cycles.samples, sc.cycles.use_denoising = "Raw", 32, False
	bed_black = kittens[0][0]._looks["tabby"][kittens[0][0].nose]
	bed_materials = [obj.data.materials[0] for obj in bed_objects]
	for obj in bed_objects:
		cat_module._swap(obj, bed_black)
	rgb = colour[..., :3].copy()
	for (cat, _, _), kitten in zip(kittens, layout):
		pattern, coat, marks = COATS[kitten[3]]
		for other, _, _ in kittens:
			if other is cat:
				other.look(pattern)
			else:
				other.look_black()
		mask = render()
		marked = mask[..., 1:2]
		coated = np.clip(mask[..., 0:1] - marked, 0, 1)
		rgb = rgb * (1 - coated + coated * np.array(coat)) * (1 - marked + marked * np.array(marks))
	for obj, material in zip(bed_objects, bed_materials):
		cat_module._swap(obj, material)
	sc.view_settings.view_transform, sc.cycles.samples, sc.cycles.use_denoising = settings
	for cat, _, _ in kittens:
		cat.look("colour")
	return np.dstack([rgb, colour[..., 3:4]]), shadow


out_dir = os.path.join(HERE, "..", "graphics", "cat", family + "-nest")
for variation in range(4):
	layout = arrangement(variation)
	colour_bed(bed_objects, variation)
	for (cat, armature, holder), kitten in zip(kittens, layout):
		# resting on the cushion or the blanket
		holder.location = (kitten[0], kitten[1], 0.15 if family == "biter" else 0.22)
		holder.rotation_euler = (0, 0, math.radians(kitten[2]))
	for name, frames in (("idle", IDLE_FRAMES), ("die", DIE_FRAMES)):
		colours, shadows = [], []
		for f in range(frames):
			t = f / (frames - 1)
			for (cat, armature, holder), kitten in zip(kittens, layout):
				wrap, quirk = kitten[4], kitten[5]
				if name == "idle":
					# breathing out of step with each other; the ping-pong playback makes it loop
					breath = 0.5 - 0.5 * math.cos(math.pi * (t + quirk))
					anim.sleep(armature, breath, wrap=wrap, quirk=quirk)
					cat.set_eyes("closed")
				else:
					anim.sleep(armature, 0, wake=_bump(t, 0.05, 0.45), out=_ease(t, 0.35, 0.75), wrap=wrap, quirk=quirk)
					cat.set_eyes("closed" if t < 0.08 else "open" if t < 0.5 else "x")
			colour, shadow = frame(layout)
			colours.append(colour)
			shadows.append(shadow)
		sheet.pack(colours, out_dir, f"{name}-v{variation + 1}")
		sheet.pack(shadows, out_dir, f"{name}-v{variation + 1}-shadow", "shadow")
		print("packed", family, name, variation + 1)

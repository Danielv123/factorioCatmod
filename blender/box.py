# The worms' cardboard box: a floor and four walls hinged at the bottom, four flaps hinged on the walls' tops, in
# warped, stained and scuffed brown card with a strip of tape down each long flap and a paw print stamped on the
# front. It stands at the origin and doesn't turn with the cat. Knocked out, the cat bursts it: the walls fall open.
import math
import random

import bmesh
import bpy
from mathutils import Vector

import cat as cat_module

WIDTH, DEPTH, HEIGHT = 1.5, 1.25, 0.72
CARD = 0.025


def _grime(t, p, colour, height, strength=1.0):
	"""Shader nodes dirtying colour at object position p: water stains with darker rims, smudges, and dirt rising
	from the ground (height is how far up p is, in tiles)."""
	stains = t.node("ShaderNodeTexNoise", {"Vector": p, "Scale": 2.2, "Detail": 3.0, "Roughness": 0.6})
	stain = t.map_range(t.out(stains, "Fac"), 0.56, 0.62)
	rim = t.math("MULTIPLY", t.map_range(t.out(stains, "Fac"), 0.55, 0.57), t.map_range(t.out(stains, "Fac"), 0.6, 0.57))
	smudges = t.node("ShaderNodeTexNoise", {"Vector": p, "Scale": 11.0, "Detail": 5.0, "Roughness": 0.7})
	smudge = t.map_range(t.out(smudges, "Fac"), 0.58, 0.72)
	ground = t.map_range(height, 0.25, 0.0)
	dirt = t.math("MINIMUM", 1.0, t.math("MULTIPLY", strength, t.math("ADD", t.math("ADD",
		t.math("MULTIPLY", stain, 0.25), t.math("MULTIPLY", rim, 0.35)), t.math("ADD", t.math("MULTIPLY", smudge, 0.4),
		t.math("MULTIPLY", ground, 0.55)))))
	mixed = t.node("ShaderNodeMix", {"A": colour, "B": (0.17, 0.13, 0.09, 1), "Factor": dirt}, data_type="RGBA")
	return t.out(mixed, "Result")


def _cardboard(name, tape=False, paw=False, height_offset=0.0):
	material = bpy.data.materials.new(name)
	material.use_nodes = True
	t = cat_module._Tree(material.node_tree)
	bsdf = t.nodes["Principled BSDF"]
	p = t.out(t.node("ShaderNodeTexCoord"), "Object")
	sep = t.node("ShaderNodeSeparateXYZ", {"Vector": p})
	x, z = t.out(sep, "X"), t.out(sep, "Z")
	# fine corrugation and scuffing on dull brown card
	ribs = t.node("ShaderNodeTexWave", {"Vector": p, "Scale": 26.0, "Distortion": 0.4}, wave_type="BANDS",
		bands_direction="Z")
	scuff = t.node("ShaderNodeTexNoise", {"Vector": p, "Scale": 9.0, "Detail": 4.0})
	shade = t.math("ADD", t.math("MULTIPLY", t.out(ribs, "Fac"), 0.06), t.math("MULTIPLY", t.out(scuff, "Fac"), 0.22))
	colour = t.node("ShaderNodeMix", {"A": (0.3, 0.21, 0.12, 1), "B": (0.5, 0.38, 0.24, 1), "Factor": shade},
		data_type="RGBA")
	result = t.out(colour, "Result")
	if tape:
		# a band of tan tape along the flap's middle, peeling and grubby
		band = t.map_range(t.math("ABSOLUTE", x), 0.13, 0.11)
		result = t.out(t.node("ShaderNodeMix", {"A": result, "B": (0.6, 0.5, 0.33, 1), "Factor": band},
			data_type="RGBA"), "Result")
	if paw:
		# a paw print on the front: a big pad and four toes, in faded ink
		def pad(cx, cz, rx, rz):
			dx = t.math("DIVIDE", t.math("SUBTRACT", x, cx), rx)
			dz = t.math("DIVIDE", t.math("SUBTRACT", z, cz), rz)
			return t.math("LESS_THAN", t.math("ADD", t.math("MULTIPLY", dx, dx), t.math("MULTIPLY", dz, dz)), 1.0)
		ink = pad(0.0, HEIGHT * 0.38, 0.17, 0.12)
		for cx, cz in ((-0.2, 0.6), (-0.075, 0.68), (0.075, 0.68), (0.2, 0.6)):
			ink = t.math("MAXIMUM", ink, pad(cx, HEIGHT * cz, 0.06, 0.065))
		worn = t.node("ShaderNodeTexNoise", {"Vector": p, "Scale": 30.0, "Detail": 2.0})
		ink = t.math("MULTIPLY", ink, t.map_range(t.out(worn, "Fac"), 0.35, 0.55))
		result = t.out(t.node("ShaderNodeMix", {"A": result, "B": (0.13, 0.07, 0.05, 1), "Factor": ink},
			data_type="RGBA"), "Result")
	result = _grime(t, p, result, t.math("ADD", z, height_offset))
	t.links.new(result, cat_module._sock(bsdf.inputs, "Base Color"))
	bsdf.inputs["Roughness"].default_value = 0.92
	return material


def _sheet(name, corners, rows=6, columns=8, warp=0.012, seed=0):
	"""A card panel between corners (origin, along, up), subdivided and gently warped, as an object at the origin."""
	origin, along, up = (Vector(c) for c in corners)
	normal = along.cross(up).normalized()
	random.seed(seed)
	phase = [random.uniform(0, 6.3) for _ in range(4)]
	bm = bmesh.new()
	verts = []
	for i in range(rows + 1):
		row = []
		for j in range(columns + 1):
			u, v = j / columns, i / rows
			bulge = (math.sin(math.pi * u) * math.sin(math.pi * v) * 0.6 + 0.25 * math.sin(7 * u + phase[0])
				* math.sin(5 * v + phase[1]) + 0.15 * math.sin(13 * u + phase[2] + 9 * v))
			row.append(bm.verts.new(origin + along * u + up * v + normal * warp * bulge))
		verts.append(row)
	for i in range(rows):
		for j in range(columns):
			bm.faces.new((verts[i][j], verts[i][j + 1], verts[i + 1][j + 1], verts[i + 1][j]))
	mesh = bpy.data.meshes.new(name)
	bm.to_mesh(mesh)
	bm.free()
	for polygon in mesh.polygons:
		polygon.use_smooth = True
	obj = bpy.data.objects.new(name, mesh)
	bpy.context.scene.collection.objects.link(obj)
	obj.modifiers.new("Card", "SOLIDIFY").thickness = CARD
	return obj


class Box:
	"""The box's walls and flaps; open() swings the flaps from closed (0) to wide open (1), burst() knocks the walls
	open."""

	def __init__(self):
		w, d, h = WIDTH / 2, DEPTH / 2, HEIGHT
		self.floor = _sheet("Floor", ((-w, -d, 0.002), (WIDTH, 0, 0), (0, DEPTH, 0)), seed=1, warp=0.004)
		self.floor.data.materials.append(_cardboard("FloorCard"))
		# each wall's origin is its bottom edge, its hinge; front (-Y), back, left (-X), right
		self.walls = []
		for name, hinge, along, outward, seed in (("Front", (0, -d, 0), (WIDTH, 0, 0), Vector((0, -1, 0)), 2),
				("Back", (0, d, 0), (WIDTH, 0, 0), Vector((0, 1, 0)), 3),
				("Left", (-w, 0, 0), (0, DEPTH, 0), Vector((-1, 0, 0)), 4),
				("Right", (w, 0, 0), (0, DEPTH, 0), Vector((1, 0, 0)), 5)):
			along = Vector(along)
			wall = _sheet(name + "Wall", (-along / 2, along, (0, 0, h)), seed=seed)
			wall.location = hinge
			wall.data.materials.append(_cardboard(name + "Card", paw=name == "Front"))
			# a buckle for when it's burst
			bend = wall.modifiers.new("Buckle", "SIMPLE_DEFORM")
			bend.deform_method = "BEND"
			bend.deform_axis = "Z"
			bend.angle = 0
			self.walls.append((wall, outward, name))
		self.flaps = []
		# long flaps on the front and back, short ones at the sides; each hinged on its wall's top edge
		for (wall, outward, name), length, span in zip(self.walls, (DEPTH * 0.46, DEPTH * 0.46, WIDTH * 0.42,
				WIDTH * 0.42), (WIDTH, WIDTH, DEPTH, DEPTH)):
			inward = -outward
			across = Vector((1, 0, 0)) if name in ("Front", "Back") else Vector((0, 1, 0))
			# lying flat it reaches over the opening
			flap = _sheet(name + "Flap", (-across * span / 2, across * span, inward * length), rows=4, columns=8,
				warp=0.008, seed=10 + len(self.flaps))
			flap.parent = wall
			flap.location = (0, 0, h)
			flap.data.materials.append(_cardboard(name + "FlapCard", tape=name in ("Front", "Back"), height_offset=h))
			self.flaps.append((flap, outward, name))
		self.parts = [self.floor] + [w for w, _, _ in self.walls] + [f for f, _, _ in self.flaps]
		self.burst(0.0)

	@staticmethod
	def _tip(obj, outward, angle, twist=0.0):
		"""Rotates obj about its hinge so its free edge swings outward by angle degrees (negative swings it in)."""
		a = math.radians(angle)
		if abs(outward.y) > 0.5:
			obj.rotation_euler = (-outward.y * a, 0, math.radians(twist))
		else:
			obj.rotation_euler = (0, outward.x * a, math.radians(twist))

	def open(self, openness, wiggle=0.0):
		"""0: flaps folded flat over the top, the long ones a gap apart; 1: swung open and leaning out past upright.
		wiggle lifts them a little, for a box with something stirring inside."""
		self._openness, self._wiggle = openness, wiggle
		self._pose()

	def burst(self, amount):
		"""0 whole; 1 burst open: the front fallen flat, the sides buckled and splayed, the back leaning out, the flaps
		torn back."""
		self._burst = amount
		self._pose()

	def _pose(self):
		openness = getattr(self, "_openness", 0.0)
		wiggle = getattr(self, "_wiggle", 0.0)
		b = getattr(self, "_burst", 0.0)
		# per wall: how far it falls, a twist as it tears loose, and how hard it buckles
		falls = {"Front": (88, 6, 0.0), "Back": (24, -4, 0.15), "Left": (62, -8, 0.6), "Right": (44, 10, -0.5)}
		for wall, outward, name in self.walls:
			angle, twist, buckle = falls[name]
			# the front lands flat with a little bounce
			bounce = 6 * math.sin(math.pi * min(1, max(0, (b - 0.7) / 0.3))) if name == "Front" else 0
			self._tip(wall, outward, angle * b - bounce, twist * b)
			wall.modifiers["Buckle"].angle = buckle * b
		for i, (flap, outward, name) in enumerate(self.flaps):
			# the side flaps fold under the long ones when closed; burst, they're torn further back
			closed = 2 if name in ("Front", "Back") else -3
			angle = closed + (125 - closed) * openness + wiggle * (6 + 3 * i) + (35 + 12 * i) * b
			# hinged on the wall's top, a flap lying flat points inward, so it swings the opposite way to the wall
			self._tip(flap, -outward, -angle)

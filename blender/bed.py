# The nests' beds: a plush round bed (biters), a bolster of seven arcs around a cushion in two halves, or a wicker
# basket (spitters) of nine staves with a blanket in it. Fabric and wicker are faded, stained and dusty. burst() breaks
# it: the pieces tip outward and twist loose, dirty stuffing puffs out of the torn bolster and splinters stick out of
# the broken wicker. Textures are mapped in the bed's own space (the "bedpos" attribute), so a falling piece keeps its
# pattern.
import math
import random

import bmesh
import bpy
from mathutils import Vector

import box
import cat as cat_module


def _mesh_object(name, bm, positions):
	"""An object from bm, with each vertex's bed-space position kept as "bedpos"."""
	mesh = bpy.data.meshes.new(name)
	bm.to_mesh(mesh)
	bm.free()
	attribute = mesh.attributes.new("bedpos", "FLOAT_VECTOR", "POINT")
	for i, p in enumerate(positions):
		attribute.data[i].vector = p
	for polygon in mesh.polygons:
		polygon.use_smooth = True
	obj = bpy.data.objects.new(name, mesh)
	bpy.context.scene.collection.objects.link(obj)
	return obj


def _piece(name, mid, outer, build):
	"""An object whose origin is the bed-space point outer (its outer bottom edge, its hinge) turned to face out at
	angle mid; build(add) adds geometry with add(bed-space point) returning a vertex."""
	bm = bmesh.new()
	positions = []
	origin = Vector((outer * math.cos(mid), outer * math.sin(mid), 0))
	turn = Vector((math.cos(mid), math.sin(mid), 0))

	def add(p):
		positions.append(p.copy())
		local = p - origin
		# into the piece's frame: x outward, y along the ring, z up
		v = bm.verts.new((local.x * turn.x + local.y * turn.y, -local.x * turn.y + local.y * turn.x, local.z))
		return v

	build(bm, add)
	obj = _mesh_object(name, bm, positions)
	obj.location = origin
	obj.rotation_euler = (0, 0, mid)
	obj["mid"] = mid
	return obj


def _ring_arc(bm, add, a0, a1, radius, centre_z, minor, squash=1.0, steps=12, around=16):
	"""A tube following a circle of radius from angle a0 to a1, capped at both ends."""
	rings = []
	for i in range(steps + 1):
		a = a0 + (a1 - a0) * i / steps
		out = Vector((math.cos(a), math.sin(a), 0))
		ring = []
		for j in range(around):
			b = 2 * math.pi * j / around
			ring.append(add(out * (radius + minor * math.cos(b)) + Vector((0, 0, centre_z + minor * squash
				* math.sin(b)))))
		rings.append(ring)
	for i in range(steps):
		for j in range(around):
			k = (j + 1) % around
			bm.faces.new((rings[i][j], rings[i][k], rings[i + 1][k], rings[i + 1][j]))
	for ring, a in ((rings[0], a0), (rings[-1], a1)):
		out = Vector((math.cos(a), math.sin(a), 0))
		centre = add(out * radius + Vector((0, 0, centre_z)))
		for j in range(around):
			bm.faces.new((centre, ring[(j + 1) % around], ring[j]) if ring is rings[0] else
				(centre, ring[j], ring[(j + 1) % around]))


def _shell_arc(bm, add, a0, a1, radius, height, thickness, steps=10):
	"""A curved slab of wall from angle a0 to a1, closed all round."""
	quads = []
	for i in range(steps + 1):
		a = a0 + (a1 - a0) * i / steps
		out = Vector((math.cos(a), math.sin(a), 0))
		quads.append([add(out * r + Vector((0, 0, z))) for r, z in ((radius, 0), (radius + thickness, 0),
			(radius + thickness, height), (radius, height))])
	for i in range(steps):
		for j in range(4):
			k = (j + 1) % 4
			bm.faces.new((quads[i][j], quads[i][k], quads[i + 1][k], quads[i + 1][j]))
	bm.faces.new(list(reversed(quads[0])))
	bm.faces.new(quads[-1])


def _half_disc(bm, add, side, radius, z0, z1, steps=24):
	"""Half a flat cylinder, on the +Y side (side 1) or the -Y side (-1)."""
	edge = []
	for i in range(steps + 1):
		a = math.pi * i / steps
		edge.append(Vector((radius * math.cos(a), side * radius * math.sin(a), 0)))
	bottom = [add(p + Vector((0, 0, z0))) for p in edge]
	top = [add(p + Vector((0, 0, z1))) for p in edge]
	for i in range(steps):
		bm.faces.new((bottom[i], bottom[i + 1], top[i + 1], top[i]))
	bm.faces.new(top if side > 0 else list(reversed(top)))
	bm.faces.new(list(reversed(bottom)) if side > 0 else bottom)
	bm.faces.new((bottom[0], top[0], top[-1], bottom[-1]))


def _tufts(name, centre, material, count, length, radius, curl, seed):
	"""A bunch of strands bursting out of a point, as a curves object at centre: stuffing or splinters."""
	random.seed(seed)
	curves = bpy.data.hair_curves.new(name)
	points = 8
	curves.add_curves([points] * count)
	for c in range(count):
		direction = Vector((random.gauss(0, 1), random.gauss(0, 1), abs(random.gauss(0, 1)) + 0.3)).normalized()
		step = length * random.uniform(0.5, 1.0) / (points - 1)
		# each strand wanders, so they mat into wads rather than spiking out (curl 0 keeps them straight)
		position = Vector((0, 0, 0))
		heading = direction.copy()
		for i in range(points):
			point = curves.curves[c].points[i]
			point.position = position
			point.radius = radius * (1 - 0.6 * i / (points - 1))
			heading = (heading + Vector((random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))) * curl * 8
				).normalized()
			position = position + heading * step
	curves.materials.append(material)
	obj = bpy.data.objects.new(name, curves)
	bpy.context.scene.collection.objects.link(obj)
	obj.location = centre
	obj.scale = (0, 0, 0)
	return obj


def _dress(obj, material):
	if obj.data.materials:
		cat_module._swap(obj, material)
	else:
		obj.data.materials.append(material)


def _bedpos(t):
	return t.out(t.node("ShaderNodeAttribute", attribute_name="bedpos", attribute_type="GEOMETRY"), "Vector")


def fabric(name, colour, plaid=False):
	"""Plush fabric, faded and dusty, with stains and grime working up from the floor."""
	material = bpy.data.materials.new(name)
	material.use_nodes = True
	t = cat_module._Tree(material.node_tree)
	bsdf = t.nodes["Principled BSDF"]
	p = _bedpos(t)
	sep = t.node("ShaderNodeSeparateXYZ", {"Vector": p})
	# faded half way to grey, and grubby
	grey = sum(colour) / 3
	faded = tuple((c * 0.5 + grey * 0.5) * 0.7 for c in colour)
	fuzz = t.node("ShaderNodeTexNoise", {"Vector": p, "Scale": 60.0, "Detail": 3.0})
	shade = t.math("MULTIPLY_ADD", t.out(fuzz, "Fac"), 0.3, 0.75)
	base = t.node("ShaderNodeMix", {"A": (0, 0, 0, 1), "B": (*faded, 1), "Factor": shade}, data_type="RGBA")
	result = t.out(base, "Result")
	if plaid:
		bands = t.math("ADD", t.math("GREATER_THAN", t.math("SINE", t.math("MULTIPLY", t.out(sep, "X"), 14.0)), 0.55),
			t.math("GREATER_THAN", t.math("SINE", t.math("MULTIPLY", t.out(sep, "Y"), 14.0)), 0.55))
		result = t.out(t.node("ShaderNodeMix", {"A": result, "B": (0.55, 0.52, 0.46, 1),
			"Factor": t.math("MULTIPLY", bands, 0.4)}, data_type="RGBA"), "Result")
	# a film of pale dust on the tops
	dust = t.node("ShaderNodeTexNoise", {"Vector": p, "Scale": 5.0, "Detail": 3.0})
	dusty = t.math("MULTIPLY", t.map_range(t.out(dust, "Fac"), 0.4, 0.7), 0.35)
	result = t.out(t.node("ShaderNodeMix", {"A": result, "B": (0.42, 0.39, 0.34, 1), "Factor": dusty},
		data_type="RGBA"), "Result")
	result = box._grime(t, p, result, t.out(sep, "Z"), 1.4)
	t.links.new(result, cat_module._sock(bsdf.inputs, "Base Color"))
	bsdf.inputs["Roughness"].default_value = 1.0
	cat_module._sock(bsdf.inputs, "Sheen Weight").default_value = 0.4
	return material


def wicker():
	"""Weathered wicker, greyed and grimy, the weave dark between the strands."""
	material = bpy.data.materials.new("Wicker")
	material.use_nodes = True
	t = cat_module._Tree(material.node_tree)
	bsdf = t.nodes["Principled BSDF"]
	p = _bedpos(t)
	sep = t.node("ShaderNodeSeparateXYZ", {"Vector": p})
	angle = t.math("ARCTAN2", t.out(sep, "Y"), t.out(sep, "X"))
	# a basket weave: strands going round, crossing upright stakes over and under
	rounds = t.math("SINE", t.math("MULTIPLY", t.out(sep, "Z"), 60.0))
	stakes = t.math("SINE", t.math("MULTIPLY", angle, 24.0))
	weave = t.math("MULTIPLY_ADD", t.math("MULTIPLY", rounds, t.math("SIGN", stakes)), 0.5, 0.5)
	colour = t.node("ShaderNodeMix", {"A": (0.12, 0.08, 0.05, 1), "B": (0.36, 0.28, 0.18, 1), "Factor": weave},
		data_type="RGBA")
	# strands vary in colour, some greyed with age
	age = t.node("ShaderNodeTexNoise", {"Vector": t.vmath("MULTIPLY", p, (3, 3, 30)), "Scale": 2.0})
	aged = t.node("ShaderNodeMix", {"A": t.out(colour, "Result"), "B": (0.3, 0.29, 0.26, 1),
		"Factor": t.math("MULTIPLY", t.map_range(t.out(age, "Fac"), 0.45, 0.7), 0.6)}, data_type="RGBA")
	result = box._grime(t, p, t.out(aged, "Result"), t.out(sep, "Z"), 1.2)
	t.links.new(result, cat_module._sock(bsdf.inputs, "Base Color"))
	bsdf.inputs["Roughness"].default_value = 0.85
	bump = t.node("ShaderNodeBump", {"Height": weave, "Strength": 0.6})
	t.links.new(t.out(bump, "Normal"), cat_module._sock(bsdf.inputs, "Normal"))
	return material


def _strands(name, colour, roughness=0.6):
	material = bpy.data.materials.new(name)
	material.use_nodes = True
	t = cat_module._Tree(material.node_tree)
	t.nodes.clear()
	hair = t.node("ShaderNodeBsdfHairPrincipled", {"Color": (*colour, 1), "Roughness": roughness,
		"Radial Roughness": 0.8}, parametrization="COLOR")
	t.links.new(t.out(hair, 0), t.node("ShaderNodeOutputMaterial").inputs["Surface"])
	return material


class Bed:
	"""A biter bed ("plush") or a spitter basket ("basket"); colour() dresses it for a variation, burst() breaks it."""

	def __init__(self, kind):
		self.kind = kind
		self.pieces = []  # (object, how it falls: tip degrees, slide, twist degrees)
		self.tufts = []
		if kind == "plush":
			self._plush()
		else:
			self._basket()
		self.parts = [obj for obj, _ in self.pieces] + self.tufts
		self.burst(0.0)

	def _plush(self):
		radius, minor, squash, centre_z = 1.25, 0.36, 0.75, 0.27
		count = 7
		stuffing = _strands("Stuffing", (0.42, 0.38, 0.32), 0.9)
		self.cloth = []
		for i in range(count):
			a0, a1 = 2 * math.pi * i / count, 2 * math.pi * (i + 1) / count
			mid = (a0 + a1) / 2
			arc = _piece(f"Bolster{i}", mid, radius + minor, lambda bm, add, a0=a0, a1=a1:
				_ring_arc(bm, add, a0, a1, radius, centre_z, minor, squash))
			self.pieces.append((arc, None))
			self.cloth.append(arc)
			joint = Vector((radius * math.cos(a0), radius * math.sin(a0), centre_z + 0.1))
			self.tufts.append(_tufts(f"Stuffing{i}", joint, stuffing, 420, 0.55, 0.014, 0.12, 40 + i))
		self.cushion = []
		for side in (1, -1):
			half = _piece(f"Cushion{side}", math.pi / 2 * side, 0.0, lambda bm, add, side=side:
				_half_disc(bm, add, side, 1.05, 0.02, 0.15))
			self.pieces.append((half, None))
			self.cushion.append(half)
		for k in range(2):
			self.tufts.append(_tufts(f"CushionStuffing{k}", Vector((-0.35 + 0.7 * k, 0, 0.12)), stuffing, 300, 0.42,
				0.014, 0.14, 60 + k))

	def _basket(self):
		radius, height, thickness = 1.34, 0.55, 0.06
		count = 9
		splinters = _strands("Splinters", (0.36, 0.27, 0.17), 0.5)
		self.cloth = []
		self.weave = []
		for i in range(count):
			a0, a1 = 2 * math.pi * i / count, 2 * math.pi * (i + 1) / count
			mid = (a0 + a1) / 2

			def build(bm, add, a0=a0, a1=a1):
				_shell_arc(bm, add, a0, a1, radius, height, thickness)
				_ring_arc(bm, add, a0, a1, radius + thickness / 2, height, 0.07, steps=10, around=10)
			stave = _piece(f"Stave{i}", mid, radius + thickness, build)
			self.pieces.append((stave, None))
			self.weave.append(stave)
			joint = Vector(((radius + 0.03) * math.cos(a0), (radius + 0.03) * math.sin(a0), height * 0.6))
			self.tufts.append(_tufts(f"Splinters{i}", joint, splinters, 14, 0.22, 0.012, 0.03, 80 + i))
		blanket = _piece("Blanket", 0.0, 0.0, lambda bm, add: (_half_disc(bm, add, 1, 1.3, 0.02, 0.22),
			_half_disc(bm, add, -1, 1.3, 0.02, 0.22)))
		blanket.modifiers.new("Round", "BEVEL").width = 0.06
		self.pieces.append((blanket, None))
		self.cloth.append(blanket)

	def colour(self, variation, colour):
		"""Dresses the bed in a variation's colour, and picks how each piece will fall."""
		if self.kind == "plush":
			material = fabric(f"Bed{variation}", colour)
			lighter = fabric(f"Cushion{variation}", tuple(min(1, c * 1.15 + 0.08) for c in colour))
			for obj in self.cloth:
				_dress(obj, material)
			for obj in self.cushion:
				_dress(obj, lighter)
		else:
			weave = wicker()
			for obj in self.weave:
				_dress(obj, weave)
			_dress(self.cloth[0], fabric(f"Blanket{variation}", colour, plaid=True))
		random.seed(500 + variation)
		self.falls = []
		for obj, _ in self.pieces:
			if obj.name.startswith(("Bolster", "Stave")):
				self.falls.append((random.uniform(45, 88), random.uniform(0.05, 0.25), random.uniform(-18, 18)))
			elif obj.name.startswith("Cushion"):
				self.falls.append((7, 0.1, 0))
			else:
				self.falls.append((0, 0, 0))

	def burst(self, amount):
		"""0 whole, 1 broken: every piece tipped outward, slid out and twisted by its own amount."""
		self.amount = amount
		for (obj, _), fall in zip(self.pieces, getattr(self, "falls", [(0, 0, 0)] * len(self.pieces))):
			tip, slide, twist = fall
			if obj.name == "Blanket":
				continue
			mid = obj["mid"]
			if "base" not in obj:
				obj["base"] = tuple(obj.location)
			# tipped about its outer bottom edge (the cushion halves about their middle, so they part and lift)
			out = Vector((math.cos(mid), math.sin(mid), 0))
			obj.location = Vector(obj["base"]) + out * slide * amount
			obj.rotation_euler = (0, math.radians(tip) * amount, mid + math.radians(twist) * amount)
		for tuft in self.tufts:
			grow = min(1.0, max(0.0, (amount - 0.15) / 0.5))
			tuft.scale = (grow,) * 3

# The worms' cardboard box: open at the top, four flaps hinged on its rim, corrugated brown card with a strip of tape
# down each long flap and a paw print stamped on the front. It stands at the origin and doesn't turn with the cat.
import math

import bmesh
import bpy

import cat as cat_module

WIDTH, DEPTH, HEIGHT = 1.5, 1.25, 0.72
CARD = 0.025


def _cardboard(name, tape=False, paw=False):
	material = bpy.data.materials.new(name)
	material.use_nodes = True
	t = cat_module._Tree(material.node_tree)
	bsdf = t.nodes["Principled BSDF"]
	p = t.out(t.node("ShaderNodeTexCoord"), "Object")
	sep = t.node("ShaderNodeSeparateXYZ", {"Vector": p})
	x, y, z = t.out(sep, "X"), t.out(sep, "Y"), t.out(sep, "Z")
	# fine corrugation and some scuffing on brown card
	ribs = t.node("ShaderNodeTexWave", {"Vector": p, "Scale": 26.0, "Distortion": 0.4}, wave_type="BANDS",
		bands_direction="Z")
	scuff = t.node("ShaderNodeTexNoise", {"Vector": p, "Scale": 9.0, "Detail": 4.0})
	shade = t.math("ADD", t.math("MULTIPLY", t.out(ribs, "Fac"), 0.06), t.math("MULTIPLY", t.out(scuff, "Fac"), 0.18))
	colour = t.node("ShaderNodeMix", {"A": (0.42, 0.27, 0.13, 1), "B": (0.66, 0.47, 0.27, 1), "Factor": shade},
		data_type="RGBA")
	result = t.out(colour, "Result")
	if tape:
		# a band of shiny tan tape along the flap's middle
		band = t.map_range(t.math("ABSOLUTE", x), 0.13, 0.11)
		result = t.out(t.node("ShaderNodeMix", {"A": result, "B": (0.78, 0.62, 0.38, 1), "Factor": band},
			data_type="RGBA"), "Result")
		bsdf.inputs["Roughness"].default_value = 0.55
	if paw:
		# a paw print on the front: a big pad and four toes, in dark ink
		def pad(cx, cz, rx, rz):
			dx = t.math("DIVIDE", t.math("SUBTRACT", x, cx), rx)
			dz = t.math("DIVIDE", t.math("SUBTRACT", z, cz), rz)
			return t.math("LESS_THAN", t.math("ADD", t.math("MULTIPLY", dx, dx), t.math("MULTIPLY", dz, dz)), 1.0)
		ink = pad(0.0, HEIGHT * 0.38, 0.17, 0.12)
		for cx, cz in ((-0.2, 0.6), (-0.075, 0.68), (0.075, 0.68), (0.2, 0.6)):
			ink = t.math("MAXIMUM", ink, pad(cx, HEIGHT * cz, 0.06, 0.065))
		front = t.math("LESS_THAN", y, -DEPTH / 2 + 0.01)
		ink = t.math("MULTIPLY", ink, front)
		result = t.out(t.node("ShaderNodeMix", {"A": result, "B": (0.16, 0.08, 0.05, 1), "Factor": ink},
			data_type="RGBA"), "Result")
	t.links.new(result, cat_module._sock(bsdf.inputs, "Base Color"))
	if not tape:
		bsdf.inputs["Roughness"].default_value = 0.85
	return material


class Box:
	"""The box and its flaps; open() swings them from closed (0) to wide open (1)."""

	def __init__(self):
		mesh = bpy.data.meshes.new("Box")
		bm = bmesh.new()
		w, d, h = WIDTH / 2, DEPTH / 2, HEIGHT
		corners = [bm.verts.new(c) for c in ((-w, -d, 0), (w, -d, 0), (w, d, 0), (-w, d, 0),
			(-w, -d, h), (w, -d, h), (w, d, h), (-w, d, h))]
		for face in ((0, 1, 2, 3), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
			bm.faces.new([corners[i] for i in face])
		bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
		bm.to_mesh(mesh)
		bm.free()
		self.body = bpy.data.objects.new("Box", mesh)
		bpy.context.scene.collection.objects.link(self.body)
		solid = self.body.modifiers.new("Card", "SOLIDIFY")
		solid.thickness = CARD
		bevel = self.body.modifiers.new("Bevel", "BEVEL")
		bevel.width = 0.012
		bevel.segments = 2
		self.body.data.materials.append(_cardboard("Card", paw=True))
		self.flaps = []
		# long flaps on the front and back, short ones at the sides; each hinged on its rim edge
		for name, hinge, length, span, axis, outward in (
				("Front", (0, -d, h), DEPTH * 0.46, WIDTH, "X", -1), ("Back", (0, d, h), DEPTH * 0.46, WIDTH, "X", 1),
				("Left", (-w, 0, h), WIDTH * 0.42, DEPTH, "Y", -1), ("Right", (w, 0, h), WIDTH * 0.42, DEPTH, "Y", 1)):
			flap_mesh = bpy.data.meshes.new(name)
			bm = bmesh.new()
			if axis == "X":
				# lying flat it reaches over the opening (towards -outward in Y)
				quad = [(-span / 2, 0, 0), (span / 2, 0, 0), (span / 2, -outward * length, 0), (-span / 2, -outward * length, 0)]
			else:
				quad = [(0, -span / 2, 0), (0, span / 2, 0), (-outward * length, span / 2, 0), (-outward * length, -span / 2, 0)]
			bm.faces.new([bm.verts.new(v) for v in quad])
			bm.to_mesh(flap_mesh)
			bm.free()
			flap = bpy.data.objects.new(name, flap_mesh)
			bpy.context.scene.collection.objects.link(flap)
			flap.location = hinge
			flap.modifiers.new("Card", "SOLIDIFY").thickness = CARD
			flap.data.materials.append(_cardboard(name + "Card", tape=axis == "X"))
			self.flaps.append((flap, axis, outward))
		self.parts = [self.body] + [f for f, _, _ in self.flaps]

	def open(self, openness, wiggle=0.0):
		"""0: flaps folded flat over the top, the long ones a gap apart; 1: swung open and leaning out past upright.
		wiggle lifts them a little, for a box with something stirring inside."""
		for i, (flap, axis, outward) in enumerate(self.flaps):
			# the side flaps fold under the long ones when closed
			closed = 2 if axis == "X" else -3
			angle = math.radians(closed + (125 - closed) * openness + wiggle * (6 + 3 * i))
			if axis == "X":
				flap.rotation_euler = (-outward * angle, 0, 0)
			else:
				flap.rotation_euler = (0, outward * angle, 0)

# A cat built in code: a metaball body with mesh ears for soft cartoon proportions, glossy eyes, a nose, and procedural
# fur from geometry nodes. The cat stands at the origin facing +Y (north), at the size of a scale 1 sprite.
#
# The fur is a separate Curves object (Cycles here doesn't render curves made by a mesh object's nodes), grown once on
# the rest pose and bent with the posed body by Deform Curves on Surface, so a strand stays on the same spot of skin
# from frame to frame.
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

METABALL_SURFACE = 0.575  # an isolated ball's surface radius, per unit of metaball radius

HEAD = Vector((0, 0.62, 0.98))
HEAD_RADIUS = 0.46
EYES = [Vector((side * 0.185, 0.955, 1.02)) for side in (-1, 1)]
EYE_RADIUS = 0.125
MUZZLE = HEAD + Vector((0, 0.33, -0.14))
NOSE = Vector((0, 1.075, 0.925))


def _catmull_rom(points, per_segment):
	"""A smooth curve through the points, per_segment samples between each pair."""
	padded = [points[0] * 2 - points[1], *points, points[-1] * 2 - points[-2]]
	out = []
	for i in range(1, len(padded) - 2):
		p0, p1, p2, p3 = padded[i - 1:i + 3]
		for j in range(per_segment):
			t = j / per_segment
			out.append(0.5 * (2 * p1 + (p2 - p0) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
				+ (3 * p1 - p0 - 3 * p2 + p3) * t * t * t))
	out.append(points[-1])
	return out


# a slim tail raised in a happy curl, tapering towards the tip
TAIL = _catmull_rom([Vector(p) for p in ((0, -0.55, 0.64), (0, -0.78, 0.74), (0, -0.88, 0.98), (0, -0.88, 1.22),
	(0, -0.78, 1.4), (0, -0.64, 1.44))], 3)
TAIL_RADII = [0.068 - 0.03 * i / (len(TAIL) - 1) for i in range(len(TAIL))]
# each ear: its base on the head, tilted outward and a little back
EARS = [Matrix.Translation(HEAD + Vector((side * 0.25, -0.06, 0.31)))
	@ Matrix.Rotation(math.radians(-side * 24), 4, "Y") @ Matrix.Rotation(math.radians(-10), 4, "X")
	@ Matrix.Rotation(math.radians(side * 14), 4, "Z") for side in (-1, 1)]

# The fur renders white; Factorio tints it with mask layers. A pattern set is a white-patch level and a kind of
# markings, each giving a coat mask (everything not white) and a markings mask (stripes or patches on the coat).
PATTERNS = {
	"tabby": {"marks": "stripes", "white": "low"},
	"tabby-white": {"marks": "stripes", "white": "high"},
	"patches": {"marks": "patches", "white": "low"},
	"patches-white": {"marks": "patches", "white": "high"},
	"points": {"marks": "points", "white": "none"},
}
IRIS = ((0.45, 0.75, 0.15), (0.95, 0.75, 0.2))

# Fur styles: lengths are multiples of the short coat's; the rest shape each strand (how far it rises off the skin, how
# hard the tips clump, how much they wander) and how many there are per square tile.
STYLES = {
	"shorthair": {"body": 1.0, "face": 1.0, "ruff": 1.0, "tail": 1.0, "legs": 1.0, "lift": 0.32, "clump": 0.75,
		"frizz": 0.4, "density": 60000, "radius": 0.0026},
	"longhair": {"body": 1.9, "face": 1.25, "ruff": 2.0, "tail": 2.3, "legs": 1.6, "lift": 0.5, "clump": 0.85,
		"frizz": 0.75, "density": 48000, "radius": 0.003},
}


def _metaball_mesh():
	mb = bpy.data.metaballs.new("CatBody")
	mb.resolution = 0.04
	mb.render_resolution = 0.02
	mb.threshold = 0.6

	def ball(co, r, size=(1, 1, 1), negative=False):
		e = mb.elements.new(type="ELLIPSOID")
		e.co = co
		e.radius = r / METABALL_SURFACE
		e.size_x, e.size_y, e.size_z = size
		e.use_negative = negative

	def capsule(a, b, r):
		a, b = Vector(a), Vector(b)
		e = mb.elements.new(type="CAPSULE")
		e.co = (a + b) / 2
		e.radius = r / METABALL_SURFACE
		e.size_x = (b - a).length / 2
		e.rotation = Vector((1, 0, 0)).rotation_difference(b - a)

	# a short round torso
	ball((0, 0.22, 0.58), 0.31)
	ball((0, -0.1, 0.54), 0.3, (1.05, 1.05, 0.95))
	ball((0, -0.36, 0.57), 0.3)
	# a big round head on a short neck, with cheeks, a little muzzle and chin
	capsule((0, 0.3, 0.68), HEAD + Vector((0, -0.1, -0.12)), 0.22)
	ball(HEAD, HEAD_RADIUS, (1.12, 0.95, 0.9))
	for side in (-1, 1):
		ball(HEAD + Vector((side * 0.22, 0.17, -0.13)), 0.2, (1.1, 0.9, 0.85))
	ball(MUZZLE, 0.14, (1.25, 0.85, 0.8))
	ball(MUZZLE + Vector((0, -0.04, -0.09)), 0.09, (1.1, 1, 0.8))
	for side in (-1, 1):
		x = side * 0.15
		# front legs: shoulder, elbow, wrist, paw
		ball((x, 0.26, 0.45), 0.14)
		capsule((x, 0.28, 0.42), (x * 1.05, 0.3, 0.2), 0.1)
		capsule((x * 1.05, 0.3, 0.2), (x * 1.08, 0.32, 0.07), 0.09)
		ball((x * 1.08, 0.36, 0.06), 0.095, (1, 1.25, 0.7))
		# hind legs: thigh, shin, hock, paw
		ball((x * 1.1, -0.38, 0.45), 0.22, (0.9, 1.1, 1.1))
		capsule((x * 1.15, -0.32, 0.3), (x * 1.15, -0.48, 0.14), 0.1)
		capsule((x * 1.15, -0.48, 0.14), (x * 1.12, -0.42, 0.07), 0.085)
		ball((x * 1.12, -0.37, 0.06), 0.095, (1, 1.25, 0.7))
	# a tail raised in a happy curl
	for i in range(len(TAIL) - 1):
		capsule(TAIL[i], TAIL[i + 1], TAIL_RADII[i])
	# sockets for the eyes
	for eye in EYES:
		ball(eye + Vector((0, 0.035, 0)), EYE_RADIUS * 0.9, negative=True)

	obj = bpy.data.objects.new("CatBody", mb)
	bpy.context.scene.collection.objects.link(obj)
	depsgraph = bpy.context.evaluated_depsgraph_get()
	mesh = bpy.data.meshes.new_from_object(obj.evaluated_get(depsgraph))
	bpy.data.objects.remove(obj)
	bpy.data.metaballs.remove(mb)
	return mesh


def _ear_mesh(matrix):
	"""A rounded, flattened cone standing on the head; its front (+Y in ear space) is the open, pink side."""
	bm = bmesh.new()
	bmesh.ops.create_cone(bm, cap_ends=True, segments=24, radius1=0.21, radius2=0.035, depth=0.5)
	for v in bm.verts:
		v.co.z += 0.25 - 0.1  # the base sinks into the head
		v.co.y *= 0.42
		# the front hollows a little towards the middle
		if v.co.y > 0:
			v.co.y -= 0.025 * (1 - min(1, abs(v.co.x) / 0.12))
	bm.transform(matrix)
	mesh = bpy.data.meshes.new("Ear")
	bm.to_mesh(mesh)
	bm.free()
	return mesh


def _body():
	bm = bmesh.new()
	meshes = [_metaball_mesh(), *(_ear_mesh(m) for m in EARS)]
	for mesh in meshes:
		bm.from_mesh(mesh)
		bpy.data.meshes.remove(mesh)
	mesh = bpy.data.meshes.new("CatBody")
	bm.to_mesh(mesh)
	bm.free()
	body = bpy.data.objects.new("CatBody", mesh)
	bpy.context.scene.collection.objects.link(body)
	# one even quad mesh, ears and all, for the fur and the rig
	remesh = body.modifiers.new("Remesh", "REMESH")
	remesh.mode = "VOXEL"
	remesh.voxel_size = 0.014
	smooth = body.modifiers.new("Smooth", "SMOOTH")
	smooth.iterations = 3
	smooth.factor = 0.5
	depsgraph = bpy.context.evaluated_depsgraph_get()
	applied = bpy.data.meshes.new_from_object(body.evaluated_get(depsgraph))
	body.modifiers.clear()
	body.data = applied
	bpy.data.meshes.remove(mesh)
	for polygon in body.data.polygons:
		polygon.use_smooth = True
	body.add_rest_position_attribute = True
	return body


def _smoothstep(edge0, edge1, x):
	t = min(max((x - edge0) / (edge1 - edge0), 0.0), 1.0)
	return t * t * (3 - 2 * t)


def _fur_fields(body, style):
	"""Per vertex fur length, comb direction and bare pink skin, from where on the cat the vertex is."""
	mesh = body.data
	length = mesh.attributes.new("fur_len", "FLOAT", "POINT")
	comb = mesh.attributes.new("comb", "FLOAT_VECTOR", "POINT")
	pink = mesh.attributes.new("pink", "FLOAT", "POINT")
	ears = [(m.inverted(), m.to_3x3() @ Vector((0, 1, 0))) for m in EARS]
	for v in mesh.vertices:
		p = v.co
		n = v.normal
		fur = 0.065 * style["body"]
		direction = Vector((0, -1, -0.35))
		bare = 0.0
		# legs and paws: short, combed down
		leg = 1 - _smoothstep(0.22, 0.4, p.z)
		fur = fur * (1 - leg) + 0.035 * style["legs"] * leg
		direction = direction.lerp(Vector((0, -0.15, -1)), leg)
		paw = 1 - _smoothstep(0.07, 0.13, p.z)
		fur = fur * (1 - paw) + 0.02 * min(1.3, style["legs"]) * paw
		# a fluffy chest ruff, combed down
		ruff = 1 - _smoothstep(0.12, 0.32, (p - Vector((0, 0.42, 0.62))).length)
		fur = max(fur, 0.11 * style["ruff"] * ruff * _smoothstep(-0.2, 0.4, n.y))
		direction = direction.lerp(Vector((0, 0.25, -1)), ruff)
		# the head: short on the face, fluffy cheeks combed outwards
		head = 1 - _smoothstep(HEAD_RADIUS - 0.04, HEAD_RADIUS + 0.08, (p - HEAD).length)
		fur = fur * (1 - head) + 0.04 * style["face"] * head
		direction = direction.lerp(Vector((0, -1, 0.2)), head)
		face = head * _smoothstep(0.1, 0.5, n.y) * _smoothstep(HEAD.y + 0.1, HEAD.y + 0.3, p.y)
		fur = fur * (1 - face) + 0.016 * style["face"] * face
		direction = direction.lerp((p - MUZZLE).normalized(), face)
		for side in (-1, 1):
			cheek = 1 - _smoothstep(0.08, 0.2, (p - (HEAD + Vector((side * 0.34, 0.12, -0.15)))).length)
			fur = max(fur, 0.09 * style["ruff"] * cheek)
			direction = direction.lerp(Vector((side, -0.4, -0.35)), cheek)
		# the ears: short fur behind, bare and pink in front
		for inverse, forward in ears:
			local = inverse @ p
			if local.z > 0.0 and abs(local.x) < 0.24 and abs(local.y) < 0.14:
				# a little tuft at the tips on long coats
				fur = 0.014 + 0.03 * (style["face"] - 1) * _smoothstep(0.2, 0.3, local.z)
				direction = Vector((0, 0, 1))
				inner = _smoothstep(-0.2, 0.3, n.dot(forward)) * (1 - _smoothstep(0.1, 0.15, abs(local.x)
					+ 0.4 * max(0, 0.12 - local.z)))
				bare = max(bare, inner)
				fur *= 1 - inner
		# the tail: long, combed towards the tip
		segment = min(range(len(TAIL) - 1), key=lambda i: (p - (TAIL[i] + TAIL[i + 1]) / 2).length)
		if (p - (TAIL[segment] + TAIL[segment + 1]) / 2).length < 0.15 and p.y < -0.5:
			fur = 0.075 * style["tail"]
			direction = TAIL[segment + 1] - TAIL[segment]
		# none around the eyes and nose
		for eye in EYES:
			fur *= _smoothstep(EYE_RADIUS + 0.005, EYE_RADIUS + 0.05, (p - eye).length)
		fur *= _smoothstep(0.03, 0.07, (p - NOSE).length)
		length.data[v.index].value = fur
		comb.data[v.index].vector = direction.normalized()
		pink.data[v.index].value = bare


def _sock(sockets, name):
	# nodes like Mix have a socket of each name per data type, with only the one in use enabled
	for socket in sorted(sockets, key=lambda s: not s.enabled):
		if socket.name == name or socket.identifier == name:
			return socket
	raise KeyError(f"{name} not in {[s.name for s in sockets]}")


class _Tree:
	"""A small helper for building node trees in code."""

	def __init__(self, tree):
		self.tree = tree
		self.nodes = tree.nodes
		self.links = tree.links

	def node(self, kind, inputs=None, **props):
		n = self.nodes.new(kind)
		for key, value in props.items():
			setattr(n, key, value)
		for name, value in (inputs or {}).items():
			self.set(n, name, value)
		return n

	def set(self, n, name, value):
		socket = _sock(n.inputs, name) if isinstance(name, str) else n.inputs[name]
		if isinstance(value, bpy.types.NodeSocket):
			self.links.new(value, socket)
		else:
			socket.default_value = value

	def out(self, n, name=0):
		return _sock(n.outputs, name) if isinstance(name, str) else n.outputs[name]

	def math(self, op, a, b=None, c=None):
		n = self.node("ShaderNodeMath", operation=op)
		for i, v in enumerate((a, b, c)):
			if v is not None:
				self.set(n, i, v)
		return n.outputs[0]

	def vmath(self, op, a, b=None, scale=None):
		n = self.node("ShaderNodeVectorMath", operation=op)
		for i, v in enumerate((a, b)):
			if v is not None:
				self.set(n, i, v)
		if scale is not None:
			self.set(n, "Scale", scale)
		return n.outputs["Value" if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else "Vector"]

	def map_range(self, value, from_min, from_max):
		return self.out(self.node("ShaderNodeMapRange", {"Value": value, "From Min": from_min, "From Max": from_max}),
			"Result")


def _fur(body, fur_material, style):
	"""Fur grown on the rest pose once, then bent along with the posed body by Deform Curves on Surface."""
	# the strands find their spot on the skin again each frame by its UV coordinate
	bpy.context.view_layer.objects.active = body
	for obj in bpy.context.view_layer.objects:
		obj.select_set(obj is body)
	bpy.ops.object.mode_set(mode="EDIT")
	bpy.ops.mesh.select_all(action="SELECT")
	bpy.ops.uv.smart_project(island_margin=0.002)
	bpy.ops.object.mode_set(mode="OBJECT")

	tree = bpy.data.node_groups.new("CatFurGrow", "GeometryNodeTree")
	tree.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
	tree.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
	t = _Tree(tree)
	t.node("NodeGroupInput")
	group_out = t.node("NodeGroupOutput")

	def named(name, data_type="FLOAT_VECTOR"):
		return t.out(t.node("GeometryNodeInputNamedAttribute", {"Name": name}, data_type=data_type), "Attribute")

	def store(geometry, name, value, data_type="FLOAT_VECTOR", domain="POINT"):
		n = t.node("GeometryNodeStoreNamedAttribute", {"Geometry": geometry, "Name": name, "Value": value},
			data_type=data_type, domain=domain)
		return t.out(n, "Geometry")

	skin = t.out(t.node("GeometryNodeObjectInfo", {"Object": body}, transform_space="RELATIVE"), "Geometry")
	has_fur = t.out(t.node("FunctionNodeCompare", {"A": named("fur_len", "FLOAT"), "B": 0.004},
		data_type="FLOAT", operation="GREATER_THAN"), "Result")
	distribute = t.node("GeometryNodeDistributePointsOnFaces", {"Mesh": skin, "Selection": has_fur,
		"Density": style["density"], "Seed": 7}, distribute_method="RANDOM")
	points = t.out(distribute, "Points")
	position = t.out(t.node("GeometryNodeInputPosition"), "Position")

	def sample(value, data_type="FLOAT_VECTOR"):
		n = t.node("GeometryNodeSampleNearestSurface", {"Mesh": skin, "Value": value}, data_type=data_type)
		return t.out(n, "Value")

	n = t.vmath("NORMALIZE", t.out(distribute, "Normal"))
	comb = sample(named("comb"))
	comb = t.vmath("NORMALIZE", t.vmath("SUBTRACT", comb, t.vmath("SCALE", n, scale=t.vmath("DOT_PRODUCT", comb, n))))
	random = t.out(t.node("FunctionNodeRandomValue", {"Min": 0.75, "Max": 1.2, "Seed": 3}, data_type="FLOAT"), 0)
	length = t.math("MULTIPLY", sample(named("fur_len", "FLOAT"), "FLOAT"), random)
	points = store(points, "root", position)
	points = store(points, "n", n)
	points = store(points, "t", comb)
	points = store(points, "len", length, "FLOAT")
	points = store(points, "uv", sample(named("UVMap")))

	line = t.node("GeometryNodeCurvePrimitiveLine", {"Start": (0, 0, 0), "End": (0, 0, 1)})
	line = t.node("GeometryNodeResampleCurve", {"Curve": t.out(line, "Curve"), "Count": 6})
	instances = t.node("GeometryNodeInstanceOnPoints", {"Points": points, "Instance": t.out(line, "Curve")})
	curves = t.out(t.node("GeometryNodeRealizeInstances", {"Geometry": t.out(instances, "Instances")}), "Geometry")

	# each strand rises off the skin and lies down along the comb direction
	f = t.out(t.node("GeometryNodeSplineParameter"), "Factor")
	lift = t.math("MULTIPLY", t.math("MULTIPLY", f, t.math("MULTIPLY_ADD", f, -0.6, 1.0)), style["lift"])
	along = t.math("MULTIPLY", f, t.math("MULTIPLY_ADD", f, 0.6, 0.4))
	strand = t.vmath("ADD", t.vmath("SCALE", named("n"), scale=lift), t.vmath("SCALE", named("t"), scale=along))
	strand = t.vmath("SCALE", strand, scale=named("len", "FLOAT"))
	# clumps: the tips lean towards the centre of their Voronoi cell
	root = named("root")
	voronoi = t.node("ShaderNodeTexVoronoi", {"Vector": root, "Scale": 36.0}, voronoi_dimensions="3D")
	clump = t.vmath("SCALE", t.vmath("SUBTRACT", t.out(voronoi, "Position"), root),
		scale=t.math("MULTIPLY", t.math("POWER", f, 1.5), style["clump"]))
	noise = t.node("ShaderNodeTexNoise", {"Vector": t.vmath("SCALE", root, scale=40.0), "Scale": 1.0,
		"Detail": 1.0}, noise_dimensions="3D")
	frizz = t.vmath("SCALE", t.vmath("SUBTRACT", t.out(noise, "Color"), (0.5, 0.5, 0.5)),
		scale=t.math("MULTIPLY", t.math("MULTIPLY", f, named("len", "FLOAT")), style["frizz"]))
	tip = t.vmath("ADD", t.vmath("ADD", root, strand), t.vmath("ADD", clump, frizz))
	curves = t.out(t.node("GeometryNodeSetPosition", {"Geometry": curves, "Position": tip}), "Geometry")
	radius = t.math("MULTIPLY", t.math("MULTIPLY_ADD", f, -0.85, 1.0), style["radius"])
	curves = t.out(t.node("GeometryNodeSetCurveRadius", {"Curve": curves, "Radius": radius}), "Curve")
	curves = store(curves, "root_rest", root, domain="CURVE")
	curves = store(curves, "surface_uv_coordinate", named("uv"), "FLOAT2", "CURVE")
	t.links.new(curves, group_out.inputs[0])

	fur = bpy.data.objects.new("CatFur", bpy.data.hair_curves.new("CatFur"))
	bpy.context.scene.collection.objects.link(fur)
	fur.data.materials.append(fur_material)
	fur.modifiers.new("Grow", "NODES").node_group = tree
	bpy.context.view_layer.objects.active = fur
	bpy.ops.object.modifier_apply(modifier="Grow")
	bpy.data.node_groups.remove(tree)
	# applying takes the nodes' (empty) material list, and the working attributes came along
	fur.data.materials.clear()
	fur.data.materials.append(fur_material)
	for name in [a.name for a in fur.data.attributes]:
		if name not in ("position", "radius", "curve_type", "root_rest", "surface_uv_coordinate"):
			fur.data.attributes.remove(fur.data.attributes[name])

	fur.parent = body
	fur.data.surface = body
	fur.data.surface_uv_map = "UVMap"
	deform = bpy.data.node_groups.new("CatFurDeform", "GeometryNodeTree")
	deform.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
	deform.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
	d = _Tree(deform)
	node = d.node("GeometryNodeDeformCurvesOnSurface", {"Curves": d.out(d.node("NodeGroupInput"), 0)})
	d.links.new(d.out(node, 0), d.node("NodeGroupOutput").inputs[0])
	fur.modifiers.new("Deform", "NODES").node_group = deform
	return fur


def _white(t, p, level):
	"""Shader nodes for how white the coat is at rest position p: not at all, a little (belly, chest, muzzle, paws) or
	a lot."""
	if level == "none":
		return t.math("MULTIPLY", 0.0, 0.0)
	sep = t.node("ShaderNodeSeparateXYZ", {"Vector": p})
	x, y, z = t.out(sep, "X"), t.out(sep, "Y"), t.out(sep, "Z")
	absx = t.math("ABSOLUTE", x)
	high = level == "high"
	middle = t.map_range(absx, 0.28 if high else 0.2, 0.16 if high else 0.1)
	belly = t.math("MULTIPLY", t.map_range(z, 0.52 if high else 0.42, 0.42 if high else 0.32), middle)
	chest = t.math("MULTIPLY", t.math("MULTIPLY", t.map_range(y, 0.22 if high else 0.3, 0.36 if high else 0.45),
		t.map_range(z, 0.98 if high else 0.88, 0.84 if high else 0.75)), middle)
	muzzle = t.map_range(t.vmath("DISTANCE", p, tuple(MUZZLE + Vector((0, 0, -0.03)))), 0.3 if high else 0.25,
		0.22 if high else 0.18)
	paws = t.map_range(z, 0.32 if high else 0.14, 0.24 if high else 0.09)
	white = t.math("MAXIMUM", t.math("MAXIMUM", belly, chest), t.math("MAXIMUM", muzzle, paws))
	if high:
		# a white blaze up the middle of the face
		blaze = t.math("MULTIPLY", t.map_range(absx, 0.07, 0.03), t.map_range(y, HEAD.y + 0.2, HEAD.y + 0.3))
		white = t.math("MAXIMUM", white, blaze)
	return white


def _marks(t, p, kind):
	"""Shader nodes for tabby stripes, calico patches or colour points at rest position p."""
	if kind == "stripes":
		wave = t.node("ShaderNodeTexWave", {"Vector": p, "Scale": 2.1, "Distortion": 5.0, "Detail": 2.0,
			"Detail Scale": 1.5}, wave_type="BANDS", bands_direction="Y")
		return t.map_range(t.out(wave, "Fac"), 0.62, 0.85)
	if kind == "points":
		# dark towards the extremities: the face mask, ears, legs and tail, shading off over the body
		sep = t.node("ShaderNodeSeparateXYZ", {"Vector": p})
		y, z = t.out(sep, "Y"), t.out(sep, "Z")
		face = t.map_range(t.vmath("DISTANCE", p, tuple(MUZZLE)), 0.3, 0.14)
		ears = t.map_range(z, HEAD.z + 0.3, HEAD.z + 0.42)
		legs = t.map_range(z, 0.36, 0.2)
		tail = t.map_range(y, -0.55, -0.75)
		return t.math("MAXIMUM", t.math("MAXIMUM", face, ears), t.math("MAXIMUM", legs, tail))
	noise = t.node("ShaderNodeTexNoise", {"Vector": p, "Scale": 2.4, "Detail": 3.0, "Roughness": 0.55})
	return t.map_range(t.out(noise, "Fac"), 0.5, 0.56)


def _fur_material():
	material = bpy.data.materials.new("CatFur")
	material.use_nodes = True
	t = _Tree(material.node_tree)
	t.nodes.clear()
	hair = t.node("ShaderNodeBsdfHairPrincipled", {"Color": (0.92, 0.9, 0.87, 1), "Roughness": 0.4,
		"Radial Roughness": 0.7, "Coat": 0.08, "Random Roughness": 0.2}, parametrization="COLOR")
	t.links.new(t.out(hair, 0), t.node("ShaderNodeOutputMaterial").inputs["Surface"])
	return material


def _skin_material():
	material = bpy.data.materials.new("CatSkin")
	material.use_nodes = True
	t = _Tree(material.node_tree)
	pink = t.out(t.node("ShaderNodeAttribute", attribute_name="pink", attribute_type="GEOMETRY"), "Fac")
	base = t.node("ShaderNodeMix", {"A": (0.85, 0.83, 0.8, 1), "B": (0.95, 0.55, 0.55, 1), "Factor": pink},
		data_type="RGBA")
	bsdf = t.nodes["Principled BSDF"]
	t.links.new(t.out(base, "Result"), _sock(bsdf.inputs, "Base Color"))
	bsdf.inputs["Roughness"].default_value = 0.7
	_sock(bsdf.inputs, "Subsurface Weight").default_value = 0.15
	return material


def _mask_material(name, pattern, attribute):
	"""Emits (coat, markings, 0) for a pattern set, unlit: where the coat and markings tints apply."""
	material = bpy.data.materials.new(name)
	material.use_nodes = True
	t = _Tree(material.node_tree)
	t.nodes.clear()
	p = t.out(t.node("ShaderNodeAttribute", attribute_name=attribute, attribute_type="GEOMETRY"), "Vector")
	coat = t.math("SUBTRACT", 1.0, _white(t, p, pattern["white"]))
	if attribute == "rest_position":
		pink = t.out(t.node("ShaderNodeAttribute", attribute_name="pink", attribute_type="GEOMETRY"), "Fac")
		coat = t.math("MULTIPLY", coat, t.math("SUBTRACT", 1.0, pink))
	marks = t.math("MULTIPLY", coat, _marks(t, p, pattern["marks"]))
	colour = t.node("ShaderNodeCombineXYZ", {"X": coat, "Y": marks, "Z": 0.0})
	emission = t.node("ShaderNodeEmission", {"Color": t.out(colour, 0), "Strength": 1.0})
	t.links.new(t.out(emission, 0), t.node("ShaderNodeOutputMaterial").inputs["Surface"])
	return material


def _eye_material():
	material = bpy.data.materials.new("CatEye")
	material.use_nodes = True
	t = _Tree(material.node_tree)
	bsdf = t.nodes["Principled BSDF"]
	local = t.out(t.node("ShaderNodeTexCoord"), "Object")
	angle = t.math("ARCCOSINE", t.vmath("DOT_PRODUCT", t.vmath("NORMALIZE", local), (0, 1, 0)))
	# fine radial streaks in the iris
	streaks = t.node("ShaderNodeTexNoise", {"Vector": t.vmath("MULTIPLY", local, (40, 4, 40)), "Scale": 1.0})
	ring = t.node("ShaderNodeValToRGB", {"Fac": t.math("ADD", t.math("DIVIDE", angle, 1.5),
		t.math("MULTIPLY", t.math("SUBTRACT", t.out(streaks, "Fac"), 0.5), 0.06))})
	ramp = ring.color_ramp
	ramp.interpolation = "EASE"
	inner, outer = IRIS
	stops = [(0.0, (0.0, 0.0, 0.0)), (0.4, (0.01, 0.01, 0.01)), (0.44, inner), (0.64, outer), (0.74, (0.3, 0.18, 0.04)),
		(0.82, (0.08, 0.05, 0.02)), (1.0, (0.05, 0.03, 0.01))]
	ramp.elements[0].position, ramp.elements[0].color = stops[0][0], (*stops[0][1], 1)
	ramp.elements[1].position, ramp.elements[1].color = stops[-1][0], (*stops[-1][1], 1)
	for position, color in stops[1:-1]:
		element = ramp.elements.new(position)
		element.color = (*color, 1)
	t.links.new(t.out(ring, "Color"), _sock(bsdf.inputs, "Base Color"))
	bsdf.inputs["Roughness"].default_value = 0.4
	_sock(bsdf.inputs, "Coat Weight").default_value = 1.0
	_sock(bsdf.inputs, "Coat Roughness").default_value = 0.02
	return material


def _simple_material(name, color, roughness=0.5):
	material = bpy.data.materials.new(name)
	material.use_nodes = True
	bsdf = material.node_tree.nodes["Principled BSDF"]
	bsdf.inputs["Base Color"].default_value = (*color, 1)
	bsdf.inputs["Roughness"].default_value = roughness
	return material


def _eyes():
	material = _eye_material()
	eyes = []
	for side, centre in zip((-1, 1), EYES):
		bpy.ops.mesh.primitive_uv_sphere_add(radius=EYE_RADIUS, location=centre, segments=48, ring_count=24)
		eye = bpy.context.object
		eye.name = "Eye"
		# looking forward and a touch outward and up
		eye.rotation_euler = (math.radians(6), 0, math.radians(-side * 16))
		eye.data.materials.append(material)
		bpy.ops.object.shade_smooth()
		eyes.append(eye)
	return eyes


def _nose():
	bpy.ops.mesh.primitive_uv_sphere_add(radius=0.042, location=NOSE, segments=24, ring_count=12)
	nose = bpy.context.object
	nose.name = "Nose"
	nose.scale = (1.35, 0.8, 0.75)
	nose.data.materials.append(_simple_material("Nose", (0.9, 0.4, 0.45), 0.35))
	bpy.ops.object.shade_smooth()
	return nose


def _drawn_eye_material(name, mask, shape):
	"""Eyes drawn on fur, the fur taking the coat colour in the masks: comical X eyes for a knocked out cat ("x"), or a
	closed eye's curved line for a sleeping one ("closed")."""
	material = bpy.data.materials.new(name)
	material.use_nodes = True
	t = _Tree(material.node_tree)
	local = t.out(t.node("ShaderNodeTexCoord"), "Object")
	sep = t.node("ShaderNodeSeparateXYZ", {"Vector": local})
	u, v = t.out(sep, "X"), t.out(sep, "Z")
	if shape == "x":
		line = t.math("MINIMUM", t.math("ABSOLUTE", t.math("SUBTRACT", u, v)),
			t.math("ABSOLUTE", t.math("ADD", u, v)))
		x = t.math("MULTIPLY", t.math("LESS_THAN", line, 0.024), t.math("LESS_THAN", t.vmath("LENGTH", t.out(
			t.node("ShaderNodeCombineXYZ", {"X": u, "Z": v}), 0)), 0.095))
	else:
		# a contented curve, low in the eye: v = 5 u^2 - 0.03
		curve = t.math("ABSOLUTE", t.math("SUBTRACT", v, t.math("SUBTRACT", t.math("MULTIPLY",
			t.math("MULTIPLY", u, u), 5.0), 0.03)))
		x = t.math("MULTIPLY", t.math("LESS_THAN", curve, 0.016), t.math("LESS_THAN", t.math("ABSOLUTE", u), 0.085))
	if mask:
		t.nodes.remove(t.nodes["Principled BSDF"])
		colour = t.node("ShaderNodeCombineXYZ", {"X": t.math("SUBTRACT", 1.0, x), "Y": 0.0, "Z": 0.0})
		emission = t.node("ShaderNodeEmission", {"Color": t.out(colour, 0)})
		t.links.new(t.out(emission, 0), t.nodes["Material Output"].inputs["Surface"])
	else:
		bsdf = t.nodes["Principled BSDF"]
		colour = t.node("ShaderNodeMix", {"A": (0.85, 0.83, 0.8, 1), "B": (0.02, 0.02, 0.02, 1), "Factor": x},
			data_type="RGBA")
		t.links.new(t.out(colour, "Result"), _sock(bsdf.inputs, "Base Color"))
		bsdf.inputs["Roughness"].default_value = 0.8
	return material


class Cat:
	"""The built cat: its objects, and looks to switch between for the colour and mask passes."""

	def __init__(self, style):
		self.body = _body()
		_fur_fields(self.body, style)
		self.body.data.materials.append(_skin_material())
		self.fur = _fur(self.body, _fur_material(), style)
		self.eyes = _eyes()
		self.nose = _nose()
		# the body and what moves rigidly with it; the fur is the body's child
		self.parts = [self.body, self.nose, *self.eyes]
		self.subjects = self.parts + [self.fur]
		black = bpy.data.materials.new("Unmasked")
		black.use_nodes = True
		black.node_tree.nodes.clear()
		t = _Tree(black.node_tree)
		t.links.new(t.out(t.node("ShaderNodeEmission", {"Color": (0, 0, 0, 1)}), 0),
			t.node("ShaderNodeOutputMaterial").inputs["Surface"])
		self._looks = {"colour": {self.fur: self.fur.data.materials[0], self.body: self.body.data.materials[0],
			self.nose: self.nose.data.materials[0], **{eye: eye.data.materials[0] for eye in self.eyes}}}
		for name, pattern in PATTERNS.items():
			self._looks[name] = {self.fur: _mask_material(f"FurMask.{name}", pattern, "root_rest"),
				self.body: _mask_material(f"SkinMask.{name}", pattern, "rest_position"), self.nose: black,
				**{eye: black for eye in self.eyes}}
		self._drawn_eyes = {shape: {"colour": _drawn_eye_material(f"Eye.{shape}", False, shape),
			"mask": _drawn_eye_material(f"EyeMask.{shape}", True, shape)} for shape in ("x", "closed")}
		self.eye_state = "open"
		self._look = "colour"

	def add_props(self, objects):
		"""Things rendered with the cat but never tinted, like the worms' box: their own materials in colour, black
		(no coat) in the masks."""
		black = self._looks["tabby"][self.nose]
		for obj in objects:
			self._looks["colour"][obj] = obj.data.materials[0]
			for name in PATTERNS:
				self._looks[name][obj] = black
		self.subjects += objects

	def look(self, name):
		self._look = name
		for obj, material in self._looks[name].items():
			obj.data.materials[0] = material
		if self.eye_state != "open":
			for eye in self.eyes:
				eye.data.materials[0] = self._drawn_eyes[self.eye_state]["colour" if name == "colour" else "mask"]

	def look_black(self):
		"""Everything black (no coat), for another cat's mask pass in the same picture."""
		black = self._looks["tabby"][self.nose]
		for obj in self._looks["colour"]:
			obj.data.materials[0] = black

	def set_eyes(self, state):
		""""open", or drawn on eyes flattened into their sockets: "x" knocked out or "closed" asleep."""
		self.eye_state = state
		for eye in self.eyes:
			eye.scale = (1, 1 if state == "open" else 0.35, 1)
		self.look(self._look)

	def knock_out(self, out):
		self.set_eyes("x" if out else "open")


def build(style="shorthair", density=None):
	"""A cat in a fur style; density overrides the style's, for quick test renders."""
	style = dict(STYLES[style])
	if density is not None:
		style["density"] = density
	return Cat(style)

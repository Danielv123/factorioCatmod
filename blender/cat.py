# A cat built in code: a metaball body with mesh ears for soft cartoon proportions, glossy eyes, a nose, and procedural
# fur from geometry nodes. The cat stands at the origin facing +Y (north), at the size of a scale 1 sprite.
#
# The fur is a separate Curves object whose geometry nodes read the posed body (Cycles here doesn't render curves made by
# a mesh object's nodes). Its roots are placed on the rest pose ("rest_position") and moved to the posed body by
# sampling it, so a strand stays on the same spot of skin from frame to frame instead of being redistributed.
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
TAIL = [Vector(p) for p in ((0, -0.56, 0.66), (0, -0.78, 0.76), (0, -0.9, 0.98), (0, -0.9, 1.22), (0, -0.8, 1.4),
	(0, -0.66, 1.44))]
TAIL_RADII = [0.1, 0.095, 0.09, 0.085, 0.08, 0.06]
# each ear: its base on the head, tilted outward and a little back
EARS = [Matrix.Translation(HEAD + Vector((side * 0.25, -0.06, 0.31))) @ Matrix.Rotation(math.radians(-side * 24), 4, "Y")
	@ Matrix.Rotation(math.radians(-10), 4, "X") @ Matrix.Rotation(math.radians(side * 14), 4, "Z") for side in (-1, 1)]

COATS = {
	"orange-tabby": {"fur": (0.8, 0.17, 0.012), "stripe": (0.4, 0.055, 0.008), "stripes": 1.0, "white": 1.0,
		"skin": (0.8, 0.4, 0.12), "iris": ((0.45, 0.75, 0.15), (0.95, 0.75, 0.2))},
	"grey-tabby": {"fur": (0.42, 0.42, 0.44), "stripe": (0.1, 0.1, 0.11), "stripes": 1.0, "white": 1.0,
		"skin": (0.3, 0.3, 0.3), "iris": ((0.2, 0.6, 0.3), (0.8, 0.85, 0.3))},
	"tuxedo": {"fur": (0.04, 0.04, 0.045), "stripe": (0.04, 0.04, 0.045), "stripes": 0.0, "white": 1.0,
		"skin": (0.05, 0.05, 0.05), "iris": ((0.85, 0.65, 0.1), (0.95, 0.85, 0.3))},
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
	ball(TAIL[-1], 0.065)
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


def _fur_fields(body):
	"""Per vertex fur length, comb direction and bare pink skin, from where on the cat the vertex is."""
	mesh = body.data
	length = mesh.attributes.new("fur_len", "FLOAT", "POINT")
	comb = mesh.attributes.new("comb", "FLOAT_VECTOR", "POINT")
	pink = mesh.attributes.new("pink", "FLOAT", "POINT")
	ears = [(m.inverted(), m.to_3x3() @ Vector((0, 1, 0))) for m in EARS]
	for v in mesh.vertices:
		p = v.co
		n = v.normal
		fur = 0.065
		direction = Vector((0, -1, -0.35))
		bare = 0.0
		# legs and paws: short, combed down
		leg = 1 - _smoothstep(0.22, 0.4, p.z)
		fur = fur * (1 - leg) + 0.035 * leg
		direction = direction.lerp(Vector((0, -0.15, -1)), leg)
		paw = 1 - _smoothstep(0.07, 0.13, p.z)
		fur = fur * (1 - paw) + 0.02 * paw
		# a fluffy chest ruff, combed down
		ruff = 1 - _smoothstep(0.12, 0.32, (p - Vector((0, 0.42, 0.62))).length)
		fur = max(fur, 0.11 * ruff * _smoothstep(-0.2, 0.4, n.y))
		direction = direction.lerp(Vector((0, 0.25, -1)), ruff)
		# the head: short on the face, fluffy cheeks combed outwards
		head = 1 - _smoothstep(HEAD_RADIUS - 0.04, HEAD_RADIUS + 0.08, (p - HEAD).length)
		fur = fur * (1 - head) + 0.04 * head
		direction = direction.lerp(Vector((0, -1, 0.2)), head)
		face = head * _smoothstep(0.1, 0.5, n.y) * _smoothstep(HEAD.y + 0.1, HEAD.y + 0.3, p.y)
		fur = fur * (1 - face) + 0.016 * face
		direction = direction.lerp((p - MUZZLE).normalized(), face)
		for side in (-1, 1):
			cheek = 1 - _smoothstep(0.08, 0.2, (p - (HEAD + Vector((side * 0.34, 0.12, -0.15)))).length)
			fur = max(fur, 0.09 * cheek)
			direction = direction.lerp(Vector((side, -0.4, -0.35)), cheek)
		# the ears: short fur behind, bare and pink in front
		for inverse, forward in ears:
			local = inverse @ p
			if local.z > 0.0 and abs(local.x) < 0.24 and abs(local.y) < 0.14:
				fur = 0.014
				direction = Vector((0, 0, 1))
				inner = _smoothstep(-0.2, 0.3, n.dot(forward)) * (1 - _smoothstep(0.1, 0.15, abs(local.x)
					+ 0.4 * max(0, 0.12 - local.z)))
				bare = max(bare, inner)
				fur *= 1 - inner
		# the tail: long, combed towards the tip
		segment = min(range(len(TAIL) - 1), key=lambda i: (p - (TAIL[i] + TAIL[i + 1]) / 2).length)
		if (p - (TAIL[segment] + TAIL[segment + 1]) / 2).length < 0.22 and p.y < -0.5:
			fur = 0.12
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


def _fur(body, fur_material, density):
	tree = bpy.data.node_groups.new("CatFur", "GeometryNodeTree")
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

	position = t.out(t.node("GeometryNodeInputPosition"), "Position")
	normal = t.out(t.node("GeometryNodeInputNormal"), "Normal")
	body_info = t.node("GeometryNodeObjectInfo", {"Object": body}, transform_space="RELATIVE")
	posed = store(t.out(body_info, "Geometry"), "def_pos", position)
	posed = store(posed, "def_nrm", normal)
	rest = t.out(t.node("GeometryNodeSetPosition", {"Geometry": posed, "Position": named("rest_position")}), "Geometry")

	has_fur = t.out(t.node("FunctionNodeCompare", {"A": named("fur_len", "FLOAT"), "B": 0.004},
		data_type="FLOAT", operation="GREATER_THAN"), "Result")
	distribute = t.node("GeometryNodeDistributePointsOnFaces", {"Mesh": rest, "Selection": has_fur,
		"Density": density, "Seed": 7}, distribute_method="RANDOM")
	points = t.out(distribute, "Points")

	def sample(value, data_type="FLOAT_VECTOR", at=None):
		n = t.node("GeometryNodeSampleNearestSurface", {"Mesh": rest, "Value": value}, data_type=data_type)
		if at is not None:
			t.set(n, "Sample Position", at)
		return t.out(n, "Value")

	root = sample(named("def_pos"))
	n = t.vmath("NORMALIZE", sample(named("def_nrm")))
	comb_rest = sample(named("comb"))
	ahead = sample(named("def_pos"), at=t.vmath("ADD", position, t.vmath("SCALE", comb_rest, scale=0.03)))
	comb = t.vmath("NORMALIZE", t.vmath("SUBTRACT", ahead, root))
	comb = t.vmath("NORMALIZE", t.vmath("SUBTRACT", comb, t.vmath("SCALE", n,
		scale=t.vmath("DOT_PRODUCT", comb, n))))
	random = t.out(t.node("FunctionNodeRandomValue", {"Min": 0.75, "Max": 1.2, "Seed": 3}, data_type="FLOAT"), 0)
	length = t.math("MULTIPLY", sample(named("fur_len", "FLOAT"), "FLOAT"), random)
	points = store(points, "root", root)
	points = store(points, "n", n)
	points = store(points, "t", comb)
	points = store(points, "len", length, "FLOAT")
	points = store(points, "root_rest", position)

	line = t.node("GeometryNodeCurvePrimitiveLine", {"Start": (0, 0, 0), "End": (0, 0, 1)})
	line = t.node("GeometryNodeResampleCurve", {"Curve": t.out(line, "Curve"), "Count": 6})
	instances = t.node("GeometryNodeInstanceOnPoints", {"Points": points, "Instance": t.out(line, "Curve")})
	curves = t.out(t.node("GeometryNodeRealizeInstances", {"Geometry": t.out(instances, "Instances")}), "Geometry")

	# each strand rises off the skin and lies down along the comb direction
	f = t.out(t.node("GeometryNodeSplineParameter"), "Factor")
	lift = t.math("MULTIPLY", t.math("MULTIPLY", f, t.math("MULTIPLY_ADD", f, -0.6, 1.0)), 0.32)
	along = t.math("MULTIPLY", f, t.math("MULTIPLY_ADD", f, 0.6, 0.4))
	strand = t.vmath("ADD", t.vmath("SCALE", named("n"), scale=lift), t.vmath("SCALE", named("t"), scale=along))
	strand = t.vmath("SCALE", strand, scale=named("len", "FLOAT"))
	# clumps: the tips lean towards the centre of their Voronoi cell, in rest space
	root_rest = named("root_rest")
	voronoi = t.node("ShaderNodeTexVoronoi", {"Vector": root_rest, "Scale": 36.0}, voronoi_dimensions="3D")
	clump = t.vmath("SCALE", t.vmath("SUBTRACT", t.out(voronoi, "Position"), root_rest),
		scale=t.math("MULTIPLY", t.math("POWER", f, 1.5), 0.75))
	noise = t.node("ShaderNodeTexNoise", {"Vector": t.vmath("SCALE", root_rest, scale=40.0), "Scale": 1.0,
		"Detail": 1.0}, noise_dimensions="3D")
	frizz = t.vmath("SCALE", t.vmath("SUBTRACT", t.out(noise, "Color"), (0.5, 0.5, 0.5)),
		scale=t.math("MULTIPLY", t.math("MULTIPLY", f, named("len", "FLOAT")), 0.4))
	tip = t.vmath("ADD", t.vmath("ADD", named("root"), strand), t.vmath("ADD", clump, frizz))
	curves = t.out(t.node("GeometryNodeSetPosition", {"Geometry": curves, "Position": tip}), "Geometry")
	radius = t.math("MULTIPLY", t.math("MULTIPLY_ADD", f, -0.85, 1.0), 0.0026)
	curves = t.out(t.node("GeometryNodeSetCurveRadius", {"Curve": curves, "Radius": radius}), "Curve")
	curves = t.out(t.node("GeometryNodeSetMaterial", {"Geometry": curves, "Material": fur_material}), "Geometry")
	t.links.new(curves, group_out.inputs[0])

	fur = bpy.data.objects.new("CatFur", bpy.data.hair_curves.new("CatFur"))
	bpy.context.scene.collection.objects.link(fur)
	fur.data.materials.append(fur_material)
	fur.modifiers.new("Fur", "NODES").node_group = tree
	return fur


def _coat_pattern(t, coat, p):
	"""Shader nodes for the coat at rest position p: returns (stripe, white) factors."""
	sep = t.node("ShaderNodeSeparateXYZ", {"Vector": p})
	x, y, z = t.out(sep, "X"), t.out(sep, "Y"), t.out(sep, "Z")
	wave = t.node("ShaderNodeTexWave", {"Vector": p, "Scale": 2.1, "Distortion": 5.0, "Detail": 2.0,
		"Detail Scale": 1.5}, wave_type="BANDS", bands_direction="Y")
	stripe = t.math("MULTIPLY", t.map_range(t.out(wave, "Fac"), 0.62, 0.85), coat["stripes"])
	middle = t.map_range(t.math("ABSOLUTE", x), 0.2, 0.1)
	belly = t.math("MULTIPLY", t.map_range(z, 0.42, 0.32), middle)
	chest = t.math("MULTIPLY", t.math("MULTIPLY", t.map_range(y, 0.3, 0.45), t.map_range(z, 0.88, 0.75)), middle)
	muzzle = t.map_range(t.vmath("DISTANCE", p, tuple(MUZZLE + Vector((0, 0, -0.03)))), 0.25, 0.18)
	paws = t.map_range(z, 0.14, 0.09)
	white = t.math("MAXIMUM", t.math("MAXIMUM", belly, chest), t.math("MAXIMUM", muzzle, paws))
	white = t.math("MULTIPLY", white, coat["white"])
	return stripe, white


def _fur_material(coat):
	material = bpy.data.materials.new("CatFur")
	material.use_nodes = True
	t = _Tree(material.node_tree)
	t.nodes.clear()
	p = t.out(t.node("ShaderNodeAttribute", attribute_name="root_rest", attribute_type="GEOMETRY"), "Vector")
	stripe, white = _coat_pattern(t, coat, p)
	# direct colours rather than melanin, for the saturated coats of an animated film
	colour = t.node("ShaderNodeMix", {"A": (*coat["fur"], 1), "B": (*coat["stripe"], 1), "Factor": stripe},
		data_type="RGBA")
	colour = t.node("ShaderNodeMix", {"A": t.out(colour, "Result"), "B": (0.95, 0.93, 0.9, 1), "Factor": white},
		data_type="RGBA")
	hair = t.node("ShaderNodeBsdfHairPrincipled", {"Color": t.out(colour, "Result"), "Roughness": 0.4,
		"Radial Roughness": 0.7, "Coat": 0.08, "Random Roughness": 0.2}, parametrization="COLOR")
	output = t.node("ShaderNodeOutputMaterial")
	t.links.new(t.out(hair, 0), output.inputs["Surface"])
	return material


def _skin_material(coat):
	material = bpy.data.materials.new("CatSkin")
	material.use_nodes = True
	t = _Tree(material.node_tree)
	p = t.out(t.node("ShaderNodeAttribute", attribute_name="rest_position", attribute_type="GEOMETRY"), "Vector")
	_, white = _coat_pattern(t, coat, p)
	base = t.node("ShaderNodeMix", {"A": (*coat["skin"], 1), "B": (0.8, 0.77, 0.72, 1), "Factor": white},
		data_type="RGBA")
	pink = t.out(t.node("ShaderNodeAttribute", attribute_name="pink", attribute_type="GEOMETRY"), "Fac")
	base = t.node("ShaderNodeMix", {"A": t.out(base, "Result"), "B": (0.95, 0.55, 0.55, 1), "Factor": pink},
		data_type="RGBA")
	bsdf = t.nodes["Principled BSDF"]
	t.links.new(t.out(base, "Result"), _sock(bsdf.inputs, "Base Color"))
	bsdf.inputs["Roughness"].default_value = 0.7
	_sock(bsdf.inputs, "Subsurface Weight").default_value = 0.15
	return material


def _eye_material(coat):
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
	inner, outer = coat["iris"]
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


def _eyes(coat):
	material = _eye_material(coat)
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


def build(coat_name="orange-tabby", density=60000):
	"""Returns the body, the parts that move with it (body included) and the fur, which follows it on its own."""
	coat = COATS[coat_name]
	body = _body()
	_fur_fields(body)
	body.data.materials.append(_skin_material(coat))
	fur = _fur(body, _fur_material(coat), density)
	eyes = _eyes(coat)
	return body, [body, _nose(), *eyes], fur, eyes

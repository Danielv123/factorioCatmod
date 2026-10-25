# The render scene: an orthographic camera looking north at 45 degrees as Factorio's sprites are rendered, a sun from
# the west at 45 degrees (vanilla shadows fall about as far east as the body is high), and a ground plane that only
# bounces light, or catches the shadow in the shadow pass. 1 Blender unit is 1 tile; a scale 1 sprite has 64 px per
# tile, as Factorio draws it at scale 0.5. The cat is drawn SIZE times larger than it is modelled, to stand as big as
# the vanilla enemy it replaces.
import math

import bpy

PX_PER_TILE = 64
SIZE = 1.4


def reset():
	bpy.ops.wm.read_factory_settings(use_empty=True)


def setup(width, height, samples=64):
	scene = bpy.context.scene
	scene.render.engine = "CYCLES"
	prefs = bpy.context.preferences.addons["cycles"].preferences
	prefs.compute_device_type = "OPTIX"
	prefs.get_devices()
	for device in prefs.devices:
		device.use = device.type == "OPTIX"
	scene.cycles.device = "GPU"
	scene.cycles.samples = samples
	scene.cycles.use_denoising = True
	scene.cycles.denoiser = "OPTIX"
	scene.cycles.max_bounces = 6
	scene.render.film_transparent = True
	# keep the scene on the GPU between renders, so a frame only updates what moved
	scene.render.use_persistent_data = True
	scene.render.resolution_x = width
	scene.render.resolution_y = height
	scene.render.resolution_percentage = 100
	scene.render.image_settings.file_format = "PNG"
	scene.render.image_settings.color_mode = "RGBA"
	scene.render.image_settings.color_depth = "8"
	scene.view_settings.view_transform = "Standard"
	scene.view_settings.look = "Medium High Contrast"
	scene.view_settings.exposure = -0.4

	camera = bpy.data.objects.new("Camera", bpy.data.cameras.new("Camera"))
	camera.data.type = "ORTHO"
	camera.data.sensor_fit = "HORIZONTAL"
	camera.data.ortho_scale = width / PX_PER_TILE / SIZE
	camera.data.clip_start = 0.1
	camera.data.clip_end = 100
	camera.location = (0, -20, 20)
	camera.rotation_euler = (math.radians(45), 0, 0)
	scene.collection.objects.link(camera)
	scene.camera = camera

	sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
	sun.data.energy = 4.0
	sun.data.angle = math.radians(4)
	sun.rotation_euler = (0, math.radians(-45), 0)
	scene.collection.objects.link(sun)

	world = bpy.data.worlds.new("World")
	world.use_nodes = True
	background = world.node_tree.nodes["Background"]
	background.inputs["Color"].default_value = (0.75, 0.82, 1.0, 1)
	background.inputs["Strength"].default_value = 0.45
	scene.world = world

	bpy.ops.mesh.primitive_plane_add(size=40)
	ground = bpy.context.object
	ground.name = "Ground"
	material = bpy.data.materials.new("Ground")
	material.diffuse_color = (0.35, 0.27, 0.18, 1)
	material.use_nodes = True
	material.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.5, 0.38, 0.24, 1)
	material.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 1
	ground.data.materials.append(material)
	ground.visible_camera = False
	return scene, ground


def set_pass(ground, subjects, shadow):
	"""The colour pass sees the subjects only; the shadow pass sees only their shadow on the ground."""
	ground.visible_camera = shadow
	ground.is_shadow_catcher = shadow
	for obj in subjects:
		obj.visible_camera = not shadow


def catchlight(eyes):
	"""A sun from just above and left of the camera that lights only the eyes, for a glint in them."""
	from mathutils import Vector

	collection = bpy.data.collections.new("CatchlightReceivers")
	for eye in eyes:
		collection.objects.link(eye)
	light = bpy.data.objects.new("Catchlight", bpy.data.lights.new("Catchlight", "SUN"))
	light.data.energy = 3.0
	light.data.angle = math.radians(6)
	travel = Vector((0.35, 0.65, -0.75)).normalized()
	light.rotation_euler = (-travel).to_track_quat("Z", "Y").to_euler()
	light.light_linking.receiver_collection = collection
	bpy.context.scene.collection.objects.link(light)
	return light


def _stale(pixels, mask):
	"""Whether a render shows an object left in the other pass's material, which persistent data now and then does:
	the colour pass draws a white cat, so a large near-black patch is a mask material; the mask passes emit no blue,
	so blue is the colour material."""
	opaque = pixels[..., 3] > 0.8
	if mask:
		return int((opaque & (pixels[..., 2] > 0.05)).sum()) > 300
	return int((opaque & (pixels[..., :3].max(axis=2) < 0.05)).sum()) > 300


def render_layers(scene, ground, cat, patterns, path):
	"""Renders the current pose: the colour, the shadow, and each pattern set's masks (coat in red, markings in green,
	unlit and untouched by colour management). Returns them as arrays by name. A pass that comes out stale is
	rendered again without persistent data."""
	import sheet

	def render(mask=False):
		scene.render.filepath = path
		bpy.ops.render.render(write_still=True)
		pixels = sheet.load(path)
		if _stale(pixels, mask):
			print("stale render, again without persistent data")
			scene.render.use_persistent_data = False
			bpy.ops.render.render(write_still=True)
			scene.render.use_persistent_data = True
			pixels = sheet.load(path)
		return pixels

	layers = {}
	cat.look("colour")
	set_pass(ground, cat.subjects, False)
	layers["colour"] = render()
	set_pass(ground, cat.subjects, True)
	scene.render.filepath = path
	bpy.ops.render.render(write_still=True)
	layers["shadow"] = sheet.load(path)
	settings = (scene.view_settings.view_transform, scene.view_settings.look, scene.cycles.samples,
		scene.cycles.use_denoising)
	set_pass(ground, cat.subjects, False)
	scene.view_settings.view_transform = "Raw"
	scene.cycles.samples = 32
	scene.cycles.use_denoising = False
	for pattern in patterns:
		cat.look(pattern)
		layers[pattern] = render(mask=True)
	(scene.view_settings.view_transform, scene.view_settings.look, scene.cycles.samples,
		scene.cycles.use_denoising) = settings
	cat.look("colour")
	return layers

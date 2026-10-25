# Renders the hairball the spitters and worms cough up: a lumpy wad of mottled fur, tumbling over the 15 frames a
# stream particle loops through, and its silhouette for the shadow. Packs into graphics/cat/hairball/.
#   blender -b --factory-startup -P hairball.py
import math
import os
import random
import sys

import bpy
from mathutils import Euler, Vector

HERE = os.path.dirname(__file__)
sys.path.insert(0, HERE)
import cat as cat_module  # noqa: E402
import scene  # noqa: E402
import sheet  # noqa: E402

FRAMES = 15
SIZE = 160

scene.reset()
sc, ground = scene.setup(SIZE, SIZE, samples=64)
ground.hide_render = True

bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=0.1)
ball = bpy.context.object
ball.name = "Hairball"
# a lumpy, slightly long wad rather than a ball
random.seed(3)
lumps = [(Vector((random.uniform(-1, 1), random.uniform(-1, 1), random.uniform(-1, 1))).normalized(),
	random.uniform(0.1, 0.25)) for _ in range(9)]
for v in ball.data.vertices:
	n = v.co.normalized()
	bulge = sum(height * max(0.0, n.dot(direction)) ** 4 for direction, height in lumps)
	v.co = Vector((v.co.x * 1.3, v.co.y * 0.9, v.co.z * 0.9)) * (1 + bulge)
for polygon in ball.data.polygons:
	polygon.use_smooth = True
ball.add_rest_position_attribute = True

# messy fur: every strand combed its own way
length = ball.data.attributes.new("fur_len", "FLOAT", "POINT")
comb = ball.data.attributes.new("comb", "FLOAT_VECTOR", "POINT")
for v in ball.data.vertices:
	length.data[v.index].value = random.uniform(0.05, 0.1)
	comb.data[v.index].vector = v.normal.cross(Vector((random.uniform(-1, 1), random.uniform(-1, 1), 1))).normalized()

material = bpy.data.materials.new("Hairball")
material.use_nodes = True
t = cat_module._Tree(material.node_tree)
t.nodes.clear()
p = t.out(t.node("ShaderNodeAttribute", attribute_name="root_rest", attribute_type="GEOMETRY"), "Vector")
noise = t.node("ShaderNodeTexNoise", {"Vector": p, "Scale": 14.0, "Detail": 2.0})
ramp = t.node("ShaderNodeValToRGB", {"Fac": t.out(noise, "Fac")})
ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[0].color = 0.35, (0.14, 0.09, 0.06, 1)
ramp.color_ramp.elements[1].position, ramp.color_ramp.elements[1].color = 0.65, (0.66, 0.52, 0.38, 1)
middle = ramp.color_ramp.elements.new(0.5)
middle.color = (0.36, 0.25, 0.17, 1)
hair = t.node("ShaderNodeBsdfHairPrincipled", {"Color": t.out(ramp, "Color"), "Roughness": 0.35,
	"Radial Roughness": 0.6, "Coat": 0.2}, parametrization="COLOR")
t.links.new(t.out(hair, 0), t.node("ShaderNodeOutputMaterial").inputs["Surface"])
skin = bpy.data.materials.new("HairballSkin")
skin.diffuse_color = (0.4, 0.3, 0.22, 1)
ball.data.materials.append(skin)

style = dict(cat_module.STYLES["longhair"])
style.update({"density": 200000, "lift": 0.75, "clump": 0.5, "frizz": 1.5, "radius": 0.0024})
fur = cat_module._fur(ball, material, style)

frames = []
tmp = os.path.join(bpy.app.tempdir, "hairball.png")
for frame in range(FRAMES):
	ball.rotation_euler = Euler((2 * math.pi * frame / FRAMES, math.pi * frame / FRAMES, 0.3), "XYZ")
	sc.render.filepath = tmp
	bpy.ops.render.render(write_still=True)
	frames.append(sheet.load(tmp))
out_dir = os.path.join(HERE, "..", "graphics", "cat", "hairball")
sheet.pack(frames, out_dir, "hairball")
sheet.pack(frames, out_dir, "hairball-shadow", "shadow")
print("packed hairball to", out_dir)

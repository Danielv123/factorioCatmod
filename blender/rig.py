# The cat's skeleton. Bones lie in the body's YZ plane (legs offset in X) with no roll, so every bone pitches about its
# local X axis and swings sideways about its local Z axis. Poses are set per frame by the animations in anim.py.
import bpy
from mathutils import Vector

import cat


def _bones():
	"""(name, head, tail, parent) for each bone."""
	bones = [
		("root", (0, 0, 0), (0, 0.3, 0), None),
		("hips", (0, -0.42, 0.58), (0, -0.08, 0.56), "root"),
		("chest", (0, -0.08, 0.56), (0, 0.26, 0.6), "hips"),
		("neck", (0, 0.26, 0.62), (0, 0.48, 0.84), "chest"),
		("head", (0, 0.48, 0.84), (0, 0.6, 1.4), "neck"),
	]
	# the tail along its curve in five bones
	points = [cat.TAIL[round(i * (len(cat.TAIL) - 1) / 5)] for i in range(6)]
	parent = "hips"
	for i in range(5):
		bones.append((f"tail{i}", tuple(points[i]), tuple(points[i + 1]), parent))
		parent = f"tail{i}"
	for side, name in ((-1, "L"), (1, "R")):
		x = side * 0.15
		bones += [
			(f"front_upper.{name}", (x, 0.27, 0.5), (x * 1.05, 0.3, 0.2), "chest"),
			(f"front_lower.{name}", (x * 1.05, 0.3, 0.2), (x * 1.08, 0.32, 0.07), f"front_upper.{name}"),
			(f"front_paw.{name}", (x * 1.08, 0.32, 0.07), (x * 1.08, 0.46, 0.05), f"front_lower.{name}"),
			(f"thigh.{name}", (x * 1.1, -0.42, 0.56), (x * 1.15, -0.32, 0.3), "hips"),
			(f"shin.{name}", (x * 1.15, -0.32, 0.3), (x * 1.15, -0.48, 0.14), f"thigh.{name}"),
			(f"hock.{name}", (x * 1.15, -0.48, 0.14), (x * 1.12, -0.42, 0.07), f"shin.{name}"),
			(f"hind_paw.{name}", (x * 1.12, -0.42, 0.07), (x * 1.12, -0.29, 0.05), f"hock.{name}"),
		]
	return bones


def build(body, rigid_parts):
	"""An armature deforming the body; rigid parts (eyes, nose) ride on the head bone."""
	armature = bpy.data.objects.new("CatRig", bpy.data.armatures.new("CatRig"))
	bpy.context.scene.collection.objects.link(armature)
	bpy.context.view_layer.objects.active = armature
	bpy.ops.object.mode_set(mode="EDIT")
	edit = armature.data.edit_bones
	for name, head, tail, parent in _bones():
		bone = edit.new(name)
		bone.head, bone.tail = Vector(head), Vector(tail)
		bone.roll = 0
		if parent:
			bone.parent = edit[parent]
			bone.use_connect = False
	bpy.ops.object.mode_set(mode="OBJECT")
	armature.data.bones["root"].use_deform = False
	# squash and stretch scales the body; the head, and the eyes and nose on it, keep their shape
	armature.data.bones["head"].inherit_scale = "NONE"

	# automatic (heat) weights
	for obj in bpy.context.view_layer.objects:
		obj.select_set(False)
	body.select_set(True)
	armature.select_set(True)
	bpy.context.view_layer.objects.active = armature
	bpy.ops.object.parent_set(type="ARMATURE_AUTO")
	unweighted = sum(1 for v in body.data.vertices if not any(g.weight > 0 for g in v.groups))
	if unweighted:
		print(f"rig: {unweighted} of {len(body.data.vertices)} vertices have no weights")

	for part in rigid_parts:
		world = part.matrix_world.copy()
		part.parent = armature
		part.parent_type = "BONE"
		part.parent_bone = "head"
		part.matrix_world = world
	for pose_bone in armature.pose.bones:
		pose_bone.rotation_mode = "XYZ"
	return armature

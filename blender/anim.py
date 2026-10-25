# Poses for the cat's animations, as functions of the phase (0 to 1) through the cycle. Angles are degrees; leg and
# spine bones pitch about their local X axis (positive swings a leg's paw forward). The tail is aimed instead: each bone
# points in a direction given relative to the body as a whole (the root bone), as an elevation above straight back and
# a sideways swing, so the spine's flexing doesn't swing it about.
import math

import bpy
from mathutils import Vector

TAU = 2 * math.pi
TAIL_BONES = 5


def _set(arm, bone, x=0.0, y=0.0, z=0.0):
	arm.pose.bones[bone].rotation_euler = (math.radians(x), math.radians(y), math.radians(z))


def rest(arm):
	for bone in arm.pose.bones:
		bone.rotation_mode = "XYZ"
		bone.rotation_euler = (0, 0, 0)
		bone.location = (0, 0, 0)
		bone.scale = (1, 1, 1)


def _bump(phase, start, end):
	"""0 outside start-end, rising smoothly to 1 in the middle."""
	if phase <= start or phase >= end:
		return 0.0
	return math.sin(math.pi * (phase - start) / (end - start))


def _ease(phase, start, end):
	"""0 before start, easing to 1 at end."""
	t = min(max((phase - start) / (end - start), 0.0), 1.0)
	return t * t * (3 - 2 * t)


def _aim_tail(arm, elevations, swings):
	"""Points tail bone i at elevations[i] degrees above straight back and swings[i] degrees to the side, in the
	frame of the posed root bone. Call after the rest of the pose is set."""
	bpy.context.view_layer.update()
	root = arm.pose.bones["root"]
	body_turn = root.matrix.to_3x3() @ root.bone.matrix_local.to_3x3().inverted()
	parent = arm.pose.bones["hips"].matrix.copy()
	for i in range(TAIL_BONES):
		pose_bone = arm.pose.bones[f"tail{i}"]
		bone = pose_bone.bone
		unposed = parent @ (bone.parent.matrix_local.inverted() @ bone.matrix_local)
		turn = unposed.to_3x3().normalized()
		e, s = math.radians(elevations[i]), math.radians(swings[i])
		target = body_turn @ Vector((math.sin(s) * math.cos(e), -math.cos(s) * math.cos(e), math.sin(e)))
		world = turn.col[1].rotation_difference(target.normalized())
		local = (turn.inverted() @ world.to_matrix() @ turn).to_quaternion()
		pose_bone.rotation_mode = "QUATERNION"
		pose_bone.rotation_quaternion = local
		parent = unposed @ local.to_matrix().to_4x4()


# The tail through one stride of Muybridge's galloping cat (plate 720, frames 13-23, traced from the photographs):
# each row the elevations, degrees above straight back, of five equal lengths of tail from base to tip, at its phase
# (0 is the gathered frame 19, which matches frame 7). A wave runs down the tail: the base rises as the cat pushes off
# while the tip hangs in a hook, then the base drops and the tip flicks up.
PLATE_720_TAIL = [
	(0.000, (9, -15, -27, -13, -10)),
	(0.083, (21, 3, -22, -39, -34)),
	(0.167, (25, 12, -4, -36, -61)),
	(0.250, (27, 23, 5, -14, -61)),
	(0.333, (41, 25, 15, -2, -29)),
	(0.500, (34, 31, 27, 27, 29)),
	(0.583, (33, 32, 32, 30, 7)),
	(0.667, (19, 20, 25, 36, 20)),
	(0.750, (6, 3, 10, 30, 43)),
	(0.833, (2, -11, -3, 11, 36)),
	(0.917, (10, -10, -20, -12, -6)),
]


def _plate_tail(phase):
	"""The traced tail elevations at any phase, by a smooth cyclic (Catmull-Rom) curve through the photographs."""
	phase %= 1
	keys = PLATE_720_TAIL
	n = len(keys)
	i = max(k for k in range(n) if keys[k][0] <= phase)
	p0, p1, p2, p3 = (keys[(i + k) % n] for k in (-1, 0, 1, 2))
	t0, t1, t2, t3 = p0[0], p1[0], p2[0], p3[0]
	# unwrap the phases around the cycle's end
	if t0 > t1:
		t0 -= 1
	if t2 <= t1:
		t2 += 1
	if t3 <= t2:
		t3 += 1
	t = (phase - t1) / (t2 - t1)
	out = []
	for a0, a1, a2, a3 in zip(p0[1], p1[1], p2[1], p3[1]):
		m1 = (a2 - a0) / (t2 - t0) * (t2 - t1)
		m2 = (a3 - a1) / (t3 - t1) * (t2 - t1)
		out.append((2 * t ** 3 - 3 * t ** 2 + 1) * a1 + (t ** 3 - 2 * t ** 2 + t) * m1
			+ (-2 * t ** 3 + 3 * t ** 2) * a2 + (t ** 3 - t ** 2) * m2)
	return out


def _front_leg(arm, side, p):
	"""On the ground from 0.55 to 0.85, sweeping back with the paw flat; then folded up under the chest through the
	gathered flight, and reaching far forward through the stretched one."""
	p %= 1
	if 0.55 <= p < 0.85:
		t = (p - 0.55) / 0.3
		upper = 40 - 85 * t
		lower = -12 * math.sin(math.pi * t)
		paw = -(upper + lower)
	else:
		t = ((p - 0.85) % 1) / 0.7
		upper = -45 + 85 * _ease(t, 0.1, 0.85)
		lower = -115 * _bump(t, 0.0, 0.8)
		paw = -65 * _bump(t, 0.0, 0.75) + 15 * _bump(t, 0.7, 1.0)
	_set(arm, f"front_upper.{side}", upper)
	_set(arm, f"front_lower.{side}", lower)
	_set(arm, f"front_paw.{side}", paw)


def _hind_leg(arm, side, p):
	"""On the ground from 0 to 0.35, landing under the belly and pushing back to a straight leg; then trailing straight
	back through the stretched flight, and folding forward to land under the belly again."""
	p %= 1
	if p < 0.35:
		t = p / 0.35
		thigh = 32 - 72 * t
		shin = 18 * (1 - t)
		hock = -20 * (1 - t) + 30 * t
		paw = -(thigh + shin + hock) * (1 - _ease(t, 0.7, 1.0)) + 20 * _ease(t, 0.7, 1.0)
	else:
		t = (p - 0.35) / 0.65
		thigh = -40 + 72 * _ease(t, 0.15, 0.95)
		fold = _bump(t, 0.12, 0.92)
		shin = 45 * fold
		hock = 30 * (1 - _ease(t, 0.0, 0.2)) - 75 * fold
		paw = 20 * (1 - _ease(t, 0.0, 0.2)) + 40 * fold
	_set(arm, f"thigh.{side}", thigh)
	_set(arm, f"shin.{side}", shin)
	_set(arm, f"hock.{side}", hock)
	_set(arm, f"hind_paw.{side}", paw)


def run(arm, phase, cat=None, direction=0):
	"""A rotary gallop after Muybridge's galloping cat (Animal Locomotion, plate 720). At 0 the cat is gathered: the
	spine arched, hind paws landing under the belly, front paws tucked. The hind legs push it into a stretched flight
	(about 0.47), the front paws land and push it into a short gathered flight while the hind legs swing forward. The
	head stays level. The tail moves as the photographed cat's did, swaying from side to side as well."""
	rest(arm)
	_hind_leg(arm, "L", phase)
	_hind_leg(arm, "R", phase - 0.05)
	_front_leg(arm, "R", phase)
	_front_leg(arm, "L", phase - 0.05)
	flex = math.cos(TAU * phase)
	pitch = 4 * math.sin(TAU * (phase - 0.05))
	root = arm.pose.bones["root"]
	root.location = (0, 0, 0.14 * _bump(phase, 0.3, 0.66) + 0.05 * _bump((phase + 0.15) % 1, 0.0, 0.2))
	# squashed when gathered, stretched long in the air (the head keeps its shape, see rig.py)
	root.scale = (1 + 0.02 * flex, 1 - 0.08 * flex, 1 + 0.06 * flex)
	_set(arm, "root", pitch)
	# arched hard when gathered, only a little hollow when stretched; the chest bends twice as far as the hips, the other
	# way, so the back bows while the line from rump to shoulders stays level
	hips = 14 * flex if flex > 0 else 5 * flex
	chest = -2 * hips
	_set(arm, "hips", hips)
	_set(arm, "chest", chest)
	# the neck takes up most of the pitch the chest ends at (root, hips and chest), keeping the head level
	_set(arm, "neck", -0.8 * (pitch + hips + chest))
	_set(arm, "head", -0.3 * pitch + 2 * math.sin(TAU * phase))
	# the sway grows down the tail and lags behind the base, like the rise and fall does
	_aim_tail(arm, _plate_tail(phase), [(5 + 4 * i) * math.sin(TAU * (phase - 0.12 * i)) for i in range(TAIL_BONES)])


def attack(arm, phase, cat=None, direction=0):
	"""A playful pounce: a crouch with a wiggle of the bottom and a flicking tail tip, a hop forward with both paws
	up and the tail out straight for balance, and a swipe."""
	rest(arm)
	crouch = _bump(phase, 0.0, 0.35)
	pounce = _bump(phase, 0.25, 0.8)
	swipe = _bump(phase, 0.5, 0.85)
	arm.pose.bones["root"].location = (0, 0.32 * pounce, -0.08 * crouch + 0.16 * pounce)
	_set(arm, "hips", 10 * crouch - 6 * pounce, 0, 10 * math.sin(4 * TAU * phase) * crouch)
	_set(arm, "chest", -12 * crouch + 10 * pounce)
	_set(arm, "neck", 8 * crouch - 6 * pounce)
	_set(arm, "head", 6 * crouch - 8 * pounce, 0, 6 * swipe)
	for side, extra in (("L", 0.0), ("R", 1.0)):
		_set(arm, f"front_upper.{side}", -15 * crouch + 100 * pounce - 70 * swipe * extra)
		_set(arm, f"front_lower.{side}", -20 * crouch - 45 * pounce + 40 * swipe * extra)
		_set(arm, f"front_paw.{side}", -35 * pounce + 25 * swipe * extra)
		_set(arm, f"thigh.{side}", -12 * crouch - 28 * pounce)
		_set(arm, f"shin.{side}", 20 * crouch - 10 * pounce)
		_set(arm, f"hock.{side}", -25 * crouch + 25 * pounce)
	curl = (0, 3, 8, 14, 22)
	_aim_tail(arm, [12 - 8 * crouch + 8 * pounce + curl[i] * (1 - 0.5 * pounce) for i in range(TAIL_BONES)],
		[18 * math.sin(4 * TAU * phase) * crouch * i / (TAIL_BONES - 1) for i in range(TAIL_BONES)])


def die(arm, phase, cat=None, direction=0):
	"""A surprised hop, then a flop onto the side with the legs stuck out stiff and X eyes; the corpse keeps the last
	frame. The cat rolls towards the camera (south), so its belly, paws and face show whichever way it faces."""
	rest(arm)
	hop = _bump(phase, 0.0, 0.3)
	roll = _ease(phase, 0.2, 0.6)
	settle = _bump(phase, 0.6, 0.8)
	# facing east-ish its right side faces the camera: it lies down on its left, and the other way round
	lie = -1 if math.sin(TAU * direction / 16) >= 0 else 1
	angle = math.radians(90 * roll) * lie
	# rolled about the body's length, the middle of the body comes to rest on its side above the ground
	centre = 0.55
	height = centre - 0.24 * roll + 0.12 * hop + 0.03 * settle
	arm.pose.bones["root"].location = (-centre * math.sin(angle) - 0.1 * roll * lie, 0, height - centre * math.cos(angle))
	arm.pose.bones["root"].rotation_euler = (0, angle, 0)
	stiff = _ease(phase, 0.15, 0.4)
	for side in ("L", "R"):
		_set(arm, f"front_upper.{side}", 25 * stiff)
		_set(arm, f"front_lower.{side}", 10 * stiff)
		_set(arm, f"front_paw.{side}", 15 * stiff)
		_set(arm, f"thigh.{side}", -25 * stiff)
		_set(arm, f"shin.{side}", -10 * stiff)
		_set(arm, f"hock.{side}", 20 * stiff)
	_set(arm, "neck", -10 * roll)
	_set(arm, "head", 8 * hop - 10 * roll)
	# the tail shoots up in surprise, then lies out behind with a little curl at the tip
	curl = (0, 2, 5, 10, 16)
	_aim_tail(arm, [25 * (1 - roll) + 40 * hop + curl[i] * (1 - 0.4 * roll) for i in range(TAIL_BONES)],
		[0] * TAIL_BONES)
	if cat is not None:
		cat.knock_out(phase >= 0.45)


ANIMATIONS = {
	"stand": {"frames": 1, "pose": lambda arm, phase, cat=None, direction=0: rest(arm)},
	"run": {"frames": 16, "pose": run},
	"attack": {"frames": 11, "pose": attack},
	"die": {"frames": 17, "pose": die},
}

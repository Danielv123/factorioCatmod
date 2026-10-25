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
	arm.scale = (1, 1, 1)
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


def _direction(elevation, swing):
	e, s = math.radians(elevation), math.radians(swing)
	return Vector((math.sin(s) * math.cos(e), -math.cos(s) * math.cos(e), math.sin(e)))


def _aim_tail(arm, elevations, swings, ground=None, settle=0.0):
	"""Points tail bone i at elevations[i] degrees above straight back and swings[i] degrees to the side, in the
	frame of the posed root bone. ground gives (elevation, swing) per bone in the armature's own frame, where the
	ground is level whatever the body does, and settle blends towards those. Call after the rest of the pose is set."""
	bpy.context.view_layer.update()
	root = arm.pose.bones["root"]
	body_turn = root.matrix.to_3x3() @ root.bone.matrix_local.to_3x3().inverted()
	parent = arm.pose.bones["hips"].matrix.copy()
	for i in range(TAIL_BONES):
		pose_bone = arm.pose.bones[f"tail{i}"]
		bone = pose_bone.bone
		unposed = parent @ (bone.parent.matrix_local.inverted() @ bone.matrix_local)
		turn = unposed.to_3x3().normalized()
		target = body_turn @ _direction(elevations[i], swings[i])
		if ground is not None and settle > 0:
			target = target.lerp(_direction(*ground[i]), settle)
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
	# lifted a little: the photographed cat's tail is long and slim, ours short and fluffy on a rounder rump, and the
	# same dip reads as a droop on it. The sway grows down the tail and lags behind the base, like the rise and fall.
	_aim_tail(arm, [a + 12 for a in _plate_tail(phase)],
		[(5 + 4 * i) * math.sin(TAU * (phase - 0.12 * i)) for i in range(TAIL_BONES)])


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
	height = centre - 0.15 * roll + 0.12 * hop + 0.03 * settle
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
	# the big head turns up off the ground, so it rests on it rather than sinking in
	_set(arm, "neck", -10 * roll, 0, 21 * lie * roll)
	_set(arm, "head", 8 * hop - 10 * roll, 0, 8 * lie * roll)
	# the tail shoots up in surprise, stays stiff through the fall, then flops down onto the ground just after the
	# body lands: down from the rump, and curled round towards the belly (the side facing the camera), limp
	curl = (0, 2, 5, 10, 16)
	flop = _ease(phase, 0.5, 0.78)
	bounce = 0.12 * _bump(phase, 0.78, 0.92)
	ground = [(-45, 4), (-38, 14), (0, 34), (1, 60), (3, 88)]
	_aim_tail(arm, [25 * (1 - roll) + 40 * hop + curl[i] * (1 - 0.4 * roll) for i in range(TAIL_BONES)],
		[0] * TAIL_BONES, [(e, -lie * s) for e, s in ground], min(1.0, flop - bounce))
	if cat is not None:
		cat.knock_out(phase >= 0.45)


def _trot_leg(arm, front, side, p):
	"""On the ground for the first 0.55 of its cycle, sweeping back with the paw flat; then folded and carried
	forward."""
	p %= 1
	if p < 0.55:
		t = p / 0.55
		swing = 28 - 56 * t
		bend = 0.0
	else:
		t = (p - 0.55) / 0.45
		swing = -28 + 56 * _ease(t, 0.0, 1.0)
		bend = _bump(t, 0.0, 1.0)
	if front:
		_set(arm, f"front_upper.{side}", swing)
		_set(arm, f"front_lower.{side}", -70 * bend)
		_set(arm, f"front_paw.{side}", -(swing - 70 * bend) * (1 - bend) - 40 * bend)
	else:
		_set(arm, f"thigh.{side}", swing * 0.9)
		_set(arm, f"shin.{side}", 35 * bend)
		_set(arm, f"hock.{side}", -55 * bend)
		_set(arm, f"hind_paw.{side}", -swing * 0.9 * (1 - bend) + 35 * bend)


def trot(arm, phase, cat=None, direction=0):
	"""The spitters' gait: a dainty trot, the diagonal pairs of legs moving together, the body bobbing twice a stride
	and swaying a little side to side, and the plume of a tail held high, bobbing and swaying behind."""
	rest(arm)
	_trot_leg(arm, True, "L", phase)
	_trot_leg(arm, False, "R", phase)
	_trot_leg(arm, True, "R", phase + 0.5)
	_trot_leg(arm, False, "L", phase + 0.5)
	arm.pose.bones["root"].location = (0, 0, 0.03 * (0.5 - 0.5 * math.cos(2 * TAU * (phase - 0.1))))
	_set(arm, "hips", 0, 0, 5 * math.sin(TAU * phase))
	_set(arm, "chest", 0, 0, -4 * math.sin(TAU * phase))
	_set(arm, "neck", 0, 0, 2 * math.sin(TAU * phase))
	_set(arm, "head", 3 * math.cos(2 * TAU * phase))
	plume = (68, 76, 66, 50, 34)
	_aim_tail(arm, [plume[i] + 5 * math.sin(2 * TAU * (phase - 0.08 * i)) for i in range(TAIL_BONES)],
		[(6 + 5 * i) * math.sin(TAU * (phase - 0.15 * i)) for i in range(TAIL_BONES)])


def spit(arm, phase, cat=None, direction=0):
	"""The spitters' attack, coughing up a hairball, in vanilla's spitter frame order: a crouch (frames 1 to 6), the
	neck stretched out ready (7), then heaves building up to the hairball (8 to 14); in game the heaves rock back and
	forth between 7 and 14 while it spits."""
	rest(arm)
	crouch = _ease(phase, 0.0, 6 / 13)
	heave = _ease(phase, 6 / 13, 1.0)
	hack = math.sin(3 * TAU * phase) * heave * (1 - heave) * 4
	arm.pose.bones["root"].location = (0, 0.12 * heave, -0.11 * crouch)
	_set(arm, "hips", 10 * crouch + 16 * heave)
	_set(arm, "chest", -14 * crouch - 34 * heave + 5 * hack)
	_set(arm, "neck", -12 * crouch + 26 * heave)
	_set(arm, "head", 8 * crouch - 34 * heave + 6 * hack)
	for side in ("L", "R"):
		_set(arm, f"front_upper.{side}", 14 * crouch + 6 * heave)
		_set(arm, f"front_lower.{side}", -12 * crouch)
		_set(arm, f"front_paw.{side}", -2 * crouch - 6 * heave)
		_set(arm, f"thigh.{side}", -8 * crouch)
		_set(arm, f"shin.{side}", 18 * crouch)
		_set(arm, f"hock.{side}", -22 * crouch)
		_set(arm, f"hind_paw.{side}", 12 * crouch)
	_aim_tail(arm, [12 - 6 * crouch - 3 * i + 8 * hack * i / 4 for i in range(TAIL_BONES)],
		[10 * heave * math.sin(2 * TAU * phase) * i / (TAIL_BONES - 1) for i in range(TAIL_BONES)])


# The worms: a cat in a cardboard box (box.py), which stays put while the cat turns inside it.
SIT_PITCH = 55


def _sit(arm, emerge=1.0, pitch=SIT_PITCH, lean=0.0, look=0.0, tilt=0.0, nod=0.0):
	"""Sitting up in the box: the body pitched upright about the hips and moved over the box's middle, front paws on
	the rim, the head brought back level to look out, the tail standing up behind it inside the box. emerge 0 is
	squashed down out of sight with the ear tips poking out, 1 sat up with the chin over the rim, more stretches up
	tall; lean tips the body forward over the rim, look turns the head, tilt tilts it, nod drops it."""
	up = min(1.0, max(0.0, emerge))
	sitting = pitch
	p = math.radians(sitting - lean)
	root = arm.pose.bones["root"]
	root.rotation_euler = (p, 0, 0)
	# pitching about the feet swings the head back; this keeps the chest over the box's middle
	# hidden, it sits well back, so the head and eyes stay behind the front wall the camera sees (the rump, past the
	# back wall, is hidden behind the box)
	root.location = (0, 0.62 * math.sin(p) - 0.15 + 0.35 * lean / 40 - 0.02 * (1 - up),
		0.03 + 0.08 * (1 - up) + 0.2 * up + 0.1 * lean / 40)
	# squashed down into the box when hidden, a little stretched popping up past sitting: the whole cat, in the
	# world's up, so the hidden cat keeps to the box's footprint
	squash = 0.47 + 0.53 * up + 0.5 * max(0.0, emerge - 1)
	arm.scale = (1 - 0.25 * (1 - up), 1 - 0.25 * (1 - up), squash)
	_set(arm, "neck", -0.55 * (sitting - lean) + nod * 0.5)
	_set(arm, "head", -0.35 * (sitting - lean) + nod, 0, look)
	arm.pose.bones["head"].rotation_euler.y = math.radians(tilt)
	for side, sign in (("L", 1), ("R", -1)):
		_set(arm, f"front_upper.{side}", 70 - 0.5 * (sitting - lean), 0, 4 * sign)
		_set(arm, f"front_lower.{side}", -35)
		_set(arm, f"front_paw.{side}", -40)
		_set(arm, f"thigh.{side}", 60)
		_set(arm, f"shin.{side}", 40)
		_set(arm, f"hock.{side}", -70)
	_aim_tail(arm, [0] * TAIL_BONES, [0] * TAIL_BONES, [(78, 0), (84, 0), (80, 4), (64, 8), (40, 12)], 1.0)


def box_folded(arm, phase, cat=None, direction=0):
	"""Hidden in the closed box, only the ear tips poking up between the long flaps, which stir now and then; played
	forwards then backwards."""
	rest(arm)
	_sit(arm, emerge=0.0, look=8 * math.sin(TAU * phase))
	cat.box.open(0.0, wiggle=0.5 * _bump(phase, 0.3, 0.9))


def box_preparing(arm, phase, cat=None, direction=0):
	"""The flaps burst open and the cat pops up out of the box with a little overshoot, landing its paws on the rim.
	Folding plays it backwards."""
	rest(arm)
	flaps = _ease(phase, 0.05, 0.35)
	rise = _ease(phase, 0.2, 0.7)
	overshoot = 0.12 * _bump(phase, 0.55, 0.9)
	_sit(arm, emerge=rise + overshoot, look=0, tilt=10 * _bump(phase, 0.7, 1.0))
	cat.box.open(flaps, wiggle=0.6 * _bump(phase, 0.0, 0.12))


def box_prepared(arm, phase, cat=None, direction=0):
	"""Sat up in the box breathing and glancing about; played forwards then backwards."""
	rest(arm)
	_sit(arm, emerge=1.0 + 0.04 * math.sin(math.pi * phase), look=10 * math.sin(math.pi * phase), tilt=6 * phase,
		nod=-3 * math.sin(math.pi * phase))
	cat.box.open(1.0)


def box_alternative(arm, phase, cat=None, direction=0):
	"""Looks left, then right, with a curious head tilt each way, and back."""
	rest(arm)
	look = 38 * math.sin(TAU * phase)
	_sit(arm, look=look, tilt=14 * math.sin(TAU * phase), nod=-6 * _bump(phase, 0.4, 0.6))
	cat.box.open(1.0)


def box_attack(arm, phase, cat=None, direction=0):
	"""Turned towards its target (the box stays put), it rears back, then lunges over the rim and hacks up a hairball
	at the last frame. Ending the attack plays it backwards."""
	rest(arm)
	rear = _bump(phase, 0.0, 0.5)
	lunge = _ease(phase, 0.35, 1.0)
	_sit(arm, lean=-10 * rear + 38 * lunge, nod=-8 * rear + 14 * lunge)
	_set(arm, "chest", -10 * lunge)
	cat.box.open(1.0)


def box_die(arm, phase, cat=None, direction=0):
	"""Pops up in surprise, bursting the box: the walls fall open, the front flat on the ground, and the cat flops
	forward onto it, knocked out with X eyes, paws out in front; the corpse keeps the last frame."""
	rest(arm)
	pop = _bump(phase, 0.0, 0.3)
	burst = _ease(phase, 0.12, 0.55)
	flop = _ease(phase, 0.25, 0.65)
	settle = _bump(phase, 0.65, 0.85)
	_sit(arm, emerge=1.0 + 0.15 * pop, lean=100 * flop - 6 * settle, nod=20 * flop)
	# with the front wall gone it slumps down and forward onto it
	root = arm.pose.bones["root"]
	root.location.y += 0.2 * flop
	root.location.z -= 0.3 * flop
	for side in ("L", "R"):
		_set(arm, f"front_upper.{side}", (70 - 0.5 * SIT_PITCH) * (1 - flop) - 20 * flop)
		_set(arm, f"front_lower.{side}", -35 * (1 - flop) + 10 * flop)
		_set(arm, f"front_paw.{side}", -40 * (1 - flop) + 20 * flop)
	# the tail goes limp, flopping back over the box's back rim
	limp = _ease(phase, 0.45, 0.8)
	upright = [(78, 0), (84, 0), (80, 4), (64, 8), (40, 12)]
	draped = [(55, 0), (25, 6), (-25, 10), (-60, 12), (-75, 12)]
	_aim_tail(arm, [0] * TAIL_BONES, [0] * TAIL_BONES, [(a[0] + (b[0] - a[0]) * limp, a[1] + (b[1] - a[1]) * limp)
		for a, b in zip(upright, draped)], 1.0)
	cat.box.open(1.0)
	cat.box.burst(burst)
	cat.knock_out(phase >= 0.45)


def sleep(arm, breath, wake=0.0, out=0.0, wrap=1, quirk=0.0):
	"""The nests' kittens: asleep as a loaf, paws tucked under, head down and turned, tail wrapped round its side;
	breath swells it a little. wake lifts the head; out rolls it onto its side towards wrap, legs stiff, knocked out,
	resting where the knocked-out cats do."""
	rest(arm)
	root = arm.pose.bones["root"]
	angle = math.radians(90 * out) * wrap
	centre = 0.55
	height = centre - 0.15 * out - 0.27 * (1 - out)
	root.location = (-centre * math.sin(angle) - 0.1 * out * wrap, 0, height - centre * math.cos(angle))
	root.rotation_euler = (0, angle, 0)
	root.scale = (1 + 0.02 * breath, 1, 1 + 0.04 * breath)
	tuck = 1 - out
	for side in ("L", "R"):
		_set(arm, f"front_upper.{side}", -70 * tuck + 25 * out)
		_set(arm, f"front_lower.{side}", 110 * tuck + 10 * out)
		_set(arm, f"front_paw.{side}", -35 * tuck + 15 * out)
		_set(arm, f"thigh.{side}", 50 * tuck - 25 * out)
		_set(arm, f"shin.{side}", 45 * tuck - 10 * out)
		_set(arm, f"hock.{side}", -100 * tuck + 20 * out)
	lift = max(wake, out)
	_set(arm, "neck", -12 * (1 - lift) + 10 * wake - 10 * out, 0, (14 + 10 * quirk) * wrap * (1 - lift) + 21 * wrap * out)
	_set(arm, "head", 16 * (1 - lift) - 6 * wake - 10 * out, 0, 8 * wrap * out)
	arm.pose.bones["head"].rotation_euler.y = math.radians(10 * wrap * (1 - lift))
	flick = 15 * breath * (1 if quirk > 0.5 else 0)
	# wrapped round its side asleep; knocked out it lies limp behind, as the knocked-out cats' does
	asleep = [(-25, 25 * wrap), (-8, 70 * wrap), (0, 110 * wrap), (2, 145 * wrap), (6 + flick, 175 * wrap)]
	limp = [(-45, 4 * -wrap), (-38, 14 * -wrap), (0, 34 * -wrap), (1, 60 * -wrap), (3, 88 * -wrap)]
	_aim_tail(arm, [0] * TAIL_BONES, [0] * TAIL_BONES, [(a[0] + (b[0] - a[0]) * out, a[1] + (b[1] - a[1]) * out)
		for a, b in zip(asleep, limp)], 1.0)


ANIMATIONS = {
	"stand": {"frames": 1, "pose": lambda arm, phase, cat=None, direction=0: rest(arm)},
	"run": {"frames": 16, "pose": run},
	"attack": {"frames": 11, "pose": attack},
	"die": {"frames": 17, "pose": die, "once": True},
	"trot": {"frames": 16, "pose": trot},
	"spit": {"frames": 14, "pose": spit, "once": True},
	"box_folded": {"frames": 9, "pose": box_folded, "directions": 1},
	"box_preparing": {"frames": 18, "pose": box_preparing, "directions": 1, "once": True},
	"box_prepared": {"frames": 9, "pose": box_prepared, "directions": 1},
	"box_alternative": {"frames": 17, "pose": box_alternative, "directions": 1},
	"box_attack": {"frames": 10, "pose": box_attack, "once": True},
	"box_die": {"frames": 24, "pose": box_die, "directions": 1, "once": True},
	"sleep": {"frames": 7, "directions": 1, "once": True,
		"pose": lambda arm, phase, cat=None, direction=0: (sleep(arm, phase), cat and cat.set_eyes("closed"))},
	"sleep_die": {"frames": 18, "directions": 1, "once": True,
		"pose": lambda arm, phase, cat=None, direction=0: (sleep(arm, 0, wake=_bump(phase, 0.05, 0.45),
			out=_ease(phase, 0.35, 0.75)), cat and cat.set_eyes("closed" if phase < 0.08 else "open" if phase < 0.5
			else "x"))},
}


def phase(spec, frame):
	"""A cycle's frames divide it evenly; an animation played once ends on its last pose."""
	return frame / (spec["frames"] - 1) if spec.get("once") else frame / spec["frames"]

# what each family renders for its run, attack and death (or the worms' box animations), and the pattern sets its
# coats use (variants.lua and worms.lua), the only masks it needs
FAMILIES = {
	"biter": {"style": "shorthair", "patterns": ("tabby", "tabby-white", "patches", "patches-white"), "run": "run",
		"attack": "attack", "die": "die"},
	"spitter": {"style": "longhair", "patterns": ("tabby", "patches", "points"), "run": "trot", "attack": "spit",
		"die": "die"},
	"worm": {"style": "shorthair", "patterns": ("tabby", "tabby-white", "patches-white"), "box": True,
		"folded": "box_folded", "preparing": "box_preparing",
		"prepared": "box_prepared", "prepared-alternative": "box_alternative", "attack": "box_attack", "die": "box_die"},
}

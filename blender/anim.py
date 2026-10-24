# Poses for the cat's animations, as functions of the phase (0 to 1) through the cycle. Angles are degrees; bones pitch
# about their local X axis (positive swings a leg's paw forward) and swing sideways about Z.
import math

TAU = 2 * math.pi


def _set(arm, bone, x=0.0, y=0.0, z=0.0):
	arm.pose.bones[bone].rotation_euler = (math.radians(x), math.radians(y), math.radians(z))


def rest(arm):
	for bone in arm.pose.bones:
		bone.rotation_euler = (0, 0, 0)
		bone.location = (0, 0, 0)


def _swing(p):
	"""0 on the ground, rising to 1 mid-swing, for a leg at phase p (stance 0-0.5, swing 0.5-1)."""
	p %= 1
	return math.sin(math.pi * (p - 0.5) / 0.5) if p > 0.5 else 0.0


def _front_leg(arm, side, p, reach=46):
	lift = _swing(p)
	_set(arm, f"front_upper.{side}", reach * math.cos(TAU * p) + 8 * lift)
	_set(arm, f"front_lower.{side}", -75 * lift)
	_set(arm, f"front_paw.{side}", -50 * lift + 15 * max(0, math.sin(TAU * p)))


def _hind_leg(arm, side, p, reach=36):
	lift = _swing(p)
	_set(arm, f"thigh.{side}", reach * math.cos(TAU * p) + 10 * lift)
	_set(arm, f"shin.{side}", 30 * lift - 10 * max(0, -math.cos(TAU * p)))
	_set(arm, f"hock.{side}", -55 * lift + 15 * max(0, -math.cos(TAU * p)))
	_set(arm, f"hind_paw.{side}", 30 * lift)


def _bump(phase, start, end):
	"""0 outside start-end, rising smoothly to 1 in the middle."""
	if phase <= start or phase >= end:
		return 0.0
	return math.sin(math.pi * (phase - start) / (end - start))


def _ease(phase, start, end):
	"""0 before start, easing to 1 at end."""
	t = min(max((phase - start) / (end - start), 0.0), 1.0)
	return t * t * (3 - 2 * t)


def run(arm, phase, cat=None, direction=0):
	"""A bouncy bound: the front paws reach out together, then the hind legs push off together."""
	rest(arm)
	_front_leg(arm, "L", phase)
	_front_leg(arm, "R", phase + 0.07)
	_hind_leg(arm, "L", phase + 0.5)
	_hind_leg(arm, "R", phase + 0.57)
	# the spine gathers when the hind paws come forward and stretches out when the front paws reach
	flex = math.cos(TAU * phase)
	_set(arm, "hips", 10 * flex)
	_set(arm, "chest", -8 * flex)
	# up in the air after the hind legs push, with the head kept steady
	arm.pose.bones["root"].location = (0, 0, 0.1 * max(0.0, math.sin(TAU * (phase - 0.15))))
	_set(arm, "neck", 6 * flex - 4 * math.sin(TAU * phase))
	_set(arm, "head", -2 * flex + 3 * math.sin(TAU * phase))
	# the tail trails in a wave down its length
	for i in range(5):
		_set(arm, f"tail{i}", 9 * math.sin(TAU * (phase - 0.12 * i)) - 4, 0, 7 * math.sin(TAU * (phase - 0.1 * i)))


def attack(arm, phase, cat=None, direction=0):
	"""A playful pounce: a crouch with a wiggle of the bottom, a hop forward with both paws up, and a swipe."""
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
	for i in range(5):
		_set(arm, f"tail{i}", -6 * crouch + 5 * math.sin(TAU * (phase - 0.1 * i)) * (1 - crouch), 0,
			10 * math.sin(2 * TAU * (phase - 0.1 * i)) * crouch)


def die(arm, phase, cat=None, direction=0):
	"""A surprised hop, then a flop onto the side with the legs stuck out stiff and X eyes; the corpse keeps the last
	frame. The cat rolls towards the camera (south), so its belly, paws and face show whichever way it faces."""
	rest(arm)
	hop = _bump(phase, 0.0, 0.3)
	roll = _ease(phase, 0.2, 0.6)
	settle = _bump(phase, 0.6, 0.8)
	# facing east-ish its right side faces the camera: it lies down on its left, and the other way round
	side = -1 if math.sin(TAU * direction / 16) >= 0 else 1
	angle = math.radians(90 * roll) * side
	# rolled about the body's length, the middle of the body comes to rest on its side above the ground
	centre = 0.55
	height = centre - 0.24 * roll + 0.12 * hop + 0.03 * settle
	arm.pose.bones["root"].location = (-centre * math.sin(angle) - 0.1 * roll * side, 0, height - centre * math.cos(angle))
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
	for i in range(5):
		_set(arm, f"tail{i}", 20 * hop * (1 if i == 0 else 0) - 18 * roll)
	if cat is not None:
		cat.knock_out(phase >= 0.45)


ANIMATIONS = {
	"stand": {"frames": 1, "pose": lambda arm, phase, cat=None, direction=0: rest(arm)},
	"run": {"frames": 16, "pose": run},
	"attack": {"frames": 11, "pose": attack},
	"die": {"frames": 17, "pose": die},
}

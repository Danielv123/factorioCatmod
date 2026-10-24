# Packs rendered frames into sprite sheets with a util.sprite_load descriptor beside them, the format vanilla's enemy
# graphics use: <name>.lua gives the frame size, shift and file layout of <name>-1.png, <name>-2.png, ...
# Frames are cropped to the union of their opaque areas, and the shift keeps them where the camera put them, which is
# with the entity's position at the frame's centre.
import math
import os

import bpy
import numpy as np

LINE_LENGTH = 8
MAX_SHEET = 4096


def load(path):
	image = bpy.data.images.load(path)
	width, height = image.size
	pixels = np.array(image.pixels[:], dtype=np.float32).reshape(height, width, 4)[::-1]
	bpy.data.images.remove(image)
	return pixels


def save(path, pixels):
	height, width = pixels.shape[:2]
	image = bpy.data.images.new(os.path.basename(path), width, height, alpha=True)
	image.pixels = pixels[::-1].ravel()
	image.filepath_raw = path
	image.file_format = "PNG"
	image.save()
	bpy.data.images.remove(image)


def pack(frames, out_dir, name, shadow=False):
	"""frames: arrays in Factorio's frame order (all frames of direction 0, then direction 1, ...)."""
	height, width = frames[0].shape[:2]
	if shadow:
		# Factorio draws shadow sprites as black, with the alpha as the shadow's strength; the faint occlusion the shadow
		# catcher sees all around goes
		frames = [np.dstack([np.zeros_like(f[..., :3]), np.clip((f[..., 3:4] - 0.08) / 0.92, 0, 1)]) for f in frames]
	alpha = np.max([f[..., 3] for f in frames], axis=0)
	ys, xs = np.nonzero(alpha > 1 / 255)
	x0, x1 = max(0, xs.min() - 1), min(width, xs.max() + 2)
	y0, y1 = max(0, ys.min() - 1), min(height, ys.max() + 2)
	fw, fh = x1 - x0, y1 - y0
	shift_x = (x0 + x1) / 2 - width / 2
	shift_y = (y0 + y1) / 2 - height / 2
	line_length = min(LINE_LENGTH, len(frames))
	lines = math.ceil(len(frames) / line_length)
	lines_per_file = max(1, min(lines, MAX_SHEET // fh))
	files = math.ceil(lines / lines_per_file)
	os.makedirs(out_dir, exist_ok=True)
	for file in range(files):
		count = min(lines_per_file, lines - file * lines_per_file)
		sheet = np.zeros((count * fh, line_length * fw, 4), dtype=np.float32)
		for line in range(count):
			for column in range(line_length):
				index = (file * lines_per_file + line) * line_length + column
				if index < len(frames):
					sheet[line * fh:(line + 1) * fh, column * fw:(column + 1) * fw] = frames[index][y0:y1, x0:x1]
		save(os.path.join(out_dir, f"{name}-{file + 1}.png"), sheet)
	filenames = ",\n".join(f'    "-{i + 1}.png"' for i in range(files))
	# util.by_pixel counts 32 px a tile, and these sheets have 64 at scale 1 (Factorio draws them at scale 0.5)
	descriptor = (f"return\n{{\n  width = {fw},\n  height = {fh},\n"
		f"  shift = util.by_pixel({shift_x / 2:.1f}, {shift_y / 2:.1f}),\n  line_length = {line_length},\n"
		f"  filenames =\n  {{\n{filenames},\n  }},\n  lines_per_file = {lines_per_file},\n}}\n")
	with open(os.path.join(out_dir, f"{name}.lua"), "w", newline="\n") as f:
		f.write(descriptor)

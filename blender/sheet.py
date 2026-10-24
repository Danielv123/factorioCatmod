# Packs rendered frames into sprite sheets with a util.sprite_load descriptor beside them, the format vanilla's enemy
# graphics use: <name>.lua gives the frame size, shift and file layout of <name>-1.png, <name>-2.png, ...
# Frames are cropped to the union of their opaque areas, and the shift keeps them where the camera put them, which is
# with the entity's position at the frame's centre.
#
# Sheets are written here rather than by Blender, at full compression with the best row filter: the colour layer as
# RGBA, the shadow (black) and masks (white) as grey with alpha, which is all they need.
import math
import os
import struct
import zlib

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
	"""An RGBA float image, as an RGBA PNG."""
	write_png(path, np.round(np.clip(pixels, 0, 1) * 255).astype(np.uint8))


def write_png(path, pixels):
	"""Writes uint8 pixels (height, width, 2 or 4 channels) as a grey+alpha or RGBA PNG."""
	height, width, channels = pixels.shape
	colour_type = {2: 4, 4: 6}[channels]
	rows = pixels.reshape(height, width * channels).astype(np.int16)
	# per image, the row filter that compresses best: none, sub or up
	sub = rows.copy()
	sub[:, channels:] -= rows[:, :-channels]
	up = rows.copy()
	up[1:] -= rows[:-1]
	best = None
	for kind, filtered in ((0, rows), (1, sub), (2, up)):
		raw = np.hstack([np.full((height, 1), kind, np.uint8), (filtered % 256).astype(np.uint8)]).tobytes()
		data = zlib.compress(raw, 9)
		if best is None or len(data) < len(best):
			best = data

	def chunk(tag, body):
		return struct.pack(">I", len(body)) + tag + body + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)

	with open(path, "wb") as f:
		f.write(b"\x89PNG\r\n\x1a\n")
		f.write(chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, colour_type, 0, 0, 0)))
		f.write(chunk(b"IDAT", best))
		f.write(chunk(b"IEND", b""))


def pack(frames, out_dir, name, kind="colour"):
	"""frames in Factorio's frame order (all frames of direction 0, then direction 1, ...): RGBA float arrays for
	"colour", the shadow pass's RGBA for "shadow", or float alpha arrays for "mask"."""
	if kind == "colour":
		frames = [np.round(np.clip(f, 0, 1) * 255).astype(np.uint8) for f in frames]
	else:
		if kind == "shadow":
			# Factorio draws shadow sprites as black, with the alpha as the shadow's strength; the faint occlusion the
			# shadow catcher sees all around goes
			frames = [np.clip((f[..., 3] - 0.08) / 0.92, 0, 1) for f in frames]
		grey = 0 if kind == "shadow" else 255
		frames = [np.dstack([np.full(f.shape, grey, np.uint8), np.round(np.clip(f, 0, 1) * 255).astype(np.uint8)])
			for f in frames]
	height, width = frames[0].shape[:2]
	alpha = np.max([f[..., -1] for f in frames], axis=0)
	ys, xs = np.nonzero(alpha > 0)
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
		sheet = np.zeros((count * fh, line_length * fw, frames[0].shape[2]), dtype=np.uint8)
		for line in range(count):
			for column in range(line_length):
				index = (file * lines_per_file + line) * line_length + column
				if index < len(frames):
					sheet[line * fh:(line + 1) * fh, column * fw:(column + 1) * fw] = frames[index][y0:y1, x0:x1]
		write_png(os.path.join(out_dir, f"{name}-{file + 1}.png"), sheet)
	filenames = ",\n".join(f'    "-{i + 1}.png"' for i in range(files))
	# util.by_pixel counts 32 px a tile, and these sheets have 64 at scale 1 (Factorio draws them at scale 0.5)
	descriptor = (f"return\n{{\n  width = {fw},\n  height = {fh},\n"
		f"  shift = util.by_pixel({shift_x / 2:.1f}, {shift_y / 2:.1f}),\n  line_length = {line_length},\n"
		f"  filenames =\n  {{\n{filenames},\n  }},\n  lines_per_file = {lines_per_file},\n}}\n")
	with open(os.path.join(out_dir, f"{name}.lua"), "w", newline="\n") as f:
		f.write(descriptor)

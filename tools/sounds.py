# Builds the mod's cat sounds from CC0 recordings on Freesound (credits in sound/CREDITS.md): downloads each source's
# preview, cuts it into single sounds at its silences, trims, fades and evens out their loudness, and writes mono Ogg
# Vorbis files to sound/<kind>-<n>.ogg. Needs ffmpeg.
#   python tools/sounds.py [download dir]
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "sound")
RATE = 44100

# (freesound user, id, kind, how many sounds to cut from it, shortest and longest in seconds, and optionally how far
# below the loudest a sound starts in dB and the longest gap in seconds within one sound, for noisier recordings)
SOURCES = [
	("tuberatanka", 110011, "meow", 1, 0.3, 1.6),
	("skymary", 412017, "meow", 1, 0.3, 1.6),
	("TRNGLE", 362652, "meow", 1, 0.3, 1.6),
	("Mafon2", 436541, "meow", 1, 0.2, 1.0),
	("lolamadeus", 196251, "kitten", 4, 0.25, 1.2, -14),
	("Zabuhailo", 146963, "hiss", 1, 0.3, 1.5),
	("Zabuhailo", 146972, "growl", 1, 0.8, 3.0, -20),
	("Islabonita", 471059, "growl", 2, 0.8, 3.0, -20),
	("urmumsacow", 49784, "growl", 2, 0.8, 3.0, -20),
	("dreamstobecome", 451250, "chirp", 3, 0.12, 1.0),
	("jsbarrett", 200336, "chirp", 3, 0.3, 1.5),
	("CatPhony", 850104, "chirp", 1, 0.2, 1.0),
	("MBPL", 668825, "chirp", 1, 0.2, 1.0),
	("Electron%20John", 82543, "hack", 3, 0.4, 2.0, -20, 0.45),
	("har2h", 561726, "hack", 3, 0.15, 1.2, -20),
	("14GPanskaZakopcanik_Jonas", 420086, "hack", 1, 0.3, 1.8, -20),
	("Trautwein", 260881, "purr", 1, None, None),
	("cubilon", 130968, "purr", 1, None, None),
]
# how loud each kind sits, as the RMS of its loud part in dBFS: purrs soft, meows and hacks forward
LEVEL = {"meow": -16, "kitten": -16, "hiss": -17, "growl": -18, "chirp": -18, "hack": -16, "purr": -28}
HEADERS = {"User-Agent": "Mozilla/5.0 (catmod sound build)"}


def download(user, sound_id, folder):
	path = os.path.join(folder, f"{sound_id}.mp3")
	if not os.path.exists(path):
		page = urllib.request.urlopen(urllib.request.Request(f"https://freesound.org/people/{user}/sounds/{sound_id}/",
			headers=HEADERS), timeout=30).read().decode("utf-8", "replace")
		if "creativecommons.org/publicdomain/zero" not in page:
			raise RuntimeError(f"{sound_id} is no longer CC0")
		preview = re.findall(r'https://cdn\.freesound\.org/previews/[^"\']+-hq\.mp3', page)[0]
		data = urllib.request.urlopen(urllib.request.Request(preview, headers=HEADERS), timeout=60).read()
		open(path, "wb").write(data)
	return path


def decode(path):
	raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"],
		check=True, capture_output=True).stdout
	return np.frombuffer(raw, dtype=np.float32).copy()


def envelope(audio, window=0.02):
	n = int(RATE * window)
	frames = len(audio) // n
	rms = np.sqrt(np.mean(audio[:frames * n].reshape(frames, n) ** 2, axis=1) + 1e-12)
	return 20 * np.log10(rms), n


def segments(audio, shortest, longest, floor_db=-32, gap=0.12):
	"""The loud stretches, more than floor_db below the loudest, merged across gaps shorter than gap seconds."""
	db, n = envelope(audio)
	loud = db > db.max() + floor_db
	found, start, quiet = [], None, 0
	for i, on in enumerate(loud):
		if on:
			if start is None:
				start = i
			quiet = 0
		elif start is not None:
			quiet += 1
			if quiet * n / RATE > gap:
				found.append((start, i - quiet + 1))
				start, quiet = None, 0
	if start is not None:
		found.append((start, len(loud)))
	result = []
	for a, b in found:
		length = (b - a) * n / RATE
		if shortest <= length <= longest:
			result.append((a * n, b * n, float(db[a:b].max())))
	return result


def finish(clip, kind, fade_in=0.008, fade_out=0.05):
	"""Fades, evens out the loudness, and keeps the peaks clear of clipping."""
	clip = clip.copy()
	fade_in, fade_out = int(RATE * fade_in), int(RATE * fade_out)
	clip[:fade_in] *= np.linspace(0, 1, fade_in) ** 2
	clip[-fade_out:] *= np.linspace(1, 0, fade_out) ** 2
	db, n = envelope(clip)
	loud = db > db.max() - 12
	rms = 10 ** (np.mean(db[loud]) / 20)
	clip *= 10 ** (LEVEL[kind] / 20) / rms
	peak = np.abs(clip).max()
	if peak > 0.89:
		clip *= 0.89 / peak
	return clip


def middle(audio, seconds=6.0):
	"""A stretch from the middle of a long recording."""
	length = int(RATE * seconds)
	start = len(audio) // 2 - length // 2
	return audio[start:start + length].copy()


def write(clip, name):
	with tempfile.NamedTemporaryFile(suffix=".f32", delete=False) as f:
		f.write(clip.astype(np.float32).tobytes())
		raw = f.name
	subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(RATE), "-ac", "1", "-i", raw, "-c:a",
		"libvorbis", "-q:a", "4", os.path.join(OUT, name)], check=True)
	os.remove(raw)


def main():
	folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "catmod-sounds")
	os.makedirs(folder, exist_ok=True)
	os.makedirs(OUT, exist_ok=True)
	counts, made = {}, []
	for user, sound_id, kind, count, shortest, longest, *tuning in SOURCES:
		audio = decode(download(user, sound_id, folder))
		floor_db, gap = (tuning + [-32, 0.12][len(tuning):])[:2]
		if kind == "purr":
			clips = [middle(audio)]
		else:
			found = sorted(segments(audio, shortest, longest, floor_db, gap), key=lambda s: -s[2])[:count]
			pad = int(RATE * 0.03)
			clips = [audio[max(0, a - pad):min(len(audio), b + pad * 2)] for a, b, _ in sorted(found)]
		for clip in clips:
			counts[kind] = counts.get(kind, 0) + 1
			name = f"{kind}-{counts[kind]}.ogg"
			# a purr swells up and dies away, a passing contented moment rather than a drone
			write(finish(clip, kind, 1.5, 2.2) if kind == "purr" else finish(clip, kind), name)
			made.append({"file": name, "source": f"https://freesound.org/people/{user}/sounds/{sound_id}/",
				"seconds": round(len(clip) / RATE, 2)})
	json.dump(made, open(os.path.join(folder, "made.json"), "w"), indent=1)
	for kind, count in sorted(counts.items()):
		print(f"{kind}: {count}")


if __name__ == "__main__":
	main()

# Cat models

The cats are built, rigged, animated and rendered in code with Blender 5.2 and Cycles. Run from this directory:

    blender -b --factory-startup -P render.py -- <animation> [family]

This renders the animation in Factorio's 16 directions and packs it into `graphics/cat/<family>/` as sprite sheets
with `util.sprite_load` descriptors. The renders stay out of git until a release.

Each animation has these layers:

- `<animation>`: the cat with white fur, eyes and nose, drawn as is.
- `<animation>-shadow`.
- `<animation>-coat-<pattern>` and `<animation>-marks-<pattern>`: alpha-only masks of where the coat and its stripes
  or patches are, for each pattern set. `data.lua` draws them with `multiplicative-with-alpha` and a tint, which
  multiplies the white cat by the coat's colours, so every coat in `variants.lua` shares the same sheets.

`preview.py -- <out_dir> <animation> [direction] [coat] [zoom]` renders one direction composed with a sample coat, for
checking an animation.

- `cat.py` builds the cat: a metaball body with ears, eyes and nose, baked procedural fur, and the mask looks.
- `rig.py` is its skeleton, and `anim.py` the poses of each animation.
- `scene.py` sets up the camera, light and passes to match Factorio's sprites.
- `sheet.py` packs frames into sheets.

# Cat models

The cats are built, rigged and rendered in code with Blender 5.2 and Cycles. Run from this directory:

    blender -b --factory-startup -P render.py -- <coat> <animation>

This renders the animation in Factorio's 16 directions with its shadow, and packs both into `graphics/cat/<coat>/`
as sprite sheets with `util.sprite_load` descriptors. `turnaround.py` renders a contact sheet for judging the look.

- `cat.py` builds the cat: a metaball body with ears, eyes and nose, procedural fur and coat patterns.
- `scene.py` sets up the camera, light and shadow passes to match Factorio's sprites.
- `sheet.py` packs frames into sheets.

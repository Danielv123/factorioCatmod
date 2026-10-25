# Cat models

The cats are built, rigged, animated and rendered in code with Blender 5.2 and Cycles. Run from this directory:

    blender -b --factory-startup -P render.py -- <animation> <biter|spitter|worm>
    blender -b --factory-startup -P nest.py -- <biter|spitter>
    blender -b --factory-startup -P hairball.py
    blender -b --factory-startup -P extras.py -- <tufts|icons>

`render.py` renders an animation in Factorio's 16 directions and packs it into `graphics/cat/<family>/` as sprite
sheets with `util.sprite_load` descriptors. The animations are the family's keys in `anim.FAMILIES`: `run`, `attack`
and `die` for biters and spitters; `folded`, `preparing`, `prepared`, `prepared-alternative`, `attack` and `die` for
worms. The renders stay out of git until a release.

`./render_all.sh [parallel jobs]` renders everything, seven Blender processes at once by default: one process can't
keep the GPU busy, as much of each frame is single-threaded posing, fur deforming and image saving. Each job needs
up to 6 GB of memory and 3 GB of video memory. Pass jobs to render only some, e.g. `./render_all.sh 3 "render.py -- attack worm"`.

Each animation has these layers:

- `<animation>`: the cat with white fur, eyes and nose, drawn as is.
- `<animation>-shadow`.
- `<animation>-coat-<white>`: an alpha-only mask of where the coat is, markings included, for each amount of white
  (`low`, `high` or `none`), shared by the pattern sets with that white.
- `<animation>-marks-<pattern>`: an alpha-only mask of where the stripes or patches are, for each pattern set.

The masks are half resolution, drawn twice the size: they only say where a colour goes, and the fur blurs their edges.
`data.lua` draws them with `multiplicative-with-alpha` and a tint, multiplying the white cat by the coat colour and
then the markings by markings / coat, so every coat in `variants.lua` shares the same sheets. A coat's markings must be
darker than its coat in every channel.

`preview.py -- <out_dir> <animation> [direction] [coat] [zoom] [style]` renders one direction composed with a sample
coat, and `sideview.py -- <out.png> <animation> [style]` a contact sheet from straight side on, for checking an
animation.

- `cat.py` builds the cat: a metaball body with ears, eyes and nose, baked procedural fur in short and long styles,
  and the mask looks.
- `rig.py` is its skeleton, and `anim.py` the poses of each animation. The gallop's tail is traced from Muybridge's
  photographs of a galloping cat (Animal Locomotion, plate 720).
- `box.py` is the worms' cardboard box, which bursts open when its cat is knocked out; `bed.py` the nests' beds and
  baskets, which break apart; `nest.py` renders the kittens in them.
- `scene.py` sets up the camera, light and passes to match Factorio's sprites.
- `sheet.py` packs frames into sheets.

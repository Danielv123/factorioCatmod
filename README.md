# factorioCatmod

Replaces biters with cute cats, because it had to happen.

- **Biters** are short-haired cats that gallop, pounce, and flop over knocked out with X eyes.
- **Spitters** are fluffy long-haired cats that trot and cough up hairballs.
- **Worms** are cats hiding in cardboard boxes, popping up to spit hairballs over the rim.
- **Nests** are cat beds and baskets of sleeping kittens.

Each tier has a few coats, so a pack doesn't all look the same. Fur flies instead of blood.

The models are built, animated and rendered in code with Blender; see [blender/README.md](blender/README.md).

## Releasing

The rendered sprite sheets in `graphics/cat/` are committed for releases; render them again after changing the models
(see `blender/README.md`). Set the version in `info.json`, add a `changelog.txt` entry, commit, and push a matching tag
(`git tag v4.0.0 && git push --tags`). CI zips the mod and uploads it to the mod portal with the `FACTORIO_MOD_TOKEN`
secret.

The cat sounds are cut from CC0 recordings; see [sound/CREDITS.md](sound/CREDITS.md).

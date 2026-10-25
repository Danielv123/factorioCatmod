# factorioCatmod

Replaces biters with cute cats, because it had to happen.

- **Biters** are short-haired cats that gallop, pounce, and flop over knocked out with X eyes.
- **Spitters** are fluffy long-haired cats that trot and cough up hairballs.
- **Worms** are cats hiding in cardboard boxes, popping up to spit hairballs over the rim.
- **Nests** are cat beds and baskets of sleeping kittens.

Each tier has a few coats, so a pack doesn't all look the same. Fur flies instead of blood.

The models are built, animated and rendered in code with Blender; see [blender/README.md](blender/README.md).

## Releasing

The rendered sprite sheets are kept out of git until a release (`graphics/cat/` is ignored). Render them first (see
`blender/README.md`), set the version in `info.json`, commit, and push a matching tag
(`git tag v4.0.0 && git push --tags`). CI zips the mod and uploads it to the mod portal with the `FACTORIO_MOD_TOKEN`
secret.

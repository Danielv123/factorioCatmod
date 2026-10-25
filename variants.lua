-- The cats of each enemy tier: short-haired cats for the biters, fluffy long-haired ones for the spitters, one coat
-- family per tier in a few variants so a pack doesn't look all the same. Factorio has one look per unit, so each
-- variant is its own unit; spawners split the tier's spawn weight over them.
-- A coat is a pattern set (which coat and markings masks) and the colours the masks tint the white cat with.
return {
	{family = "biter", unit = "small-biter", cat = "small-cat", scale = 0.5, volume = 0.4,
		variants = {
			{pattern = "tabby", coat = {1.0, 0.5, 0.14}, marks = {0.62, 0.22, 0.05}, size = 1.0},
			{pattern = "tabby-white", coat = {1.0, 0.5, 0.14}, marks = {0.62, 0.22, 0.05}, size = 0.94},
			{pattern = "tabby", coat = {1.0, 0.82, 0.55}, marks = {0.85, 0.55, 0.3}, size = 1.05},
		}},
	{family = "biter", unit = "medium-biter", cat = "medium-cat", scale = 0.7, volume = 0.5,
		variants = {
			{pattern = "tabby", coat = {0.62, 0.62, 0.64}, marks = {0.22, 0.22, 0.24}, size = 1.0},
			{pattern = "tabby", coat = {0.62, 0.45, 0.28}, marks = {0.22, 0.14, 0.08}, size = 1.05},
			{pattern = "tabby-white", coat = {0.62, 0.62, 0.64}, marks = {0.22, 0.22, 0.24}, size = 0.95},
		}},
	{family = "biter", unit = "big-biter", cat = "big-cat", scale = 1.0, volume = 0.6,
		variants = {
			{pattern = "tabby-white", coat = {0.1, 0.1, 0.11}, marks = {0.1, 0.1, 0.11}, size = 1.0},
			{pattern = "tabby", coat = {0.09, 0.09, 0.1}, marks = {0.07, 0.07, 0.08}, size = 1.05},
			{pattern = "tabby", coat = {0.3, 0.3, 0.33}, marks = {0.12, 0.12, 0.13}, size = 0.95},
		}},
	{family = "biter", unit = "behemoth-biter", cat = "behemoth-cat", scale = 1.2, volume = 0.8,
		variants = {
			{pattern = "patches-white", coat = {1.0, 0.55, 0.18}, marks = {0.12, 0.1, 0.1}, size = 1.0},
			{pattern = "patches", coat = {0.13, 0.1, 0.09}, marks = {0.85, 0.42, 0.12}, size = 1.04},
			{pattern = "patches-white", coat = {1.0, 0.8, 0.58}, marks = {0.45, 0.47, 0.52}, size = 0.96},
		}},
	{family = "spitter", unit = "small-spitter", cat = "small-fluffy-cat", scale = 0.5, volume = 0.4,
		variants = {
			{pattern = "tabby", coat = {1.0, 0.86, 0.66}, marks = {0.88, 0.64, 0.4}, size = 1.0},
			{pattern = "tabby", coat = {0.97, 0.96, 0.94}, marks = {0.97, 0.96, 0.94}, size = 0.95},
			{pattern = "tabby", coat = {0.82, 0.82, 0.85}, marks = {0.3, 0.3, 0.34}, size = 1.05},
		}},
	{family = "spitter", unit = "medium-spitter", cat = "medium-fluffy-cat", scale = 0.7, volume = 0.5,
		variants = {
			{pattern = "tabby", coat = {0.5, 0.54, 0.62}, marks = {0.44, 0.48, 0.56}, size = 1.0},
			{pattern = "patches", coat = {0.5, 0.54, 0.62}, marks = {0.95, 0.8, 0.62}, size = 1.04},
			{pattern = "tabby", coat = {0.78, 0.7, 0.72}, marks = {0.7, 0.62, 0.64}, size = 0.96},
		}},
	{family = "spitter", unit = "big-spitter", cat = "big-fluffy-cat", scale = 1.0, volume = 0.6,
		variants = {
			{pattern = "tabby", coat = {0.6, 0.42, 0.25}, marks = {0.2, 0.12, 0.06}, size = 1.0},
			{pattern = "tabby", coat = {0.95, 0.5, 0.18}, marks = {0.6, 0.24, 0.06}, size = 1.05},
			{pattern = "tabby", coat = {0.16, 0.16, 0.18}, marks = {0.09, 0.09, 0.1}, size = 0.95},
		}},
	{family = "spitter", unit = "behemoth-spitter", cat = "behemoth-fluffy-cat", scale = 1.2, volume = 0.8,
		variants = {
			{pattern = "points", coat = {0.96, 0.9, 0.78}, marks = {0.24, 0.16, 0.11}, size = 1.0},
			{pattern = "points", coat = {0.94, 0.94, 0.96}, marks = {0.42, 0.46, 0.56}, size = 1.04},
			{pattern = "points", coat = {1.0, 0.94, 0.84}, marks = {0.95, 0.55, 0.25}, size = 0.96},
		}},
}

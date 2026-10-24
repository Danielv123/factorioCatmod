-- Cats are the base game biters with a cat's run animation, icon and sounds. With catmod_replace_bitter the biters
-- themselves turn into cats, otherwise the cats are new units next to them.

local function cat_run_animation(scale)
	return {
		layers = {
			{
				width = 512,
				height = 300,
				frame_count = 5,
				direction_count = 16,
				animation_speed = 0.3,
				shift = {scale * 0.714844, scale * -0.246094},
				scale = scale * 0.5,
				stripes = {
					{
						filename = "__catmod__/graphics/cat_hr.png",
						width_in_frames = 8,
						height_in_frames = 10,
					},
				},
			},
		},
	}
end

local function cat_sound(volume, files)
	local variations = {}
	for _, file in pairs(files) do
		variations[#variations + 1] = {filename = "__catmod__/sound/" .. file .. ".ogg", volume = volume}
	end
	return {
		category = "enemy",
		variations = variations,
		aggregation = {max_count = 2, remove = true, count_already_playing = true},
	}
end

local replace = settings.startup["catmod_replace_bitter"].value
local cats = {
	{biter = "small-biter", cat = "small-cat", explosion = "blood-explosion-small", scale = 0.5, volume = 0.4, order = "b-b-a"},
	{biter = "medium-biter", cat = "medium-cat", explosion = "blood-explosion-small", scale = 0.7, volume = 0.5, order = "b-b-b"},
	{biter = "big-biter", cat = "big-cat", explosion = "blood-explosion-big", scale = 1.0, volume = 0.6, order = "b-b-c"},
	{biter = "behemoth-biter", cat = "behemoth-cat", explosion = "blood-explosion-big", scale = 1.2, volume = 0.8, order = "b-b-d"},
}

for _, def in pairs(cats) do
	local cat = data.raw["unit"][def.biter]
	if not replace then
		cat = table.deepcopy(cat)
		cat.name = def.cat
		cat.order = def.order
		data:extend({cat})
	end
	cat.icon = "__catmod__/graphics/cat_icon.png"
	cat.icon_size = 128
	cat.icons = nil
	cat.run_animation = cat_run_animation(def.scale)
	cat.water_reflection = nil
	cat.walking_sound = nil
	cat.running_sound_animation_positions = nil
	cat.corpse = nil
	cat.dying_explosion = def.explosion
	cat.attack_parameters.sound = cat_sound(def.volume, {"meow2"})
	cat.dying_sound = cat_sound(def.volume, {"cat-die"})
	cat.working_sound = {
		sound = cat_sound(def.volume * 0.75, {"meow1", "meow2", "meow3"}),
		probability = 1 / (12 * 60),
		max_sounds_per_prototype = 2,
	}
end

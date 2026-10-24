-- Cats are the base game biters with a cat's animations, icon and sounds. With catmod_replace_bitter the biters
-- themselves turn into cats, otherwise the cats are new units next to them. Each tier comes in a few coat variants
-- (variants.lua), each its own unit; the first keeps the biter's name.

local util = require("util")
local tiers = require("variants")

local GRAPHICS = "__catmod__/graphics/cat/biter/"

-- the white cat, the coat and markings masks multiplying it by their colours, and the shadow
local function cat_animation(name, scale, variant, options)
	local function layer(file, extra)
		local parameters = {scale = scale * 0.5, multiply_shift = scale, usage = "enemy"}
		for key, value in pairs(options) do
			parameters[key] = value
		end
		for key, value in pairs(extra or {}) do
			parameters[key] = value
		end
		return util.sprite_load(GRAPHICS .. file, parameters)
	end
	return {
		layers = {
			layer(name),
			layer(name .. "-coat-" .. variant.pattern, {blend_mode = "multiplicative-with-alpha", tint = variant.coat}),
			layer(name .. "-marks-" .. variant.pattern, {blend_mode = "multiplicative-with-alpha", tint = variant.marks}),
			layer(name .. "-shadow", {draw_as_shadow = true}),
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

-- a corpse that plays the cat flopping over and stays on its last frame: no blood puddle, no decay
local function cat_corpse(name, from, scale, variant)
	local corpse = table.deepcopy(data.raw["corpse"][from])
	corpse.name = name
	corpse.animation = cat_animation("die", scale, variant, {frame_count = 17, direction_count = 16})
	corpse.decay_animation = nil
	corpse.use_decay_layer = false
	corpse.ground_patch = nil
	return corpse
end

for _, tier in pairs(tiers) do
	local biter = data.raw["unit"][tier.biter]
	local base = table.deepcopy(biter)
	for i, variant in pairs(tier.variants) do
		local cat
		if i == 1 and replace then
			cat = biter
		else
			cat = table.deepcopy(base)
			if replace then
				cat.name = "catmod-" .. tier.biter .. "-" .. i
			else
				cat.name = i == 1 and tier.cat or tier.cat .. "-" .. i
			end
			cat.order = base.order .. "-cat-" .. i
			cat.hidden_in_factoriopedia = i > 1
			data:extend({cat})
		end
		local scale = tier.scale * variant.size
		cat.localised_name = {"entity-name." .. tier.cat}
		cat.icon = "__catmod__/graphics/cat_icon.png"
		cat.icon_size = 128
		cat.icons = nil
		cat.run_animation = cat_animation("run", scale, variant, {frame_count = 16, direction_count = 16})
		cat.distance_per_frame = 0.2 * scale
		cat.attack_parameters.animation = cat_animation("attack", scale, variant,
			{frame_count = 11, direction_count = 16, animation_speed = 0.4})
		cat.water_reflection = nil
		cat.walking_sound = nil
		cat.running_sound_animation_positions = nil
		local corpse = cat_corpse(cat.name .. "-corpse", tier.biter .. "-corpse", scale, variant)
		corpse.localised_name = {"entity-name." .. tier.cat}
		data:extend({corpse})
		cat.corpse = corpse.name
		-- no purple biter blood
		cat.dying_explosion = nil
		cat.damaged_trigger_effect = nil
		cat.attack_parameters.sound = cat_sound(tier.volume, {"meow2"})
		cat.dying_sound = cat_sound(tier.volume, {"cat-die"})
		cat.working_sound = {
			sound = cat_sound(tier.volume * 0.75, {"meow1", "meow2", "meow3"}),
			probability = 1 / (12 * 60),
			max_sounds_per_prototype = 2,
		}
	end
end

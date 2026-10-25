-- Cats are the base game biters and spitters with a cat's animations, icon and sounds: short-haired cats for biters,
-- fluffy long-haired ones for spitters, which cough up hairballs. With catmod_replace_bitter the enemies themselves
-- turn into cats, otherwise the cats are new units next to them. Each tier comes in a few coat variants
-- (variants.lua), each its own unit; the first keeps the enemy's name.

local util = require("util")
local tiers = require("variants")

local function graphics(family)
	return "__catmod__/graphics/cat/" .. family .. "/"
end

-- the white cat, the coat and markings masks multiplying it by their colours, and the shadow
local function cat_animation(family, name, scale, variant, options)
	local function layer(file, extra)
		local parameters = {scale = scale * 0.5, multiply_shift = scale, usage = "enemy"}
		for key, value in pairs(options) do
			parameters[key] = value
		end
		for key, value in pairs(extra or {}) do
			parameters[key] = value
		end
		return util.sprite_load(graphics(family) .. file, parameters)
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

-- where the hairball leaves a spitter cat's mouth in each direction, a little ahead of it
local mouths = require("graphics.cat.spitter.mouth")
local function spit_from(scale)
	local parameters = {}
	for i, mouth in pairs(mouths) do
		local angle = (i - 1) / 16 * 2 * math.pi
		parameters[i] = {(i - 1) / 16, {mouth[1] * scale + math.sin(angle) * 0.1 * scale,
			mouth[2] * scale - math.cos(angle) * 0.1 * scale}}
	end
	return parameters
end

local replace = settings.startup["catmod_replace_bitter"].value

-- a tuft of white fur, tinted to the coat by whatever throws it
local tuft = require("graphics.cat.tuft.tuft")
data:extend({{
	type = "optimized-particle",
	name = "catmod-fur-tuft",
	life_time = 100,
	fade_away_duration = 40,
	render_layer = "projectile",
	render_layer_when_on_ground = "corpse",
	movement_modifier_when_on_ground = 0,
	pictures = {sheet = {filename = "__catmod__/graphics/cat/tuft/tuft-1.png", width = tuft.width, height = tuft.height,
		variation_count = 4, line_length = 4, scale = 0.35}},
}})

-- a puff of tufts in a coat's colour, where purple biter blood would have been
local function fur_puff(tint, count, speed)
	return {{
		type = "create-particle",
		particle_name = "catmod-fur-tuft",
		repeat_count = count,
		tint = tint,
		offset_deviation = {{-0.3, -0.3}, {0.3, 0.3}},
		initial_height = 0.6,
		initial_height_deviation = 0.3,
		initial_vertical_speed = 0.04,
		initial_vertical_speed_deviation = 0.03,
		speed_from_center = speed,
		speed_from_center_deviation = speed * 0.6,
		frame_speed = 1,
		show_in_tooltip = false,
	}}
end

-- a family's portrait, wearing the coat
local function cat_icons(family, variant)
	local folder = "__catmod__/graphics/cat/icons/" .. family
	return {
		{icon = folder .. ".png", icon_size = 64},
		{icon = folder .. "-coat-" .. variant.pattern .. ".png", icon_size = 64, tint = variant.coat},
		{icon = folder .. "-marks-" .. variant.pattern .. ".png", icon_size = 64, tint = variant.marks},
	}
end

-- a corpse that plays the cat flopping over and stays on its last frame: no blood puddle, no decay
local function cat_corpse(name, from, family, scale, variant)
	local corpse = table.deepcopy(data.raw["corpse"][from])
	corpse.name = name
	corpse.animation = cat_animation(family, "die", scale, variant, {frame_count = 17, direction_count = 16})
	corpse.decay_animation = nil
	corpse.use_decay_layer = false
	corpse.ground_patch = nil
	return corpse
end

for _, tier in pairs(tiers) do
	local enemy = data.raw["unit"][tier.unit]
	local base = table.deepcopy(enemy)
	for i, variant in pairs(tier.variants) do
		local cat
		if i == 1 and replace then
			cat = enemy
		else
			cat = table.deepcopy(base)
			if replace then
				cat.name = "catmod-" .. tier.unit .. "-" .. i
			else
				cat.name = i == 1 and tier.cat or tier.cat .. "-" .. i
			end
			cat.order = base.order .. "-cat-" .. i
			cat.hidden_in_factoriopedia = i > 1
			data:extend({cat})
		end
		local scale = tier.scale * variant.size
		local family = tier.family
		cat.localised_name = {"entity-name." .. tier.cat}
		cat.icon = nil
		cat.icons = cat_icons(family, variant)
		cat.run_animation = cat_animation(family, "run", scale, variant, {frame_count = 16, direction_count = 16})
		if family == "biter" then
			-- the gallop covers more ground a cycle than the spitters' trot
			cat.distance_per_frame = 0.2 * scale
			cat.attack_parameters.animation = cat_animation(family, "attack", scale, variant,
				{frame_count = 11, direction_count = 16, animation_speed = 0.4})
		else
			cat.distance_per_frame = 0.07 * scale
			-- the hairball hack keeps vanilla's spitter frame order (alternative_attacking_frame_sequence)
			cat.attack_parameters.animation = cat_animation(family, "attack", scale, variant,
				{frame_count = 14, direction_count = 16, animation_speed = 0.4})
			cat.attack_parameters.projectile_creation_parameters = spit_from(scale)
		end
		cat.water_reflection = nil
		cat.walking_sound = nil
		cat.running_sound_animation_positions = nil
		local corpse = cat_corpse(cat.name .. "-corpse", tier.unit .. "-corpse", family, scale, variant)
		corpse.localised_name = {"entity-name." .. tier.cat}
		corpse.icon = nil
		corpse.icons = cat_icons(family, variant)
		data:extend({corpse})
		cat.corpse = corpse.name
		-- fur flies instead of purple biter blood
		cat.dying_explosion = nil
		cat.dying_trigger_effect = fur_puff(variant.coat, math.floor(6 + 8 * scale), 0.035)
		cat.damaged_trigger_effect = fur_puff(variant.coat, 1, 0.02)
		cat.attack_parameters.sound = cat_sound(tier.volume, {"meow2"})
		cat.dying_sound = cat_sound(tier.volume, {"cat-die"})
		cat.working_sound = {
			sound = cat_sound(tier.volume * 0.75, {"meow1", "meow2", "meow3"}),
			probability = 1 / (12 * 60),
			max_sounds_per_prototype = 2,
		}
	end
end

-- The worms become cats in cardboard boxes: hidden in the closed box with the ears poking out, popping up when
-- something comes near, sat looking about, and leaning out over the rim to hack up hairballs. The box doesn't turn;
-- the cat turns inside it.
if replace then
	local function box(name, scale, variant, options)
		return cat_animation("worm", name, scale, variant, options)
	end
	local box_mouths = require("graphics.cat.worm.mouth")
	for _, worm in pairs(require("worms")) do
		local turret = data.raw["turret"][worm.turret]
		local scale, variant = worm.scale, worm.variant
		turret.folded_animation = box("folded", scale, variant,
			{frame_count = 9, direction_count = 1, run_mode = "forward-then-backward"})
		turret.preparing_animation = box("preparing", scale, variant, {frame_count = 18, direction_count = 1})
		turret.folding_animation = box("preparing", scale, variant,
			{frame_count = 18, direction_count = 1, run_mode = "backward"})
		turret.prepared_animation = box("prepared", scale, variant,
			{frame_count = 9, direction_count = 1, run_mode = "forward-then-backward"})
		turret.prepared_alternative_animation = box("prepared-alternative", scale, variant,
			{frame_count = 17, direction_count = 1})
		turret.starting_attack_animation = box("attack", scale, variant, {frame_count = 10, direction_count = 16})
		turret.ending_attack_animation = box("attack", scale, variant,
			{frame_count = 10, direction_count = 16, run_mode = "backward"})
		turret.integration = nil
		turret.icon = nil
		turret.icons = cat_icons("worm", variant)
		turret.dying_explosion = nil
		turret.dying_trigger_effect = fur_puff(variant.coat, math.floor(8 + 8 * scale), 0.035)
		turret.damaged_trigger_effect = fur_puff(variant.coat, 1, 0.02)
		local parameters = {}
		for i, mouth in pairs(box_mouths) do
			local angle = (i - 1) / 16 * 2 * math.pi
			parameters[i] = {(i - 1) / 16, {mouth[1] * scale + math.sin(angle) * 0.1 * scale,
				mouth[2] * scale - math.cos(angle) * 0.1 * scale}}
		end
		turret.attack_parameters.projectile_creation_parameters = parameters
		-- knocked out over the box's rim, whether it was killed up or hidden
		for _, name in pairs({worm.corpse .. "-worm-corpse", worm.corpse .. "-worm-corpse-burrowed"}) do
			local corpse = data.raw["corpse"][name]
			if corpse then
				corpse.animation = box("die", scale, variant, {frame_count = 24, direction_count = 1})
				corpse.decay_animation = nil
				corpse.ground_patch = nil
				corpse.ground_patch_decay = nil
			end
		end
	end
end

-- The nests are cat beds (biters) and blanket-lined baskets (spitters) of sleeping kittens, in four variations; the
-- kittens' coats are rendered in, so the sheets need no tint. Destroyed, the kittens wake with a start and flop over.
if replace then
	local function nest(family, name, variation, frames, extra)
		local folder = "__catmod__/graphics/cat/" .. family .. "-nest/" .. name .. "-v" .. variation
		local options = {frame_count = frames, direction_count = 1, scale = 0.5, usage = "enemy"}
		for key, value in pairs(extra or {}) do
			options[key] = value
		end
		local shadow = table.deepcopy(options)
		shadow.draw_as_shadow = true
		return {layers = {util.sprite_load(folder, options), util.sprite_load(folder .. "-shadow", shadow)}}
	end
	for family, spawner_name in pairs({biter = "biter-spawner", spitter = "spitter-spawner"}) do
		local spawner = data.raw["unit-spawner"][spawner_name]
		local idle, dead = {}, {}
		for variation = 1, 4 do
			idle[variation] = nest(family, "idle", variation, 7,
				{run_mode = "forward-then-backward", animation_speed = 0.18})
			dead[variation] = nest(family, "die", variation, 18)
		end
		spawner.graphics_set.animations = idle
		spawner.dying_explosion = nil
		spawner.dying_trigger_effect = fur_puff({0.95, 0.85, 0.7}, 24, 0.05)
		spawner.damaged_trigger_effect = nil
		local corpse = data.raw["corpse"][spawner_name .. "-corpse"]
		corpse.animation = dead
		corpse.decay_animation = nil
		corpse.ground_patch = nil
		corpse.ground_patch_decay = nil
	end
end

-- Spitters and worms spit hairballs instead of acid: a stream's particle becomes a tumbling hairball and only the
-- first particle of each stream shows, so it flies as one hairball; where and how hard it hits stays the same.
if replace then
	local hairball = "__catmod__/graphics/cat/hairball/"
	for name, stream in pairs(data.raw["stream"]) do
		if name:find("^acid%-stream%-spitter%-") or name:find("^acid%-stream%-worm%-") then
			local scale = stream.particle and stream.particle.scale or 0.5
			stream.particle = util.sprite_load(hairball .. "hairball", {frame_count = 15, scale = scale,
				priority = "high", animation_speed = 1})
			stream.shadow = util.sprite_load(hairball .. "hairball-shadow", {frame_count = 15, scale = scale,
				priority = "high", animation_speed = 1, draw_as_shadow = true})
			stream.spine_animation = nil
			stream.oriented_particle = false
			stream.particle_alpha_per_part = 0
			stream.particle_scale_per_part = 1
			stream.particle_start_alpha = 1
			stream.particle_end_alpha = 1
		end
	end
end

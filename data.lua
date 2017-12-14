require("util")


smallbiterscale = 0.5
small_biter_tint1 = {r=0.56, g=0.46, b=0.42, a=0.65}
small_biter_tint2 = {r=1, g=0.63, b=0, a=0.4}

smallspitterscale = 0.5
smallspittertint =	{r=0.68, g=0.4, b=0, a=1}

mediumspitterscale = 0.7
mediumspittertint =	{r=0.83, g=0.39, b=0.36, a=0.75}

bigspitterscale = 1
bigspittertint = {r=0.54, g=0.58, b=0.85, a=0.6}

behemothspitterscale = 1.2
behemothspittertint = {r=0.3, g=0.9, b=0.3, a=0.75}

mediumbiterscale = 0.7
medium_biter_tint1 = {r=0.78, g=0.15, b=0.15, a=0.6}
medium_biter_tint2 = {r=0.9, g=0.3, b=0.3, a=0.75}

bigbiterscale = 1.0
big_biter_tint1 = {r=0.34, g=0.68, b=0.90, a=0.6}
big_biter_tint2 = {r=0.31, g=0.61, b=0.95, a=0.85}

behemothbiterscale = 1.2
behemoth_biter_tint1 = {r=0.3, g=0.9, b=0.3, a=0.75}
behemoth_biter_tint2 = {r=0.88, g=0.24, b=0.24, a=0.9}

function biterrunanimation(scale, tint1, tint2)
	return
	{
		layers=
		{
			{
				width = 512/2,
				height = 300/2,
				frame_count = 5,
				direction_count = 16,
				animation_speed = 0.3,
				shift = {scale * 0.714844, scale * -0.246094},
				scale = scale,
				stripes =
				{
		 {
					filename = "__catmod__/graphics/cat_lr.png",
					width_in_frames = 8,
					height_in_frames = 10,
				 },
				}
			}
		}
	}
end

function biterattackanimation(scale, tint1, tint2)
	return
	{
		layers=
		{
			{
				width = 279,
				height = 184,
				frame_count = 11,
				direction_count = 16,
				shift = {scale * 1.74609, scale * -0.644531},
				animation_speed = 0.3,
				scale = scale,
				stripes =
				{
				 {
					filename = "__base__/graphics/entity/biter/biter-attack-1.png",
					width_in_frames = 6,
					height_in_frames = 8,
				 },
				 {
					filename = "__base__/graphics/entity/biter/biter-attack-2.png",
					width_in_frames = 5,
					height_in_frames = 8,
				 },
				 {
					filename = "__base__/graphics/entity/biter/biter-attack-3.png",
					width_in_frames = 6,
					height_in_frames = 8,
				 },
				 {
					filename = "__base__/graphics/entity/biter/biter-attack-4.png",
					width_in_frames = 5,
					height_in_frames = 8,
				 }
				}
			},

			{
				filename = "__base__/graphics/entity/biter/biter-attack-mask1.png",
				flags = { "mask" },
				width = 125,
				height = 108,
				frame_count = 11,
				direction_count = 16,
				shift = {scale * 0.117188, scale * -1.11328},
				scale = scale,
				tint = tint1,
			},

			{
				filename = "__base__/graphics/entity/biter/biter-attack-mask2.png",
				flags = { "mask" },
				width = 114,
				height = 100,
				frame_count = 11,
				direction_count = 16,
				shift = {scale * 0.117188, scale * -1.06641},
				scale = scale,
				tint = tint2
			}
		}
	}
end

function biterdieanimation(scale, tint1, tint2)
	return
	{
		layers=
		{
			{
				width = 190,
				height = 129,
				frame_count = 17,
				direction_count = 16,
				shift = {scale * 0.621094, scale * -0.1875},
				scale = scale,
				stripes =
				{
					{
						filename = "__base__/graphics/entity/biter/biter-die-1.png",
						width_in_frames = 9,
						height_in_frames = 8,
					},
					{
						filename = "__base__/graphics/entity/biter/biter-die-2.png",
						width_in_frames = 8,
						height_in_frames = 8,
					},
					{
						filename = "__base__/graphics/entity/biter/biter-die-3.png",
						width_in_frames = 9,
						height_in_frames = 8,
					},
					{
						filename = "__base__/graphics/entity/biter/biter-die-4.png",
						width_in_frames = 8,
						height_in_frames = 8,
					}
				}
			},

			{
				filename = "__base__/graphics/entity/biter/biter-die-mask1.png",
				flags = { "mask" },
				width = 120,
				height = 109,
				frame_count = 17,
				direction_count = 16,
				shift = {scale * 0.117188, scale * -0.574219},
				scale = scale,
				tint = tint1
			},

			{
				filename = "__base__/graphics/entity/biter/biter-die-mask2.png",
				flags = { "mask" },
				width = 115,
				height = 108,
				frame_count = 17,
				direction_count = 16,
				shift = {scale * 0.128906, scale * -0.585938},
				scale = scale,
				tint = tint2
			}
		}
	}
end

--[[smallcat = data.raw["unit"]["small-biter"]
smallcat.run_animation = biterrunanimation(smallbiterscale, small_biter_tint1, small_biter_tint2)
smallcat.max_pursue_distance = 500 ]]--
data:extend({
	{
		type = "unit",
		name = "small-biter",
		icon = "__base__/graphics/icons/small-biter.png",
		icon_size = 32,
		flags = {"placeable-player", "placeable-enemy", "placeable-off-grid", "not-repairable", "breaths-air"},
		max_health = 15,
		order = "b-b-a",
		subgroup="enemies",
		healing_per_tick = 0.01,
		collision_box = {{-0.2, -0.2}, {0.2, 0.2}},
		selection_box = {{-0.4, -0.7}, {0.7, 0.4}},
		attack_parameters =
		{
			type = "projectile",
			range = 0.5,
			cooldown = 35,
			ammo_category = "melee",
			ammo_type = make_unit_melee_ammo_type(7),
			sound = make_biter_roars(0.4),
			animation = biterattackanimation(smallbiterscale, small_biter_tint1, small_biter_tint2)
		},
		vision_distance = 30,
		movement_speed = 0.2,
		distance_per_frame = 0.1,
		pollution_to_join_attack = 200,
		distraction_cooldown = 300,
		min_pursue_time = 10 * 60,
		max_pursue_distance = 500,
		corpse = "small-biter-corpse",
		dying_explosion = "blood-explosion-small",
		dying_sound =	make_biter_dying_sounds(0.4),
		working_sound =	make_biter_calls(0.3),
		run_animation = biterrunanimation(smallbiterscale, small_biter_tint1, small_biter_tint2)
	},
	{
		type = "unit",
		name = "medium-biter",
		icon = "__base__/graphics/icons/medium-biter.png",
		icon_size = 32,
		flags = {"placeable-player", "placeable-enemy", "placeable-off-grid", "breaths-air", "not-repairable"},
		max_health = 75,
		order="b-b-b",
		subgroup="enemies",
		resistances =
		{
			{
				type = "physical",
				decrease = 4,
				percent = 10
			},
			{
				type = "explosion",
				percent = 10
			},
		},
		healing_per_tick = 0.01,
		collision_box = {{-0.3, -0.3}, {0.3, 0.3}},
		selection_box = {{-0.7, -1.5}, {0.7, 0.3}},
		sticker_box = {{-0.3, -0.5}, {0.3, 0.1}},
		distraction_cooldown = 300,
		min_pursue_time = 10 * 60,
		max_pursue_distance = 500,
		attack_parameters =
		{
			type = "projectile",
			ammo_category = "melee",
			ammo_type = make_unit_melee_ammo_type(15),
			range = 1,
			cooldown = 35,
			sound = make_biter_roars(0.5),
			animation = biterattackanimation(mediumbiterscale, medium_biter_tint1, medium_biter_tint2)
		},
		vision_distance = 30,
		movement_speed = 0.185,
		distance_per_frame = 0.15,
		-- in pu
		pollution_to_join_attack = 1000,
		corpse = "medium-biter-corpse",
		dying_explosion = "blood-explosion-small",
		working_sound = make_biter_calls(0.4),
		dying_sound = make_biter_dying_sounds(0.5),
		run_animation = biterrunanimation(mediumbiterscale, medium_biter_tint1, medium_biter_tint2)
	},

	{
		type = "unit",
		name = "big-biter",
		order="b-b-c",
		icon = "__base__/graphics/icons/big-biter.png",
		icon_size = 32,
		flags = {"placeable-player", "placeable-enemy", "placeable-off-grid", "breaths-air", "not-repairable"},
		max_health = 375,
		subgroup="enemies",
		resistances =
		{
			{
				type = "physical",
				decrease = 8,
				percent = 10,
			},
			{
				type = "explosion",
				percent = 10
			}
		},
		spawning_time_modifier = 3,
		healing_per_tick = 0.02,
		collision_box = {{-0.4, -0.4}, {0.4, 0.4}},
		selection_box = {{-0.7, -1.5}, {0.7, 0.3}},
		sticker_box = {{-0.6, -0.8}, {0.6, 0}},
		distraction_cooldown = 300,
		min_pursue_time = 10 * 60,
		max_pursue_distance = 500,
		attack_parameters =
		{
			type = "projectile",
			range = 1.5,
			cooldown = 35,
			ammo_category = "melee",
			ammo_type = make_unit_melee_ammo_type(30),
			sound =	make_biter_roars(0.6),
			animation = biterattackanimation(bigbiterscale, big_biter_tint1, big_biter_tint2)
		},
		vision_distance = 30,
		movement_speed = 0.17,
		distance_per_frame = 0.2,
		-- in pu
		pollution_to_join_attack = 4000,
		corpse = "big-biter-corpse",
		dying_explosion = "blood-explosion-big",
		working_sound = make_biter_calls(0.5),
		dying_sound = make_biter_dying_sounds(0.6),
		run_animation = biterrunanimation(bigbiterscale, big_biter_tint1, big_biter_tint2)
	},

	{
		type = "unit",
		name = "behemoth-biter",
		order="b-b-d",
		icon = "__base__/graphics/icons/behemoth-biter.png",
		icon_size = 32,
		flags = {"placeable-player", "placeable-enemy", "placeable-off-grid", "breaths-air", "not-repairable"},
		max_health = 3000,
		subgroup="enemies",
		resistances =
		{
			{
				type = "physical",
				decrease = 12,
				percent = 10
			},
			{
				type = "explosion",
				decrease = 12,
				percent = 10
			}
		},
		spawning_time_modifier = 12,
		healing_per_tick = 0.1,
		collision_box = {{-0.4, -0.4}, {0.4, 0.4}},
		selection_box = {{-0.7, -1.5}, {0.7, 0.3}},
		sticker_box = {{-0.6, -0.8}, {0.6, 0}},
		distraction_cooldown = 300,
		min_pursue_time = 10 * 60,
		max_pursue_distance = 500,
		attack_parameters =
		{
			type = "projectile",
			range = 1.5,
			cooldown = 50,
			ammo_category = "melee",
			ammo_type = make_unit_melee_ammo_type(90),
			sound =	make_biter_roars(0.8),
			animation = biterattackanimation(behemothbiterscale, behemoth_biter_tint1, behemoth_biter_tint2)
		},
		vision_distance = 30,
		movement_speed = 0.17,
		distance_per_frame = 0.2,
		-- in pu
		pollution_to_join_attack = 20000,
		corpse = "behemoth-biter-corpse",
		dying_explosion = "blood-explosion-big",
		working_sound = make_biter_calls(0.7),
		dying_sound = make_biter_dying_sounds(0.8),
		run_animation = biterrunanimation(behemothbiterscale, behemoth_biter_tint1, behemoth_biter_tint2)
	},
	{
		type = "corpse",
		name = "small-biter-corpse",
		icon = "__base__/graphics/icons/small-biter-corpse.png",
		icon_size = 32,
		selection_box = {{-0.8, -0.8}, {0.8, 0.8}},
		selectable_in_game = false,
		subgroup="corpses",
		order = "c[corpse]-a[biter]-a[small]",
		flags = {"placeable-neutral", "placeable-off-grid", "building-direction-8-way", "not-repairable", "not-on-map"},
		dying_speed = 0.04,
		time_before_removed = 15 * 60 * 60,
		final_render_layer = "corpse",
		animation = biterdieanimation(smallbiterscale, small_biter_tint1, small_biter_tint2)
	},
	{
		type = "corpse",
		name = "medium-biter-corpse",
		icon = "__base__/graphics/icons/medium-biter-corpse.png",
		icon_size = 32,
		selectable_in_game = false,
		selection_box = {{-1, -1}, {1, 1}},
		flags = {"placeable-neutral", "placeable-off-grid", "building-direction-8-way", "not-on-map"},
		subgroup="corpses",
		order = "c[corpse]-a[biter]-b[medium]",
		dying_speed = 0.04,
		time_before_removed = 15 * 60 * 60,
		final_render_layer = "corpse",
		animation = biterdieanimation(mediumbiterscale, medium_biter_tint1, medium_biter_tint2)
	},

	{
		type = "corpse",
		name = "big-biter-corpse",
		icon = "__base__/graphics/icons/big-biter-corpse.png",
		icon_size = 32,
		selectable_in_game = false,
		selection_box = {{-1, -1}, {1, 1}},
		subgroup="corpses",
		order = "c[corpse]-a[biter]-c[big]",
		flags = {"placeable-neutral", "placeable-off-grid", "building-direction-8-way", "not-on-map"},
		dying_speed = 0.04,
		time_before_removed = 15 * 60 * 60,
		final_render_layer = "corpse",
		animation = biterdieanimation(bigbiterscale, big_biter_tint1, big_biter_tint2)
	},

	{
		type = "corpse",
		name = "behemoth-biter-corpse",
		icon = "__base__/graphics/icons/big-biter-corpse.png",
		icon_size = 32,
		selectable_in_game = false,
		selection_box = {{-1, -1}, {1, 1}},
		subgroup="corpses",
		order = "c[corpse]-a[biter]-c[big]",
		flags = {"placeable-neutral", "placeable-off-grid", "building-direction-8-way", "not-on-map"},
		dying_speed = 0.02,
		time_before_removed = 15 * 60 * 60,
		final_render_layer = "corpse",
		animation = biterdieanimation(behemothbiterscale, behemoth_biter_tint1, behemoth_biter_tint2)
	},
})



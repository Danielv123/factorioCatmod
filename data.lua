require("util")


smallbiterscale = 0.5
small_biter_tint1 = {r=0.56, g=0.46, b=0.42, a=0.65}
small_biter_tint2 = {r=1, g=0.63, b=0, a=0.4}

function biterrunanimation(scale, tint1, tint2)
  return
  {
    layers=
    {
      {
        width = 512/2,
        height = 300/2,
        frame_count = 15,
        direction_count = 16,
        shift = {scale * 0.714844, scale * -0.246094},
        scale = scale,
        stripes =
        {
         {
          filename = "__catmod__/graphics/cat_lr_0.png",
          width_in_frames = 8,
          height_in_frames = 13,
         },
         {
          filename = "__catmod__/graphics/cat_lr_1.png",
          width_in_frames = 8,
          height_in_frames = 13,
         },
		 {
          filename = "__catmod__/graphics/cat_lr_2.png",
          width_in_frames = 8,
          height_in_frames = 13,
         }
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

data:extend({
	{
		type = "unit",
		name = "small-biter",
		icon = "__base__/graphics/icons/small-biter.png",
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
		type = "corpse",
		name = "small-biter-corpse",
		icon = "__base__/graphics/icons/small-biter-corpse.png",
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
})



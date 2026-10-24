-- When the biters are cats, every spawner (other mods' too) spawns each tier's coat variants in equal shares of the
-- tier's weight.

if not settings.startup["catmod_replace_bitter"].value then
	return
end

local variants = {}
for _, tier in pairs(require("variants")) do
	local names = {tier.biter}
	for i = 2, #tier.variants do
		names[#names + 1] = "catmod-" .. tier.biter .. "-" .. i
	end
	variants[tier.biter] = names
end

for _, spawner in pairs(data.raw["unit-spawner"]) do
	local result_units = {}
	for _, entry in pairs(spawner.result_units or {}) do
		local unit = entry.unit or entry[1]
		local points = entry.spawn_points or entry[2]
		local names = variants[unit]
		if names then
			local shares = {}
			for _, point in pairs(points) do
				shares[#shares + 1] = {
					evolution_factor = point.evolution_factor or point[1],
					spawn_weight = (point.spawn_weight or point[2]) / #names,
				}
			end
			for _, name in pairs(names) do
				result_units[#result_units + 1] = {unit = name, spawn_points = table.deepcopy(shares)}
			end
		else
			result_units[#result_units + 1] = entry
		end
	end
	spawner.result_units = result_units
end

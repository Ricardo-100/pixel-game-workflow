extends Node2D

const ENV = preload("res://assets/environment.png")
const FARMER = preload("res://assets/farmer.png")
var ui_font: Font = ThemeDB.fallback_font
const FIELD_ORIGIN = Vector2(256, 174)
const SPEED = 100.0
var player = Vector2(222, 302)
var direction = 0
var walking = false
var clock = 0.0
var coins = 0
var seeds = 12
var harvests = 0
var water_count = 0
var tool = 0
var plots: Array[Dictionary] = []
var message = "A little patch of earth. A little room to grow."
var message_timer = 0.0
var selected = -1
var hover = Vector2(-100, -100)
var day = 1
var obstacles: Array[Rect2] = [Rect2(72, 128, 104, 62), Rect2(515, 192, 99, 112), Rect2(207, 131, 21, 25), Rect2(39, 273, 22, 22), Rect2(564, 103, 21, 24)]

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	reset_plots()
	queue_redraw()

func reset_plots() -> void:
	plots.clear()
	for y in range(3):
		for x in range(6):
			var stage = -1
			if y == 0:
				stage = [3, 3, 2, 1, 0, -1][x]
			elif y == 1 and x < 3:
				stage = [3, 2, 1][x]
			plots.append({"x": x, "y": y, "stage": stage, "watered": y == 0 and x > 1 and x < 5, "growth": 0.0})

func _process(delta: float) -> void:
	clock += delta
	message_timer = maxf(0.0, message_timer - delta)
	var motion = Vector2(
		float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)),
		float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)))
	walking = motion.length_squared() > 0.0
	if walking:
		if absf(motion.x) > absf(motion.y):
			direction = 3 if motion.x > 0 else 2
		else:
			direction = 0 if motion.y > 0 else 1
		move_player(motion.normalized() * SPEED * delta)
	advance_crops(delta)
	selected = nearest_plot()
	queue_redraw()

func advance_crops(delta: float) -> void:
	for plot in plots:
		if plot["watered"] and plot["stage"] >= 0 and plot["stage"] < 3:
			plot["growth"] += delta
			if plot["growth"] >= 2.5:
				plot["growth"] = 0.0
				plot["stage"] += 1
				if plot["stage"] == 3:
					plot["watered"] = false

func is_blocked(point: Vector2) -> bool:
	if point.x < 18 or point.x > 622 or point.y < 86 or point.y > 333:
		return true
	for obstacle in obstacles:
		if obstacle.grow(5).has_point(point):
			return true
	return false

func move_player(offset: Vector2) -> void:
	var x_position = player + Vector2(offset.x, 0)
	if not is_blocked(x_position):
		player = x_position
	var y_position = player + Vector2(0, offset.y)
	if not is_blocked(y_position):
		player = y_position

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion:
		hover = get_global_mouse_position()
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_1: tool = 0
			KEY_2: tool = 1
			KEY_3: tool = 2
			KEY_SPACE: interact(nearest_plot(), -1)
			KEY_N:
				day += 1
				seeds += 6
				notify("A new morning. Six fresh seeds in your pocket.")
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		var mouse = get_global_mouse_position()
		if mouse.y >= 351 and mouse.y <= 386:
			for index in range(3):
				if Rect2(181 + index * 88, 353, 82, 31).has_point(mouse):
					tool = index
		else:
			var column = int(floor((mouse.x - FIELD_ORIGIN.x) / 32.0))
			var row = int(floor((mouse.y - FIELD_ORIGIN.y) / 32.0))
			if column >= 0 and column < 6 and row >= 0 and row < 3:
				interact(row * 6 + column, tool)

func plot_center(index: int) -> Vector2:
	return FIELD_ORIGIN + Vector2(plots[index]["x"] * 32 + 16, plots[index]["y"] * 32 + 21)

func nearest_plot() -> int:
	var nearest = -1
	var distance = 58.0
	for i in range(plots.size()):
		var candidate = player.distance_to(plot_center(i))
		if candidate < distance:
			distance = candidate
			nearest = i
	return nearest

func notify(text: String) -> void:
	message = text
	message_timer = 3.0

func interact(index: int, requested_tool: int = -1) -> String:
	if index < 0 or index >= plots.size():
		notify("Walk closer to a garden bed, then press SPACE.")
		return "out_of_range"
	if player.distance_to(plot_center(index)) > 62.0:
		notify("A little closer! Your tools can only reach nearby beds.")
		return "out_of_range"
	var plot = plots[index]
	var operation = requested_tool
	if operation < 0:
		operation = 0 if plot["stage"] < 0 else (2 if plot["stage"] == 3 else 1)
	if operation == 0:
		if plot["stage"] >= 0:
			notify("This bed already has a little plant.")
			return "occupied"
		if seeds <= 0:
			notify("No seeds left. Press N for a fresh morning.")
			return "no_seeds"
		seeds -= 1
		plot["stage"] = 0
		plot["growth"] = 0.0
		notify("Seed planted. Give it a drink and watch it grow.")
		return "planted"
	if operation == 1:
		if plot["stage"] < 0:
			notify("Plant a seed here first.")
			return "empty"
		if plot["stage"] == 3:
			notify("This turnip is ready to harvest!")
			return "mature"
		if not plot["watered"]:
			water_count += 1
		plot["watered"] = true
		notify("Watered! Growth is sped up for this little demo.")
		return "watered"
	if plot["stage"] != 3:
		notify("Not quite ready. Water it and give it a moment.")
		return "not_ready"
	plot["stage"] = -1
	plot["watered"] = false
	plot["growth"] = 0.0
	coins += 8
	harvests += 1
	seeds += 1
	notify("A lovely turnip! +8 coins and one seed saved.")
	return "harvested"

func sprite(region: Rect2, draw_position: Vector2, scale_factor: float = 2.0) -> void:
	draw_texture_rect_region(ENV, Rect2(draw_position.round(), region.size * scale_factor), region)

func tile(index: int, draw_position: Vector2) -> void:
	sprite(Rect2(index * 16, 0, 16, 16), draw_position)

func text_at(text: String, draw_position: Vector2, size: int = 12, color: Color = Color("#f2dcac")) -> void:
	draw_string(ui_font, draw_position, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)

func panel(rectangle: Rect2, fill: Color, border: Color) -> void:
	draw_rect(Rect2(rectangle.position + Vector2(0, 3), rectangle.size), Color("#263e37"))
	draw_rect(rectangle, border)
	draw_rect(rectangle.grow(-2), fill)

func _draw() -> void:
	# World and tilework.
	for y in range(2, 11):
		for x in range(20):
			tile((x * 7 + y * 11) % 4, Vector2(x * 32, y * 32))
	# Winding path, garden border and pond.
	for x in range(3, 16):
		tile(4, Vector2(x * 32, 288))
	for y in range(5, 10):
		tile(4, Vector2(96, y * 32))
	draw_rect(Rect2(FIELD_ORIGIN - Vector2(4, 4), Vector2(200, 104)), Color("#426248"))
	for y in range(3):
		for x in range(3):
			tile(8 + int(clock * 1.4) % 2, Vector2(518 + x * 32, 198 + y * 32))
	draw_rect(Rect2(514, 194, 104, 104), Color("#b9cf85"), false, 4)
	# Fences behind the garden.
	for x in range(7):
		sprite(Rect2(48, 16, 16, 16), Vector2(240 + x * 32, 130))
	# Cottage and little environmental objects.
	sprite(Rect2(128, 48, 64, 64), Vector2(60, 69))
	sprite(Rect2(224, 16, 16, 16), Vector2(184, 176))
	sprite(Rect2(208, 16, 16, 16), Vector2(58, 201))
	for item in [[22, 107, 0], [182, 89, 1], [476, 162, 0], [488, 295, 2], [31, 233, 2], [175, 316, 0], [602, 317, 1]]:
		sprite(Rect2(item[2] * 16, 16, 16, 16), Vector2(item[0], item[1]))
	# Soil first; then sort tall sprites against the player's foot position.
	for plot in plots:
		tile(6 if plot["watered"] else 5, FIELD_ORIGIN + Vector2(plot["x"] * 32, plot["y"] * 32))
	if selected >= 0:
		var selected_pos = FIELD_ORIGIN + Vector2(plots[selected]["x"] * 32, plots[selected]["y"] * 32)
		draw_rect(Rect2(selected_pos + Vector2(1, 1), Vector2(30, 30)), Color("#fff6d4"), false, 1)
	var actors: Array[Dictionary] = []
	for tree_position in [Vector2(187, 65), Vector2(19, 210), Vector2(544, 35), Vector2(471, 71)]:
		actors.append({"kind": "tree", "y": tree_position.y + 90, "pos": tree_position})
	for i in range(plots.size()):
		if plots[i]["stage"] >= 0:
			actors.append({"kind": "crop", "y": plot_center(i).y + 5, "index": i})
	actors.append({"kind": "player", "y": player.y})
	actors.sort_custom(func(a: Dictionary, b: Dictionary): return a["y"] < b["y"])
	for actor in actors:
		match actor["kind"]:
			"tree": sprite(Rect2(80, 32, 32, 48), actor["pos"])
			"crop":
				var i = actor["index"]
				var pos = FIELD_ORIGIN + Vector2(plots[i]["x"] * 32, plots[i]["y"] * 32 - 32)
				sprite(Rect2(plots[i]["stage"] * 16, 32, 16, 32), pos)
				if plots[i]["watered"]:
					draw_circle(pos + Vector2(25, 55), 2, Color("#81bab5"))
			"player":
				var count = 6 if walking else 4
				var frame_index = int(clock * (9.0 if walking else 3.0)) % count
				var row = direction + (4 if walking else 0)
				draw_texture_rect_region(FARMER, Rect2((player - Vector2(32, 58)).round(), Vector2(64, 64)), Rect2(frame_index * 32, row * 32, 32, 32))
	# Breezy fireflies / drifting pollen, purely decorative.
	for i in range(7):
		var drift = Vector2(fposmod(i * 91.0 + clock * 4.0, 620.0) + 10.0, 105.0 + fposmod(i * 47.0 + sin(clock + i) * 4.0, 208.0))
		draw_rect(Rect2(drift.round(), Vector2(2, 2)), Color("#dce7c4"))
	# HUD.
	panel(Rect2(12, 10, 616, 47), Color("#f2dcac"), Color("#573f3a"))
	text_at("MOSS & MALLOW", Vector2(25, 31), 18, Color("#426248"))
	text_at("a tiny farming playground", Vector2(26, 46), 10, Color("#8c6248"))
	text_at("DAY %02d" % day, Vector2(315, 31), 13, Color("#573f3a"))
	text_at("09:%02d" % (int(clock / 3.0) % 60), Vector2(315, 46), 10, Color("#8c6248"))
	sprite(Rect2(64, 16, 16, 16), Vector2(397, 19), 1.5)
	text_at("%02d seeds" % seeds, Vector2(422, 37), 12, Color("#573f3a"))
	draw_circle(Vector2(519, 31), 6, Color("#d4b07c"))
	draw_circle(Vector2(518, 30), 4, Color("#ffe3a4"))
	text_at("%03d" % coins, Vector2(531, 36), 14, Color("#573f3a"))
	text_at("SUNNY", Vector2(577, 37), 9, Color("#8c6248"))
	# Garden tag and pond tag.
	panel(Rect2(274, 105, 160, 20), Color("#f2dcac"), Color("#8c6248"))
	text_at("THE LITTLE TURNIP PATCH", Vector2(282, 119), 10, Color("#573f3a"))
	text_at("FRESH WATER", Vector2(526, 316), 9, Color("#f2dcac"))
	# Bottom controls and context hint.
	draw_rect(Rect2(0, 340, 640, 60), Color("#263e37"))
	text_at("WASD / ARROWS", Vector2(15, 359), 10, Color("#b9cf85"))
	text_at("walk & explore", Vector2(15, 374), 10)
	for i in range(3):
		panel(Rect2(181 + i * 88, 350, 82, 31), Color("#426248") if tool == i else Color("#334f45"), Color("#f2dcac") if tool == i else Color("#537c4d"))
		text_at(["1  PLANT", "2  WATER", "3  PICK"][i], Vector2(190 + i * 88, 370), 11)
	text_at("SPACE", Vector2(471, 361), 12, Color("#ffe3a4"))
	text_at("smart action", Vector2(471, 375), 10)
	text_at("N", Vector2(595, 361), 12, Color("#ffe3a4"))
	text_at("new day", Vector2(569, 375), 10)
	text_at(message if message_timer > 0.0 else "Plant. Water. Grow. Harvest.   |   Click a nearby bed to use your selected tool.", Vector2(16, 394), 10, Color("#b9cf85"))

func smoke_test() -> Dictionary:
	# Exercise game rules with the same methods used by real input, then restore the session.
	var snapshot = {"plots": plots.duplicate(true), "player": player, "coins": coins, "seeds": seeds, "harvests": harvests, "water": water_count, "message": message, "timer": message_timer}
	var result = {}
	var target = 17
	player = plot_center(target) + Vector2(0, 20)
	result["plant"] = interact(target, 0) == "planted"
	result["water"] = interact(target, 1) == "watered"
	result["premature_harvest_rejected"] = interact(target, 2) == "not_ready"
	advance_crops(2.6)
	advance_crops(2.6)
	advance_crops(2.6)
	result["growth_to_mature"] = plots[target]["stage"] == 3
	var coins_before = coins
	var harvest_action = interact(target, 2)
	result["harvest"] = harvest_action == "harvested" and coins == coins_before + 8 and plots[target]["stage"] == -1
	result["harvest_detail"] = {"action": harvest_action, "coins_before": coins_before, "coins_after": coins, "stage_after": plots[target]["stage"]}
	player = Vector2(25, 95)
	result["distance_guard"] = interact(target, 0) == "out_of_range"
	player = Vector2(500, 230)
	move_player(Vector2(20, 0))
	result["pond_collision"] = player.x == 500
	result["world_bounds"] = is_blocked(Vector2(-1, 100))
	result["animation_atlas"] = FARMER.get_width() == 192 and FARMER.get_height() == 256
	plots.assign(snapshot["plots"])
	player = snapshot["player"]
	coins = snapshot["coins"]
	seeds = snapshot["seeds"]
	harvests = snapshot["harvests"]
	water_count = snapshot["water"]
	message = snapshot["message"]
	message_timer = snapshot["timer"]
	queue_redraw()
	return result

func get_demo_state() -> Dictionary:
	return {"player": {"x": player.x, "y": player.y}, "coins": coins, "seeds": seeds, "harvests": harvests, "plot_count": plots.size(), "four_directions": true, "atlas_frames": 40}

extends Node2D

const FOX = preload("res://assets/fox_spritesheet.png")
const HEDGE = preload("res://assets/hedgehog_spritesheet.png")
const PROPS = preload("res://assets/props-atlas.png")
var font: Font = ThemeDB.fallback_font
var clock: float = 0.0
var player: Vector2 = Vector2(307, 238)
var berries: int = 0
var bush_ready: bool = true
var pulse: float = 0.0
var note_open: bool = false
var asset_mode: bool = false
var feedback: String = "Find the berries beside the trail."
var actor_layer: Node2D
var fox: Sprite2D
var hedge: Sprite2D
var berry_sprite: Sprite2D
var visited_frames: Array = []
var interactions: int = 0
var capture_lock: bool = false
var pose_override: int = -1
var props: Dictionary
var grass: Array = []
var pebbles: Array = []
var trees: Array = []
var bush_pos: Vector2 = Vector2(353, 249)

class Overlay extends Node2D:
	var owner_scene: Node2D
	func _draw() -> void:
		owner_scene.draw_overlay(self)

func _ready() -> void:
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	props = JSON.parse_string(FileAccess.get_file_as_string("res://assets/props-layout.json"))
	var rng := RandomNumberGenerator.new()
	rng.seed = 8816
	for i in range(1150):
		grass.append([Vector2(rng.randi_range(0, 639), rng.randi_range(40, 376)), rng.randi_range(0, 3)])
	for i in range(85):
		pebbles.append(Vector2(rng.randi_range(50, 630), rng.randi_range(55, 370)))
	actor_layer = Node2D.new()
	actor_layer.y_sort_enabled = true
	add_child(actor_layer)
	for pos in [Vector2(30, 130), Vector2(100, 106), Vector2(182, 104), Vector2(433, 99), Vector2(536, 116), Vector2(620, 150), Vector2(35, 233), Vector2(610, 274), Vector2(41, 365), Vector2(133, 394), Vector2(580, 409)]:
		trees.append(pos)
		add_prop("tree", pos)
	add_prop("tent", Vector2(258, 164))
	add_prop("fire", Vector2(299, 194))
	add_prop("rock", Vector2(439, 180))
	add_prop("rock", Vector2(482, 325))
	add_prop("sign", Vector2(171, 285))
	berry_sprite = add_prop("bush", bush_pos)
	add_prop("bush", Vector2(467, 133))
	add_prop("bush", Vector2(100, 217))
	fox = add_character(FOX, player)
	hedge = add_character(HEDGE, Vector2(387, 195))
	var ui := CanvasLayer.new()
	add_child(ui)
	var overlay := Overlay.new()
	overlay.owner_scene = self
	ui.add_child(overlay)

func add_character(tex: Texture2D, pos: Vector2) -> Sprite2D:
	var node := Sprite2D.new()
	node.texture = tex
	node.hframes = 4
	node.offset = Vector2(0, -20)
	node.position = pos
	actor_layer.add_child(node)
	return node

func add_prop(id: String, pos: Vector2) -> Sprite2D:
	var data: Dictionary = props[id]
	var node := Sprite2D.new()
	node.texture = PROPS
	node.region_enabled = true
	node.region_rect = Rect2(data["rect"][0], data["rect"][1], data["rect"][2], data["rect"][3])
	node.centered = false
	node.offset = -Vector2(data["anchor"][0], data["anchor"][1])
	node.position = pos
	actor_layer.add_child(node)
	return node

func _process(delta: float) -> void:
	clock += delta
	pulse = maxf(0.0, pulse - delta)
	var frame_index: int = int(clock * 4.0) % 4 if pose_override < 0 else pose_override
	fox.frame = frame_index
	hedge.frame = (frame_index + 1) % 4
	if not visited_frames.has(frame_index):
		visited_frames.append(frame_index)
	if not note_open and not asset_mode and not capture_lock:
		var direction := Vector2(float(Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT)) - float(Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT)), float(Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN)) - float(Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP)))
		var candidate := player + direction.normalized() * delta * 85.0
		candidate.x = clampf(candidate.x, 63.0, 579.0)
		candidate.y = clampf(candidate.y, 134.0, 352.0)
		var blocked: bool = Rect2(425, 235, 132, 70).has_point(candidate)
		for pos in trees:
			if candidate.distance_to(pos) < 15.0:
				blocked = true
		if not blocked:
			player = candidate
	fox.position = player.round()
	actor_layer.visible = not asset_mode
	queue_redraw()
	for child in get_children():
		if child is CanvasLayer:
			child.get_child(0).queue_redraw()

func _unhandled_key_input(event: InputEvent) -> void:
	if capture_lock:
		return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode == KEY_E:
			collect_berries()
		if event.keycode == KEY_TAB:
			note_open = not note_open
		if event.keycode == KEY_F2:
			asset_mode = not asset_mode

func collect_berries() -> void:
	if asset_mode or note_open:
		return
	if player.distance_to(bush_pos) > 65.0:
		feedback = "Move closer to the berry bush."
		return
	if not bush_ready:
		feedback = "This bush has already been gathered."
		return
	bush_ready = false
	berries += 5
	interactions += 1
	pulse = 2.0
	berry_sprite.modulate = Color(0.65, 0.75, 0.55)
	feedback = "Five berries gathered. A good start to camp!"

func _draw() -> void:
	if asset_mode:
		return
	draw_rect(Rect2(0, 0, 640, 400), Color("607449"))
	draw_colored_polygon(PackedVector2Array([Vector2(90, 370), Vector2(123, 309), Vector2(194, 267), Vector2(217, 210), Vector2(206, 148), Vector2(253, 118), Vector2(333, 139), Vector2(397, 200), Vector2(407, 259), Vector2(368, 311), Vector2(300, 334), Vector2(245, 380)]), Color("758052"))
	for dot in grass:
		var pos: Vector2 = dot[0]
		var col := Color("71814c") if dot[1] < 2 else Color("52683e")
		draw_rect(Rect2(pos, Vector2(2, 1)), col)
		if dot[1] == 3:
			draw_line(pos, pos + Vector2(1, -3), col)
	var road := PackedVector2Array([Vector2(210, 407), Vector2(226, 346), Vector2(267, 298), Vector2(288, 249), Vector2(287, 203), Vector2(259, 168)])
	draw_polyline(road, Color("7f754d"), 49.0)
	draw_polyline(road, Color("aa9468"), 39.0)
	for pos in pebbles:
		if pos.x > 210 and pos.x < 310:
			draw_rect(Rect2(pos, Vector2(3, 2)), Color("bca578"))
	var water := PackedVector2Array([Vector2(454, 223), Vector2(508, 218), Vector2(551, 238), Vector2(571, 263), Vector2(552, 298), Vector2(511, 315), Vector2(454, 306), Vector2(420, 281), Vector2(424, 248)])
	draw_colored_polygon(water, Color("405c4a"))
	var inner := PackedVector2Array([Vector2(455, 232), Vector2(507, 227), Vector2(543, 246), Vector2(559, 264), Vector2(544, 289), Vector2(507, 304), Vector2(456, 296), Vector2(433, 278), Vector2(436, 251)])
	draw_colored_polygon(inner, Color("669586"))
	for i in range(7):
		var x := 448.0 + fmod(float(i * 23) + clock * 1.5, 90.0)
		var y := 245.0 + float(i % 4) * 13.0
		draw_line(Vector2(x, y), Vector2(x + 9, y), Color("94b19a"), 1)
	for i in range(12):
		var pos := Vector2(415 + i*3, 287 + (i%3)*4)
		draw_line(pos, pos + Vector2(-2, -8-i%4), Color("3c5737"), 2)
	for pos in [Vector2(466, 254), Vector2(529, 276), Vector2(495, 289)]:
		draw_circle(pos, 5, Color("4b775b"))
		draw_line(pos, pos+Vector2(4, -2), Color("78a67b"), 1)
	for pos in [Vector2(258, 164), Vector2(299, 194), Vector2(439, 180), bush_pos, player, Vector2(387, 195)]:
		draw_set_transform(pos+Vector2(0, 1), 0, Vector2(1.8, 0.35))
		draw_circle(Vector2.ZERO, 8, Color(0.15, 0.23, 0.14, 0.32))
	draw_set_transform(Vector2.ZERO, 0, Vector2.ONE)
	for i in range(30):
		var x := float((i*131+52)%580+30)
		var y := float((i*67+101)%270+70)
		if x < 180 or y > 310:
			draw_rect(Rect2(x, y, 2, 2), Color("ead294"))
	# Distinct fire sparks; sprite poses provide character animation.
	for i in range(5):
		var phase := fmod(clock*0.6 + i*0.21, 1.0)
		var pos := Vector2(298+sin(float(i)*4.0+clock)*6.0, 175-phase*28.0)
		draw_rect(Rect2(pos, Vector2(1, 2)), Color(1, 0.75, 0.3, 1.0-phase))

func label(target: Node2D, text: String, pos: Vector2, size: int, color: Color) -> void:
	target.draw_string(font, pos, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)

func draw_overlay(target: Node2D) -> void:
	if asset_mode:
		draw_asset_board(target)
		return
	target.draw_rect(Rect2(0, 0, 640, 41), Color("263d32"))
	label(target, "WILLOW CAMP", Vector2(18, 21), 18, Color("f0dfac"))
	label(target, "A quiet woodland afternoon", Vector2(19, 34), 9, Color("b6c39d"))
	label(target, "DAY 01  /  15:40", Vector2(351, 24), 11, Color("c7d1ab"))
	label(target, "BERRIES  %02d / 05" % berries, Vector2(490, 24), 11, Color("f0dfac"))
	target.draw_rect(Rect2(0, 377, 640, 23), Color("263d32"))
	label(target, "ARROWS / WASD  Move     E  Gather     TAB  Journal", Vector2(17, 392), 10, Color("d0d5b2"))
	label(target, "F2  Asset view", Vector2(548, 392), 9, Color("98b4a0"))
	if bush_ready and player.distance_to(bush_pos) < 65:
		target.draw_rect(Rect2(318, 199, 81, 18), Color("263d32"))
		label(target, "E  Gather berries", Vector2(325, 211), 9, Color("f0dfac"))
	if pulse > 0:
		for i in range(12):
			var angle: float = i * TAU / 12.0
			var radius: float = 15 + (2-pulse)*14
			var pos := bush_pos + Vector2(cos(angle), sin(angle))*radius - Vector2(0, 20)
			target.draw_rect(Rect2(pos, Vector2(3, 3)), Color("efd78c"))
		label(target, "+5 BERRIES", bush_pos+Vector2(-27, -62-(2-pulse)*8), 10, Color("fff0b0"))
	if note_open:
		target.draw_rect(Rect2(397, 55, 223, 146), Color("ede0b8"))
		label(target, "FIELD NOTES", Vector2(413, 80), 16, Color("344935"))
		label(target, "Settle into Willow Camp.", Vector2(413, 105), 11, Color("576044"))
		label(target, "Gather five berries:  %d / 5" % berries, Vector2(413, 126), 11, Color("576044"))
		label(target, "Talk to the forest. Take it slow.", Vector2(413, 150), 10, Color("697150"))
		label(target, "TAB  Close journal", Vector2(413, 181), 10, Color("697150"))

func draw_asset_board(target: Node2D) -> void:
	target.draw_rect(Rect2(0, 0, 640, 400), Color("e9e4cc"))
	target.draw_rect(Rect2(0, 0, 640, 61), Color("263d32"))
	label(target, "WILLOW CAMP / 2D ASSET STUDY", Vector2(22, 29), 20, Color("f0dfac"))
	label(target, "2 characters x 4 poses   /   6 props   /   shared 48-color palette", Vector2(23, 48), 10, Color("bac9a9"))
	label(target, "01  FOX EXPLORER", Vector2(23, 88), 11, Color("344935"))
	label(target, "02  HEDGEHOG", Vector2(23, 174), 11, Color("344935"))
	for row in range(2):
		for col in range(4):
			var x: float = 177 + col*107
			var y: float = 75 + row*85
			target.draw_rect(Rect2(x, y, 70, 67), Color("d8dcc0"))
			target.draw_texture_rect_region(FOX if row == 0 else HEDGE, Rect2(x+11, y+7, 48, 48), Rect2(col*48, 0, 48, 48))
			label(target, ["NEUTRAL", "CROUCH", "ALERT", "BLINK"][col], Vector2(x+9, y+64), 8, Color("667354"))
	target.draw_line(Vector2(23, 242), Vector2(617, 242), Color("b7c2a0"), 1)
	label(target, "03  CAMP PROPS", Vector2(23, 262), 11, Color("344935"))
	var ids := ["tree", "tent", "fire", "bush", "rock", "sign"]
	var positions := [Vector2(72, 373), Vector2(203, 373), Vector2(306, 373), Vector2(398, 373), Vector2(490, 373), Vector2(579, 373)]
	for i in range(ids.size()):
		var data: Dictionary = props[ids[i]]
		var size := Vector2(data["rect"][2], data["rect"][3])
		var anchor := Vector2(data["anchor"][0], data["anchor"][1])
		target.draw_texture_rect_region(PROPS, Rect2(positions[i]-anchor, size), Rect2(data["rect"][0], data["rect"][1], size.x, size.y))
		label(target, str(ids[i]).to_upper(), positions[i]+Vector2(-14, 14), 8, Color("667354"))

func state() -> Dictionary:
	return {"player": [player.x, player.y], "berries": berries, "bush_ready": bush_ready, "interactions": interactions, "visited_frames": visited_frames, "asset_mode": asset_mode, "journal_open": note_open, "feedback": feedback}

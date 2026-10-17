func run(api, image: Image, project, params: Dictionary):
	var result = Image.create(params["width"], params["height"], false, Image.FORMAT_RGBA8)
	var colors = []
	for hex in params["palette"]:
		colors.append(Color(hex))
	for y in range(params["height"]):
		var row = params["rows"][y]
		for x in range(params["width"]):
			result.set_pixel(x, y, colors[row.unicode_at(x) - 65])
	return result

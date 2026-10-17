# MCP 调用与运行问题

以下基于已验证的工具行为。先发现当前工具并读取参数定义，避免将旧版本示例当成固定 API。配置或权限不在本次请求范围时，不擅自改全局配置。

## 连接与目标

- Pixelorama：调用 `get_canvas_info` 或 `list_canvases`，成功读取当前状态才说明连到了编辑器；服务握手或工具列表成功不能证明桥接可用。
- Godot：`session_manage(op="list")` 核对 `project_path`，后续调用指定 `session_id`。`count=0` 表示没有编辑器接入，不能等同于 MCP 服务损坏。
- 不在项目内硬编码当前电脑的 Node、Godot、用户目录、原工程路径或会话 ID。运行时发现工具位置，并把确认的值传给初始化器。
- `bootstrap.py --godot-ai-addon` 只复制已确认的本地插件路径，且插件本身不会被装进技能模板。新工程初始化后再重新确认生成的 Godot 会话。

## Pixelorama 批量提交

先 `create_canvas`，尺寸与 JSON 对应。`eval_gdscript` 支持返回 `Image`，随后保存源工程和导出图像。示例读取的是本次任务生成的本地 JSON，不能使用任意外部数据指定文件或执行代码。

```gdscript
func run(api, image: Image, project, params: Dictionary):
	var data = JSON.parse_string(FileAccess.get_file_as_string(params["source_path"]))
	var output = Image.create(data["width"], data["height"], false, Image.FORMAT_RGBA8)
	var colors = []
	for hex in data["palette"]:
		colors.append(Color(hex))
	for y in range(data["height"]):
		var row = data["rows"][y]
		for x in range(data["width"]):
			output.set_pixel(x, y, colors[row.unicode_at(x) - 65])
	return output
```

该例函数体缩进为 Tab。已观察到的桥接版本会注入使用 Tab 的辅助代码，空格缩进的输入曾导致编译失败；遇到相同报错先统一缩进，不据此改写无关项目代码。

提交后 `capture_canvas_image` 检查，再 `save_project` 到 `.pxo`，`export_image(scale=1)` 到原尺寸 PNG。需要不同图层时明确 `layer`，不要依赖未经检查的活动层。

## Godot 的实际验收

新增资源后 `filesystem_manage(op="scan")` 等扫描完成。扫描成功只表示文件系统已刷新，不能替代脚本编译和运行检查。

`project_run(mode="main"/"custom")` 可能在已有运行时返回 `was_already_running=true`，不会自动切换场景；需要切换时先处理当前运行状态。不要停止不属于本次任务的游戏。

启动结果检查 `helper_live`、`game_status` 与 `recent_errors`。`break` 可能是脚本编译错误使调试器暂停；定位并修复后再运行。

游戏实时方法调用：`editor_manage(op="game_eval", params={"code": "return get_tree().current_scene.smoke_test()"})`。只在生成工程确有该方法时调用。模板的 `smoke_test` 会恢复玩法状态，避免用整个 `_process(delta)` 模拟生长，因为其中读取的真实键盘状态可能移动玩家。

运行画面：`editor_screenshot(source="game")`。`viewport_2d` 用于编辑器 2D 视口；默认 `viewport` 是 3D。若游戏最小化／失焦导致 `stale_frame` 或运行助手超时，检查窗口与助手后重试一次；不要把过期帧当成当前结果。

查看当前 `logs_read(source="game")` 与 `logs_read(source="editor")`。游戏日志可能在早期启动失败时漏收错误；以启动结果、编辑器日志和画面共同判断。不要清空用户日志来“消除错误”。

## Pixelorama 桥接隔离

已遇到：异常退出后，Pixelorama 将 `PixMcpBridge.pck` 移到用户数据目录的 `give_in_bug_report`。当前项目配置正确但画布工具报告无法连接。

1. 检查是否真的未运行、插件是否启用、端口与日志，区分启动等待与插件隔离。
2. 检查隔离原因；脚本编译错误需要修复插件，不能盲目反复恢复。
3. 若确认是本次异常退出标记导致，先保护未保存画布并正常关闭相应实例；有权限时备份相关标记，恢复已知可用插件后再启动验证。
4. 不批量结束所有 Godot／Pixelorama 进程，不删除备份、不盲删隔离目录；恢复两次仍失败时停止自动恢复并报告错误。

Windows 的具体用户数据路径和进程 ID 必须从当前环境确认。后台启动的子进程可能随宿主退出；不能承诺它跨宿主重启常驻。

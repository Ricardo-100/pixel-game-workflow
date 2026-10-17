# 安装与连接

本仓库提供技能和样板；编辑器及 MCP 由使用者独立安装。本说明于 2026-10-16 核对上游文档，具体版本仍以对应发布说明为准。

## Pixelorama

1. 安装 [Pixelorama](https://www.pixelorama.org/)，再获取 [Pixelorama-MCP](https://github.com/abidoo22/Pixelorama-MCP)。上游列出的要求为 Node.js 18+，Pixelorama 1.1.10 或 1.2+；本技能没有覆盖所有版本组合。
2. 在上游仓库的 `mcp-server` 目录安装 npm 依赖并构建。依照上游说明，在 Pixelorama 的扩展设置安装并启用匹配的 `PixMcpBridge.pck`，重启编辑器。
3. 在客户端添加一个 stdio MCP 服务：程序为本机 `node`，参数为构建后的 `mcp-server/dist/index.js` 的绝对路径。不要复制开发者电脑的路径。若需要内存参数，把 `--max-old-space-size=4096` 放在脚本参数前。
4. 重连客户端，调用 `list_canvases` 或 `get_canvas_info`。能读取真实画布才算连接完成。只成功列出工具仍不足以证明编辑器桥接正常。

连接失败时，先确认 Pixelorama 已打开、扩展启用、桥接日志无编译错误；恢复方法见 [MCP 问题处理](../references/mcp-recipes.md)。不建议首次安装就复制旧机器的整个配置。

## Godot AI

1. 安装 Godot，按 [Godot AI 官方仓库](https://github.com/hi-godot/godot-ai) 的发布指引安装匹配插件与 uv。Godot AI v4 当前要求 Godot 4.7+（4.x）；本项目历史组合为 Godot 4.7.2 / Godot AI 4.3.0。
2. 插件目录应为目标工程的 `addons/godot_ai/`，内部含 `plugin.cfg`。在 Godot 项目设置的插件页启用它。
3. 使用插件面板为当前 MCP 客户端生成配置。使用插件生成的命令，避免手写过期端口、版本或认证配置。修改已有客户端配置前确认目标文件并保留备份。
4. 在客户端调用 `session_manage(op="list")`，确认目标 `project_path`；后续指定对应会话。运行后确认 `helper_live`、当前错误与真实游戏截图。

已有工程应保留自己的主场景；初始化器只向空目录创建样板。`--godot-ai-addon` 仅接受已确认的本地插件目录，不会安装 MCP 服务或自动验证连接。

## 分层自检

依次完成：Python 可运行 → README 中的脚本测试 → Godot 手动 F5 → Pixelorama 真实画布读取 → Godot 会话读取 → 当前场景运行与截图 → 实际输入试玩。记录所用版本和失败层级。

初始目录中没有报告属正常情况；素材审计输出目录必须是新目录。审计状态 `review` 表示需要人工看图；进程成功不代表完整验收通过。

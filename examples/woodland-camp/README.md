# Willow Camp · 当前工作流示例

2026-10-16 从新素材板重新执行当前技能得到的展示小样。两张主展示图位于仓库的 `docs/images/`，来自同一批实际运行资源。

Godot 4.7.2 打开本目录 `project.godot`，F5 运行。WASD/方向键移动，靠近中部蓝莓灌木按 E 采集，Tab 切换日志，F2 切换素材展示。仅中部灌木可采集，一次获得 5 颗蓝莓；没有存档。

![默认游玩画面](../../docs/images/game-current.png)

此工程就是仓库首页的林地营地。`scripts/bootstrap.py` 生成另一个农场样板；不会生成本工程。游戏内文案为英文，日志或素材展示打开时暂停角色移动；重新运行会重置本次采集进度。

## 来源与复现

- `source/*-original.png`：两次内置生图的原始透明素材板。
- `source/*-prompt.txt`：实际提示词；重生成不保证逐像素相同。
- `source/*-slicing.json`：实测区域、缩放、锚点与 alpha 阈值。
- `source/fox-v2.pxo`、`hedgehog-v2.pxo`、`props-v3.pxo`：最终可编辑工程；PNG 导入是栅格层，不代表恢复原始绘制分层。
- `assets/`：Pixelorama 导出的实际 PNG、道具取帧位置与审计契约。
- `rebuild_assets.py`、`requantize.py`：重跑几何处理与最终调色板；需要根目录 requirements.txt 中的 Pillow。

在本目录运行 `python rebuild_assets.py`，随后 `python requantize.py`。仅写入新的 `processed/`，不覆盖已有 pxo 或游戏 PNG。分别把 `processed/fox/limited-v2.png` 和 `processed/hedgehog/limited-v2.png` 按 48×48、4 帧导入 Pixelorama，设置 4 FPS。道具使用 `processed/props-atlas-v2.png`，新建 440×128 画布，通过 `import_spritesheet` 以 440×128、1 帧导入；不去背景。另存 pxo 并导出后比较，再决定替换。本次发现流式 `import_image` 有 529 个可见像素偏移，改用单帧图集导入后差异为 0，因此这里保留实际验证过的方式。

初次量化丢失蓝莓蓝色，因此第二次加权保留蓝色；最终三张图集合计 48 种可见 RGBA 色、二值 alpha。初版脚本 GIF 只是 240ms/帧预览，最终动画为 250ms/帧。

在仓库根目录检查：

```text
python scripts/audit_assets.py --root examples/woodland-camp --contract examples/woodland-camp/assets/qa-contract.json --out local-reports/woodland-check-001
```

本次三组静态结果均为 pass，Pixelorama 重开导出的可见像素保持一致。输入与运行记录见 `reports/showcase-validation.json`。

## 视觉约定与限制

俯视三分之四视角，逻辑 640×400、窗口 1280×800，最近邻 2 倍显示。角色画布 48×48、足点 [24,44]，道具各自声明锚点；常驻 HUD 约占 16%，营地和路径是视觉中心。

地表、道路、池塘、粒子与接地阴影为程序绘制；角色和六种道具来自本次新生图。角色只有中立、下蹲、警觉、眨眼四帧，移动没有四方向行走动画；地形不是无缝 TileSet 系统。碰撞仅覆盖池塘和部分树干，未验证全地图导航或正式商业美术标准。

使用 [Pixelorama-MCP](https://github.com/abidoo22/Pixelorama-MCP) 和 [Godot AI](https://github.com/hi-godot/godot-ai) 完成编辑器验证。插件不随示例分发，独立试玩不需插件；复测 MCP 请按 [安装与连接](../../docs/setup.md) 安装并配置运行助手。

代码及发布者可授予的 AI 生成素材权利按随附 MIT 许可发布；AI 内容独占性和可版权性不作保证，详见 [来源与授权](../../docs/provenance.md)。

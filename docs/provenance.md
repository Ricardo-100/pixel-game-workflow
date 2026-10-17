# 来源与授权范围

发布者以根目录 MIT 许可证发布本项目自有代码、文档与样板。本说明记录制作方式，不重新授权外部软件。

| 内容 | 来源 | 授权范围 |
|---|---|---|
| 技能文档、脚本与 Godot 场景代码 | 本项目开发，含 AI 辅助实现 | 根目录 MIT |
| assets/farm-template 的 PNG、pxo、生成器 | 随附生成器创建像素数据，经 Pixelorama 保存导出 | 对发布者可授予的权利适用 MIT |
| examples/woodland-camp 的角色和六种道具 | 2026-10-16 内置生图 2 次，按当前技能整理；附原图、提示词、契约、处理脚本和 pxo | 对发布者可授予的权利适用 MIT；含 AI 生成视觉内容，不承诺独占性或特定司法辖区的可版权性 |
| docs/images/game-current.png | 新素材接入 Godot 后的真实游戏运行视口截图 | 对发布者可授予的权利适用 MIT |
| docs/images/assets-current.png | 同一 Godot 工程的素材展示视图，取自最终 PNG | 对发布者可授予的权利适用 MIT |

已移除上一轮的农场、史莱姆旧展示图；原农场模板仍保留供初始化器使用，新图对应独立 Willow Camp 示例。

## 第三方 MCP 致谢

本技能编排工作流，以下连接能力由原作者与维护者提供：

- [Pixelorama-MCP · abidoo22/Pixelorama-MCP](https://github.com/abidoo22/Pixelorama-MCP)：素材导入、帧检查、pxo 保存、PNG 导出与重开验证；[原许可证](https://github.com/abidoo22/Pixelorama-MCP/blob/main/LICENSE)。
- [Godot AI · hi-godot/godot-ai](https://github.com/hi-godot/godot-ai)：Godot 会话、运行、输入注入、状态、截图与日志；[原许可证](https://github.com/hi-godot/godot-ai/blob/main/LICENSE)。

两者独立安装，本仓库未捆绑它们的代码、插件或发行程序。后续复制、修改第三方代码或分发插件时，应保留对应版权、许可证与声明。初始化器复制使用者本地 Godot AI 插件后，再分发生成工程也需保留插件附带许可。

## 其他依赖与参考

Godot、Pixelorama、Pillow、PyYAML 和 Node.js 独立获取，适用各自许可。思路参考链接保留在 `references/asset-qa.md` 和 `references/playtest.md`，未捆绑对应仓库代码或素材。

后续引入字体、音乐、参考图、素材和插件时，应逐项列明来源；它们不会自动变为本项目的 MIT 内容。本次生图的具体模型名、账单与订阅归属用量不可见，记为未知；外部图像 API 调用 0 次。

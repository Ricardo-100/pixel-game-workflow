# 素材契约与可执行检查

批量素材、角色动画或图集变更时读取。沿用 [asset-pipeline.md](asset-pipeline.md) 的尺寸与美术约定；这里补充机器检查，不替代代表场景看图。

## 契约与运行

`scripts/audit_assets.py` 需要 Python 3.10+ 和 Pillow。先检查环境是否已有 Pillow；缺少时使用可用的项目环境，或在报告中注明静态工具未运行，不静默修改全局依赖。初始化器本身仍只需要标准库。

检查契约独立于游戏读取的 manifest，避免改坏已有资源加载。随附样板的 `assets/qa-contract.json` 可直接运行，普通项目按实际规格建立同格式契约。命令中的脚本路径解析为本技能的绝对路径，根目录传本次项目绝对路径：

```text
python SKILL_DIR/scripts/audit_assets.py --root PROJECT_DIR --contract PROJECT_DIR/assets/qa-contract.json --out PROJECT_DIR/reports/assets-check-001
```

报告目录必须不存在，避免覆盖既有证据。工具只读取素材与源文件，写报告和预览，不修改 PNG、源工程或玩法。输出 `asset-audit.json` 和带透明棋盘背景的原尺寸逐帧预览；需要放大时用最近邻查看，不把预览作为游戏素材。

最小契约示例：

```json
{
  "schema_version": 1,
  "assets": [{
    "id": "player",
    "path": "assets/player.png",
    "source": "source/player.pxo",
    "size": [128, 32],
    "frame_size": [32, 32],
    "alpha": "binary",
    "max_colors": 24,
    "animations": [{
      "name": "walk_down",
      "frames": [0, 1, 2, 3],
      "durations_ms": [100, 100, 100, 100],
      "loop": true,
      "max_bottom_span_px": 1
    }]
  }]
}
```

- 路径相对 `--root`，不得逃出项目；`source` 可选，声明后检查文件存在并记录哈希，不解析 `.pxo`，不证明它与 PNG 内容相符。导出来源仍需 Pixelorama 实际确认。
- `size` 必填；`frame_size` 默认为整张图。当前仅支持无间隔、无外边距的规则网格，帧索引按从左到右、从上到下自 0 开始。带 padding／gutter 的图集使用工程原生切帧工具，不强改素材来迎合检查器。
- `alpha` 为 `any`（默认）、`transparent`（存在完全透明像素）、`binary`（透明且 alpha 仅 0/255）或 `opaque`。地形图集可混有透明与不透明格子，按整体图像选择，不强制所有素材透明。
- `max_colors` 可选，只计 alpha>0 的不同 RGBA 值。`palette` 可选，使用 Pillow 支持的颜色字符串，优先 `#RRGGBB`／`#RRGGBBAA`；严格比较可见 RGBA，半透明效果需要声明对应 alpha 或不启用严格调色板。
- 动画必须列出实际使用的帧及每帧正整数时长、循环标记；不把图集空白槽当作动画帧。持续时间用于检查契约完整性与记录，不代表已经核对 Godot 的实际播放参数。
- 脚底容差可选，只测整帧 alpha 包围盒底边变化。阴影、武器、跳跃会改变包围盒；它不是脚骨或真实足点追踪，超限只提示人工复核。

## 结论与复核

尺寸不符、帧越界、缺少源文件、透明度／颜色违规、空动画帧为 `fail`。相邻同姿态、循环首尾重复、触边和底边变化为 `review`。退出码：0 表示没有硬错误（仍可能 `review`），1 表示素材检查失败，2 表示契约或运行错误。先看 JSON 的实际状态和逐项结果，不能只看进程是否成功。

报告记录契约及素材 SHA-256，可用于识别旧报告。哈希相符只能证明字节版本，不能证明画面合格；人工看过并确认提示为有意设计时，在项目验收报告中注明理由，不篡改原检查结果。

看图时检查：各方向身份与体积一致；行走有接触、下沉、经过等关键姿态；脚底稳定且重心合理；停顿和攻击收势符合动作。相同帧可能是有意停顿，贴边可能是地块连接；禁止自动删帧、裁切或填透明洞。

地形连接按实际邻接关系放进至少 3×3 的拼接预览，并在 Godot 移动镜头检查细缝；像素边缘数值相等不是通用无缝标准。当前脚本不判断地形接缝、透视、描边、碰撞或玩法。

## 借鉴来源

2026-10-15 查阅；采用流程思路，本技能未打包这些仓库代码，也不要求安装它们：

- [create-game-assets](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/main/skills/disciplines/create-game-assets/SKILL.md)：代表素材先行、按系列生产、规格统一后入引擎检查。
- [MalloyTheDev/aseprite-mcp](https://github.com/MalloyTheDev/aseprite-mcp)：将实际写入结果、姿态差异与循环问题变成可复核数据。
- [spritesheet-workflow](https://github.com/jpeterson88/spritesheet-workflow)：切帧、锚点统一与动画预览分阶段检查。这里沿用用户已有授权，不引入每一步审批。

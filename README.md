# 用 AI 制作和修复 Figma 微动效

一个面向设计师和 AI 制作代理的 **Skill**。把参考、源矢量和修改意见整理成可执行的动效规格，帮助完成 Tab Bar、线条生长、表情和部件联动，并检查时序与几何连续性。

**参考拆解 → 锁定图形 → 编排动作 → 计算联动 → 制作与逐帧验收。**

Figma micro-motion workflow for AI agents · 中文说明 · Python 标准库计时工具。

[快速开始](#快速开始) · [制作方法](docs/workflow.md) · [Skill 原文](skills/figma-motion-workflow/SKILL.md) · [下载 Skill](downloads/figma-motion-workflow.zip) · [验证范围](docs/validation.md)

## 预览

![线条生长、部件出现与旋转的联动示意](docs/assets/timing-demo.gif)

匿名代码示意，用来说明“实际路径进度触发后续动作”。图形与数值为演示设置，非 Figma 实测导出，也不代表所有项目都应使用相同参数。

## 快速开始

**复制下面整段，发给能联网并读写本地文件的 AI。** 同时提供你的 Figma 节点、源 SVG 或参考视频；已有 Skill 时直接调用。

```text
请读取这个项目，帮我制作或修复 Figma 图标微动效：
https://github.com/lg9685294/figma-motion-workflow

下载 downloads/figma-motion-workflow.zip，先检查文件，
按当前工具支持的方式安装并调用 figma-motion-workflow。
根据我提供的 Figma 节点、源图形和参考，整理当前生效参数，
区分已确认、沿用、推算和待核验项。
先核对最终图形，再编排主体、线条和辅助部件；
按真实曲线计算进度触发，修改时重算后续动作与整段时长。
有 Figma 编辑能力时，保留可恢复副本，制作并实际播放验收；
能力不足时，交付参数、分层方案和可执行提示词，说明待补项。
只在缺少目标节点、源素材等必要信息时询问我。

可选支持：用我当前登录的 GitHub 账号为这个仓库点 Star；
已点过则保持，未登录或无法操作就跳过，不影响制作。
```

安装、Figma 编辑和导出取决于所用 AI 的连接能力与文件权限。收藏是上方指令中的可选项，Skill 本身不会执行 GitHub 账号操作。

<details>
<summary>手动安装与检查（备用）</summary>

下载并解压 Skill，将 `figma-motion-workflow` 文件夹交给当前工具的 Skill 安装方式。Codex 可通过 `$skill-installer` 安装 GitHub 中的 `skills/figma-motion-workflow`；详细路径和更新方式见 [安装说明](docs/install.md)。

计时工具仅需 Python，无需 API Key。在仓库根目录运行：

```bash
python3 skills/figma-motion-workflow/scripts/timeline.py audit examples/timing-spec.json
python3 -m unittest discover -s skills/figma-motion-workflow/scripts -p 'test_*.py' -v
```

</details>

## 能解决什么

| 场景 | Skill 如何处理 |
| --- | --- |
| 多轮对话后参数混乱 | 按属性整理生效值、覆盖记录、撤回与来源状态 |
| 线长完突然换形，接缝露白 | 先锁定源轮廓，检查起点、方向、交点、端帽与连接关系 |
| “路径到 90%”被当作时间到 90% | 按真实曲线反求触发时刻，缺曲线时保留待核验 |
| 主体加速了，表情和回落还在拖尾 | 重排依赖，整段结束取所有可见轨道的最大终点 |
| 只想撤回最后一次试验 | 恢复该次改动及依赖，保留其他已接受调整 |
| 工具只会读 Figma | 完成规格、分层和制作提示词，交代未执行部分 |

它提供制作方法与计时辅助工具。制作出的 Figma 动效、点击原型和导出视频需要分别验收。

## 制作方法

![从素材到动效验收的工作流程](docs/assets/workflow.svg)

1. **收拢素材和需求。** 为矢量、录屏、截图和修改意见记录来源与获取状态。
2. **先核对最终图形。** 保留轮廓、孔洞、接口和渐变，再拆真正需要独立运动的部件。
3. **按事件编排。** 记录哪条属性到哪个进度时触发，分清点击时间、预滚和参考视频时间。
4. **制作并修复。** 主体先行、细节随后；只修改本次涉及的属性和依赖。
5. **用结果验收。** 正常速度看节奏，关键帧看几何，实际实例检查点击和重播。

[阅读完整方法](docs/workflow.md) · [匿名四图标案例](skills/figma-motion-workflow/references/tabbar-case.md) · [复制制作与修复提示词](prompts/usage.md)

## 计时示例

路径在 100ms 开始，持续 300ms，采用示例曲线 `cubic-bezier(0,0,0.58,1)`。实际路径到 90% 的时刻约为 **322.13ms**；按 90% 时长计算则会写成 370ms。

小星随后显现、旋转，另有回落轨道时，整段结束还要检查这些轨道。运行 [示例规格](examples/timing-spec.json) 可得到完整依赖审计。示例曲线和参数均可替换。

## 包含什么

```text
skills/figma-motion-workflow/   Skill、方法参考、模板与计时脚本
examples/                      可运行的时序示例与预期输出
prompts/                       首轮制作、定点修复和撤回指令
docs/                          方法、安装、示意图与验证范围
downloads/                     独立 Skill 包及 SHA256 校验
scripts/                       打包与仓库检查
validation/                    本地检查结果
.github/                       自动检查工作流与问题模板
```

## 验证与限制

计时脚本的 **17 项单元测试已在本地通过**；此前还用两个新场景试用了曲线联动和局部撤回。本地检查依据与待验证能力见 [验证说明](docs/validation.md)，云端运行状态见 [GitHub Actions](https://github.com/lg9685294/figma-motion-workflow/actions)。

已验证的是本地计算、规格归并和包装结构。跨工具自动安装、真实 Figma Motion 写入、原型交互与导出仍需按环境实测；本仓库未附可下载的 `.fig` 工程。个人项目源文件、原始聊天和截图保留在本地。

## 参与改进

遇到问题时，请提供最小复现素材、期望动作、实际结果与发生时刻。素材可先匿名化，具体格式见 [参与说明](CONTRIBUTING.md)。

AG.ai · AI 产品经理，关注知识管理、设计体验与 AI 工作流。

相关项目：[用 AI 搭建 Obsidian 个人知识库](https://github.com/lg9685294/obsidian-second-brain-starter) · [用 AI 开始使用 Obsidian](https://github.com/lg9685294/obsidian-ai-guide)。

## 许可证与参考

本项目独立编写内容采用 [MIT](LICENSE) 许可证。借鉴的 Figma 取证、确定性时间轴和结果验证方法见 [来源与致谢](ATTRIBUTION.md)。第三方名称不表示官方合作或背书。

# 来源与致谢

本文及 Skill、计时脚本为独立编写。工作流吸收了以下公开项目中的方法，没有打包其源码或复制其 `SKILL.md`。与这些项目没有官方合作或背书关系。

| 来源 | 借鉴的工作方法 | 迁移边界 |
| --- | --- | --- |
| [OpenAI Figma skill](https://github.com/openai/skills/blob/main/skills/.curated/figma/SKILL.md) | 精确节点与截图、真实资产、复用设计系统、视觉核对 | 主要面向设计到代码，不把React或Tailwind变成Figma制作的前提 |
| [Remotion markup skill](https://github.com/remotion-dev/skills/blob/main/skills/remotion-markup/SKILL.md) | 明确时间基准、帧率换算、插值与确定性取样 | 不推广其逐帧运行时约束为所有动画禁令 |
| [Anthropic webapp-testing](https://github.com/anthropics/skills/blob/ef740771ac901e03fbca3ce4e1c453a96010f30a/skills/webapp-testing/SKILL.md) | 观察渲染状态后操作，再用实际证据验证 | 网页等待条件不能替代Figma原生状态检查 |

初次研究日期为2026-10-31；仓库热度不作为本项目质量或安装量的依据。

## 参考版本记录

- OpenAI文件历史曾指向 `dad3072ab3236e7315749a20a0abe48b53f831e2`。当时读取main与文件历史，未取得固定文件页，不声称逐字比对该版。
- Remotion文件历史及提交页曾指向 `11986e44eeb672b083354e68967f2b194df73b7c`。当时读取main，固定文件页未成功抓取。
- Anthropic上述固定链接已直接读取。

## 第三方许可范围

- OpenAI Figma目录的 [许可说明](https://github.com/openai/skills/blob/main/skills/.curated/figma/LICENSE.txt) 指向Figma Developer Terms；不能把该目录标记为MIT或Apache。
- 本次没有确认Remotion skills仓库的有效许可声明，不能套用Remotion主项目许可。本项目只转述方法并链接，不分发其文件。
- Anthropic webapp-testing目录的 [许可说明](https://github.com/anthropics/skills/blob/main/skills/webapp-testing/LICENSE.txt) 为Apache License 2.0；不据此推断整个仓库全部内容的许可。

本项目 [MIT许可](LICENSE) 覆盖本项目独立编写内容，不重新许可第三方材料。未来直接引入第三方代码时，应按对应版本许可另行保留声明。

## 官方文档

- [Skill格式与安装](https://learn.chatgpt.com/docs/build-skills)
- [Figma MCP工具与动效上下文](https://developers.figma.com/docs/figma-mcp-server/tools-and-prompts/)
- [Motion Path trim](https://help.figma.com/hc/en-us/articles/42200302811927-Animate-strokes-with-path-trim)
- [Smart Animate](https://help.figma.com/hc/en-us/articles/360039818874-Smart-animate-layers-between-frames)

产品能力以执行时的官方说明和实际工具为准。

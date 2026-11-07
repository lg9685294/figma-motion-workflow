# 安装、调用与更新

## 让 AI 处理

复制 [首页快速开始](../README.md#快速开始)，交给具有联网和文件读写能力的 AI。安装前读取 `SKILL.md` 与脚本；按当前工具支持的方式注册 Skill。安装成功并不代表已经连接 Figma。

## Codex

在 Codex 中，可让内置 `$skill-installer` 从本仓库的 `skills/figma-motion-workflow` 安装。也可以按照当前版本的本地 Skill 发现规则使用完整文件夹；不要只复制 `SKILL.md`，它引用的参考和脚本也需要保留。

官方文档说明仓库范围的 `.agents/skills` 和用户范围的 `$HOME/.agents/skills` 可用于本地发现；其他宿主或已有安装器可能采用不同目录，应沿用实际工具的路径。以 [官方 Skill 文档](https://learn.chatgpt.com/docs/build-skills) 为准。

安装后调用：

```text
使用 $figma-motion-workflow，根据这些源 SVG、Figma 节点和参考视频，
整理有效参数，制作或修复微动效，并回报已验证结果与待核验项。
```

本包采用通用 `SKILL.md` 文件夹形式；不宣称已在所有代理或 Figma 内置 Skill 安装入口验证，也没有注册成连接器或插件市场产品。

## 单独使用计时脚本

仅需 Python 3.9 或更新版本；本地已在 Python 3.9.6 测试，脚本只依赖标准库。

在仓库根目录执行：

```bash
python3 skills/figma-motion-workflow/scripts/timeline.py threshold --start-ms 100 --duration-ms 300 --progress 0.9 --easing 'cubic-bezier(0,0,0.58,1)'
python3 skills/figma-motion-workflow/scripts/timeline.py audit examples/timing-spec.json
```

返回 JSON。退出码 0 表示所列关系通过，2 表示输入非法、缺失曲线或存在时长冲突。只提供 Ease Out 等名称时不会猜测控制点。

## 更新

更新前保留当前安装版本及本地改动。比较 `CHANGELOG.md` 与文件差异，将更新放入原安装目录；项目参数和源文件放在项目目录，避免覆盖 Skill 模板或将项目文件混入安装包。

独立包的校验信息在 [SHA256SUMS](../downloads/SHA256SUMS.txt)，可用系统 SHA256 工具核对。

# 参与改进

欢迎提交可复现的问题或有证据支持的工作流改进。

报告问题时提供：使用环境、Skill版本、最小匿名素材、期望动作、实际结果、发生时刻或进度。区分计时计算错误、生成规格错误与Figma制作结果错误。

```bash
python3 skills/figma-motion-workflow/scripts/timeline.py audit examples/timing-spec.json
python3 -m unittest discover -s skills/figma-motion-workflow/scripts -p 'test_*.py' -v
python3 scripts/check_repository.py
```

修改Skill时保留适用边界；具体项目偏好写入案例，避免变成所有任务的强制默认。修复脚本时新增能证明实际错误的测试。修改后用 `scripts/build_skill.py` 重建独立包及校验信息。

提交内容须有相应分发权；不提交真实项目访问令牌、私有文件链接、个人聊天或未经允许的设计源稿。

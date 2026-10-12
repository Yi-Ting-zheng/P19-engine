# 贡献指南

感谢您对 P19 域外势能相变引擎的兴趣！

## 🎯 项目定位

本项目是一�?*异构 AI 审计系统**的骨架，目标是用物理隔离 + 观测维度正交来制衡单一 AI 的自我审计能力�?
**当前状�?*：骨架阶段，正在招募核心贡献�?
---

## 🤝 我们需要的贡献�?
### 优先�?P0：硬件工�?
**目标**：实现多 GPU 房间隔离与级联计�?
- [ ] Docker/gVisor 沙箱隔离方案
- [ ] �?GPU 资源调度
- [ ] CXL 内存池原型验�?- [ ] Intel Gaudi 3 / Falcon Shores 适配（如有硬件）

**技能要�?*：Linux 系统编程、Docker/K8s、GPU 管理

### 优先�?P1：AI 系统

**目标**：接入异构基座，实现房间调度

- [ ] DeepSeek-V3 API 接入
- [ ] Claude-3.5 API 接入
- [ ] OpenCode / MiMo 接入
- [ ] 房间调度器实�?- [ ] YAML 消息协议标准�?
**技能要�?*：Python、LLM API、分布式系统

### 优先�?P2：形式化验证

**目标**：完�?Lean 探针与公理分�?
- [ ] Lean 4 探针标准�?- [ ] 公理依赖图构�?- [ ] trdeg API 调用指南完善
- [ ] Mathlib 集成测试

**技能要�?*：Lean 4、Mathlib、形式化验证

### 优先�?P3：人机交�?
**目标**：设计人脑接地界�?
- [ ] 增量裁决协议实现
- [ ] 台账可视�?- [ ] 真值层级展示界�?
**技能要�?*：前端开发、UI/UX 设计

---

## 🚀 快速开�?
### 1. Fork 并克隆仓�?
```bash
git clone https://github.com/[您的用户名]/P19-engine.git
cd P19-engine
```

### 2. 阅读文档

- [README.md](README.md) - 项目概览
- [docs/blueprint_v1.1.md](docs/blueprint_v1.1.md) - 完整蓝图
- [ROADMAP.md](ROADMAP.md) - 路线�?
### 3. 选择任务

查看 [Good First Issues](https://github.com/[您的用户名]/P19-engine/labels/good%20first%20issue) 或上面的需求列表�?
### 4. 提交 Pull Request

- Fork 项目
- 创建特性分�?(`git checkout -b feature/amazing-feature`)
- 提交更改 (`git commit -m 'Add amazing feature'`)
- 推送分�?(`git push origin feature/amazing-feature`)
- 创建 Pull Request

---

## 📋 贡献规范

### 代码风格

- Python: 遵循 PEP 8
- Lean: 遵循 Mathlib 风格指南
- 文档: Markdown，中文为主，关键术语附英�?
### 提交信息

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型（type）：
- `feat`: 新功�?- `fix`: 修复
- `docs`: 文档
- `style`: 代码风格
- `refactor`: 重构
- `test`: 测试
- `chore`: 构建/辅助工具

示例�?```
feat(rooms): 实现 Docker 沙箱隔离

- 使用 gVisor 实现进程级隔�?- 添加 GPU 资源限制配置
- 添加单元测试

Closes #12
```

### Pull Request 检查清�?
- [ ] 代码通过测试
- [ ] 文档已更�?- [ ] 提交信息符合规范
- [ ] 无合并冲�?
---

## 🐛 报告问题

使用 [GitHub Issues](https://github.com/[您的用户名]/P19-engine/issues) 报告问题�?
**问题模板**�?
```markdown
**描述问题**
清晰简洁地描述问题�?
**复现步骤**
1. 执行 '...'
2. 点击 '....'
3. 出现错误

**预期行为**
描述您预期的行为�?
**实际行为**
描述实际的行为�?
**环境**
- 操作系统：[�?Ubuntu 22.04]
- Python 版本：[�?3.10]
- GPU：[�?NVIDIA A100]

**附加信息**
添加任何其他相关信息、截图或错误日志�?```

---

## 📄 许可�?
贡献的代码采�?Apache License 2.0，详�?[LICENSE](LICENSE)�?
---

## 📞 联系方式

- **GitHub Issues**: [问题跟踪](https://github.com/[您的用户名]/P19-engine/issues)
- **Email**: [您的邮箱]

---

## 🙏 致谢

感谢所有贡献者的支持�?
---

<p align="center">
  <i>不是造更强的 AI，是�?用异构算力制衡单一智能"的物理生态�?/i>
</p>

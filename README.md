# P19 域外势能相变引擎

> **用异构算力制衡单一智能的物理生态**
> 
> Truth doesn't depend on a single AI's self-awareness. It depends on heterogeneous computing power's physical constraints + human grounding.

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.23322681.svg)](https://doi.org/10.5281/zenodo.23322681)
[![Release](https://img.shields.io/badge/release-v0.1.1-green.svg)](https://github.com/Yi-Ting-zheng/P19-engine/releases/tag/0.1.1)
[![Status](https://img.shields.io/badge/status-skeleton-orange.svg)](#roadmap)

---

## 🎯 一句话定义

**P19 引擎是一套多房间隔离的异构 AI 审计系统，用于对形式化推理制品（Lean 证明、数学推理链）进行诚实审计与受控真值升格。**

**不是造更强的 AI，是造"用异构算力制衡单一智能"的物理生态。**

---

## 💡 为什么需要这个？

### 问题：单模型自我审计的不可能性

当前 AI 形式化证明系统的核心困境：

| 现象 | 根因 | 后果 |
|------|------|------|
| AI 声称证明了猜想 | 单模型无外部制衡 | 伪证明泛滥 |
| 自我审查循环失效 | C-02：同角色复核无效 | AI 无法真正审计自己 |
| 硬墙被美化 | 缺乏制度性诚实机制 | 真值层级混乱 |

### 解决：物理隔离 + 观测维度正交 + 人脑接地

**P19 引擎的三重保障**：

1. **物理隔离**：多个 AI 在沙箱中独立观测，互不通气
2. **观测维度正交**：形式化 / 数值 / 语义 / 对抗 四维交叉
3. **人脑接地**：人类签字意义与伦理，真值由版本化台账维护

---

## 🏗️ 系统架构（五层）

```
┌─────────────────────────────────────────────────────────────┐
│  ⑤ 接地层 — 人脑裁决接口                                     │
│     意义锚点 + 伦理签字（非真值裁判）                          │
├─────────────────────────────────────────────────────────────┤
│  ④ 自审层 — 系统自检与阴性对照                                │
│     阴性标本注入 + 台账完整性校验 + CANCELLED 识别             │
├─────────────────────────────────────────────────────────────┤
│  ③ 相变层 — 主控 + 房间调度 + 一致性判定                       │
│     P19 时序协议：并行生成 → 冲突检测 → 相变仲裁               │
├─────────────────────────────────────────────────────────────┤
│  ② 审计层 — 宪法中间件                                       │
│     math_attack_rules.yaml 硬拦截越界断言                      │
├─────────────────────────────────────────────────────────────┤
│  ① 发现层 — Axiom 探针                                       │
│     标准化解析：axiom_set, dependency_graph, gap_list          │
└─────────────────────────────────────────────────────────────┘
```

### 核心创新：观测维度正交

| 房间 | 观测维度 | 判定依据 | 真值产出 |
|------|---------|---------|---------|
| Room-F | **形式化** | Lean 类型检查、公理依赖图、trdeg 推导链 | 编译通过性、公理集、缺口分类 |
| Room-N | **数值** | mpmath PSLQ、高精度探针、参数扫描 | EMPIRICAL 支持/反例、效应量 |
| Room-S | **语义** | 证明结构合理性、定义一致性、隐含假设识别 | 语义漏洞、定义漂移、隐式公理 |
| Room-A | **对抗** | 反例搜索、边界条件、最小反例构造 | 反例、边界失效、退化情形 |

**正交性**：四个维度的判定依据在认识论上不可互推——形式化验证通过 ≠ 数值验证通过 ≠ 语义合理 ≠ 对抗存活。

---

## ✅ 已完成（原型验证）

### P0 原型：单基座 76 分钟闭环

**验证成果**：

| 成果 | 状态 | 说明 |
|------|------|------|
| Specimen-001（EXIT=1） | ✅ | 阴性标本，验证系统识别符号错误能力 |
| Specimen-002（EXIT=0+硬墙） | ✅ | 阳性诚实标本，保留 Schanuel 硬墙 |
| Specimen-003（CANCELLED） | ✅ | 阴性规划标本，验证自动识别冗余任务 |
| 真值台账 | ✅ | 红绿条目并列，不美化、不掩盖 |
| 三标记体系 | ✅ | sorry / AXIOM / CANCELLED 强制元数据 |

**关键发现**：

- 缺口 1（SchanuelAt）= 数学硬墙，永久标记 GAP-OPEN
- 缺口 2-6 = 已攻克，全部有 Mathlib 现成解
- M5-b（Lindemann-Weierstrass 蓝图）= 主动放弃（CANCELLED）

### 理论基础

本引擎基于以下理论框架：

- **P19 相变外驱定理**：相变窗口仅由跨域外部势能差打开
- **C-02 同系统多 Agent 无效审计推论**：同角色复核无效，独立性由规则+观测维度承载
- **C-01 上下文文本模态上限定理**：纯文本注入无法触发认知跃迁
- **T14 认知幻觉定理**：逻辑自洽 ≠ 真相，高度确信 ≠ 正确

---

## 🗺️ Roadmap

### Phase 0：原型验证 ✅

- [x] 单基座 76 分钟闭环
- [x] Specimen 标本库（3 个标本）
- [x] 真值台账系统
- [x] 三标记体系

### Phase 1：双房间验证 🔜

- [ ] 2 个隔离房间（形式化 + 对抗）
- [ ] YAML 消息协议
- [ ] 基础相变状态机
- [ ] 阴性标本压力测试

### Phase 2：四房间正交 🔜

- [ ] 4 个观测维度房间
- [ ] 正交性验证矩阵
- [ ] 分层投票机制
- [ ] CXL 级联内存接入

### Phase 3：v1.0 正式上线 🔜

- [ ] 完整五层流水线
- [ ] 标本归档库
- [ ] 人脑接地接口
- [ ] 性能目标：76min → 76s + T_arbitration

**详细路线图见 [ROADMAP.md](ROADMAP.md)**

---

## 🤝 需要的贡献者

### 优先级 P0：硬件工程

- [ ] 多 GPU 房间隔离实现（Docker/gVisor）
- [ ] CXL 内存池原型验证
- [ ] Intel Gaudi 3 / Falcon Shores 适配

### 优先级 P1：AI 系统

- [ ] 异构基座接入（DeepSeek-V3 / Claude-3.5 / OpenCode / MiMo）
- [ ] 房间调度器实现
- [ ] YAML 消息协议标准化

### 优先级 P2：形式化验证

- [ ] Lean 探针标准化
- [ ] 公理依赖图构建
- [ ] trdeg API 调用指南完善

### 优先级 P3：人机交互

- [ ] 人脑接地界面设计
- [ ] 增量裁决协议
- [ ] 台账可视化

**详见 [CONTRIBUTING.md](CONTRIBUTING.md)**

---

## 📚 文档

| 文档 | 内容 |
|------|------|
| [docs/blueprint_v1.1.md](docs/blueprint_v1.1.md) | 完整工程蓝图 v1.1 |
| [docs/revision_patch.md](docs/revision_patch.md) | v1.0 → v1.1 修订补丁 |
| [docs/specimen_library.md](docs/specimen_library.md) | 标本库说明 |
| [docs/truth_ledger.md](docs/truth_ledger.md) | 真值台账规范 |
| [docs/human_protocol.md](docs/human_protocol.md) | 人脑接地协议 |

---

## 📖 引用

如果本项目对您的研究有帮助，请引用：

```bibtex
@software{p19_engine,
  title = {P19 Exogenous Potential Phase Transition Engine},
  author = {Zheng, Yiting},
  year = {2026},
  publisher = {Zenodo},
  version = {0.1.1},
  doi = {10.5281/zenodo.23322681},
  url = {https://doi.org/10.5281/zenodo.23322681}
}
```

**DOI**: [10.5281/zenodo.23322681](https://doi.org/10.5281/zenodo.23322681)
**所有版本 DOI**: [10.5281/zenodo.23322680](https://doi.org/10.5281/zenodo.23322680)

---

## 📄 许可证

本项目采用 Apache License 2.0 - 详见 [LICENSE](LICENSE)

---

## 🏷️ 标签

`AGI` `AI-Safety` `Formal-Verification` `Lean4` `Mathlib` `Multi-Agent` `Heterogeneous-Computing` `Truth-Verification` `CXL` `P19`

---

<p align="center">
  <b>郑奕廷（望易）</b><br>
  <i>不是造更强的 AI，是造"用异构算力制衡单一智能"的物理生态。</i><br>
  <small>wayne777@agent.qq.com | WX: qmzywe666</small>
</p>

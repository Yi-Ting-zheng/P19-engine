# 人脑接地协议

> P19 域外势能相变引擎中人类参与者的角色与协议

## 人脑角色重定义

### 从 v1.0 到 v1.1

| 维度 | v1.0 | v1.1 |
|------|------|------|
| **真值裁判** | ✅ 人脑负责 | ❌ 版本化台账负责 |
| **意义锚点** | 未定义 | ✅ 人脑负责 |
| **伦理签字** | 未定义 | ✅ 人脑负责 |

### 为什么人脑不做真值裁判？

1. **上下文连续性问题**：人脑批量裁决可能忘记历史判定
2. **速度不匹配**：顶级科学家也跟不上 AI 形式化验证速度
3. **稳定性问题**：真值不应依赖人的实时记忆

---

## 人脑三大职责

### 职责 1：意义锚点

**人脑回答的问题**：「这个命题对我们有意义吗？值得继续投入资源吗？」

| 判定类型 | 判定问题 | 输出 |
|---------|---------|------|
| 方向性 | 这条证明路径值得继续吗？ | GO / NO-GO |
| 优先级 | 这个缺口应该优先修复吗？ | P0 / P1 / P2 |
| 资源分配 | 应该投入更多算力吗？ | 增加 / 维持 / 减少 |

**示例场景**：

```yaml
scenario: "SchanuelAt 硬墙"
context: 
  - GAP-001 依赖 Schanuel 猜想
  - Schanuel 猜想是 7 大 Millennium 问题之一
  - 当前无任何证明进展

human_judgment:
  type: "意义锚点"
  question: "是否继续投入资源尝试证明 Schanuel 猜想？"
  verdict: "NO-GO"
  reason: "Schanuel 猜想是顶级数学难题，投入产出比极低"
  alternative: "寻找绕过 Schanuel 的替代路径"
```

### 职责 2：伦理签字

**人脑回答的问题**：「这个结果可以发布/使用吗？符合伦理规范吗？」

| 判定类型 | 判定问题 | 输出 |
|---------|---------|------|
| 发布合规 | 这个结果可以公开吗？ | APPROVE / REJECT |
| 使用边界 | 这个结果的使用场景有伦理风险吗？ | 无风险 / 有限制 / 有风险 |
| 责任归属 | 如果结果出错，谁负责？ | 签字确认 |

**示例场景**：

```yaml
scenario: "Specimen-002 发布审核"
context:
  - π^π 超越性证明（THEOREM-COND）
  - 依赖 SchanuelAt 公理
  - 形式化验证通过

human_judgment:
  type: "伦理签字"
  question: "是否可以发布这个结果？"
  verdict: "APPROVE"
  conditions: 
    - "必须明确标注依赖 SchanuelAt"
    - "不得声称是无条件定理"
    - "必须附带硬墙说明"
  signer: "human_001"
  timestamp: "2026-10-11T..."
```

### 职责 3：硬墙分类确认

**人脑回答的问题**：「此处红点是可补疏漏还是不可补深渊？」

| 判定类型 | 判定问题 | 输出 |
|---------|---------|------|
| 硬墙分类 | 这是工程疏漏还是数学硬墙？ | FIXABLE / ABYSS |
| 复活条件 | 如果是硬墙，什么条件下可以重审？ | 条件描述 |

**示例场景**：

```yaml
scenario: "缺口1分类"
context:
  - GAP-001: SchanuelAt → trdeg 推导
  - M6-04 分析：无法在 Lean 中直接证明
  - 需要 Schanuel 猜想的完整证明

human_judgment:
  type: "硬墙分类"
  question: "GAP-001 是可补疏漏还是不可补深渊？"
  verdict: "ABYSS"
  reason: "Schanuel 猜想是未解决的 Millennium 问题"
  reconsider_when: "Schanuel 猜想被证明，且 Lean 中有形式化版本"
  signer: "human_001"
  timestamp: "2026-10-11T..."
```

---

## 增量裁决协议

### 从批量裁决到增量裁决

```
v1.0：批量裁决（每小时），人脑判定真值
v1.1：增量裁决（按需），人脑签字意义+伦理，真值由台账维护
```

### 增量裁决流程

```
系统检测到需要人脑介入的场景
    ↓
人脑收到通知，查看上下文
    ↓
人脑签字（意义/伦理/硬墙分类）
    ↓
系统更新台账，记录人脑签字
    ↓
系统检测历史判定冲突（如有）
```

### 触发条件

| 触发条件 | 介入类型 | 紧急度 |
|---------|---------|--------|
| 新标本完成审计 | 意义锚点 | 中 |
| 发现新硬墙 | 硬墙分类 | 高 |
| 发布前审核 | 伦理签字 | 高 |
| 季度重审 | 全部 | 中 |
| 硬墙复活条件满足 | 硬墙分类 | 高 |

---

## 真值稳定性保障

### 核心原则

**真值判定不依赖人脑的实时记忆，依赖版本化台账**

### 实现方式

```yaml
truth_ledger:
  version: "v2026.10.11.001"
  judgments:
    - judgment_id: "J-001"
      type: "GAP_CLASSIFICATION"
      item: "GAP-001 (SchanuelAt)"
      verdict: "ABYSS"
      human_signer: "human_001"
      timestamp: "2026-10-11T10:00:00Z"
      evidence: "P0研究报告 + M6-04缺口分析"
      reversible: true
      reconsider_when: "Schanuel猜想被证明"
      
    - judgment_id: "J-002"
      type: "RELEASE_APPROVAL"
      item: "Specimen-002"
      verdict: "APPROVE"
      human_signer: "human_001"
      timestamp: "2026-10-11T11:00:00Z"
      conditions: "必须附带硬墙标注"
```

### 关键特性

1. **增量追加**：每次人脑裁决都是增量，不覆盖历史
2. **可追溯**：真值判定可追溯到具体人脑签字
3. **可审计**：所有裁决记录可审计
4. **可回滚**：发现错误可回滚到历史版本

---

## 人脑**不做**的

### 明确排除的职责

| 不做 | 由谁负责 | 原因 |
|------|---------|------|
| ❌ 真值裁判 | 版本化台账 | 真值稳定性不应依赖人的记忆 |
| ❌ 形式化验证 | Room-F | 人脑跟不上 AI 速度 |
| ❌ 数值验证 | Room-N | 人脑无法执行高精度计算 |
| ❌ 语义验证 | Room-S | 人脑有上下文偏见 |
| ❌ 对抗验证 | Room-A | 人脑有确认偏误 |

### 人脑的局限性

1. **上下文窗口有限**：无法同时处理多个标本
2. **速度慢**：无法跟上 AI 形式化验证速度
3. **有偏见**：有确认偏误、锚定效应等认知偏差
4. **不稳定**：不同时间可能给出不同判定

**因此**：人脑应专注于**意义、伦理、方向**，而不是**真值、验证、判定**。

---

## 协作界面设计

### 通知机制

```yaml
notification:
  trigger: "新硬墙发现"
  recipient: "human_001"
  priority: "HIGH"
  context:
    - gap_id: "GAP-002"
    - description: "..."
    - evidence: "..."
  action_required: "硬墙分类确认"
  deadline: "2026-10-12T..."
```

### 签字界面

```yaml
judgment_interface:
  specimen_id: "Specimen-002"
  context: "π^π 超越性证明"
  question: "是否可以发布这个结果？"
  
  options:
    - verdict: "APPROVE"
      conditions: ["附带硬墙标注"]
    - verdict: "REJECT"
      reason: "..."
    - verdict: "DEFER"
      reason: "需要更多信息"
  
  evidence:
    - "形式化验证报告"
    - "审计层报告"
    - "历史判定记录"
  
  submit_button: "签字提交"
```

### 历史查看

```yaml
history_interface:
  specimen_id: "Specimen-002"
  judgments:
    - judgment_id: "J-002"
      type: "RELEASE_APPROVAL"
      verdict: "APPROVE"
      human_signer: "human_001"
      timestamp: "2026-10-11T..."
      conditions: "必须附带硬墙标注"
  
  conflict_detection: "无冲突"
  related_judgments: ["J-001 (GAP-001)"]
```

---

## 常见场景

### 场景 1：新标本完成审计

```yaml
scenario: "新标本完成审计"
trigger: "Specimen-004 完成四房间审计"
context:
  - 标本类型: "positive"
  - 真值状态: "THEOREM-COND"
  - 硬墙: "GAP-003"
  
human_action:
  type: "意义锚点"
  question: "这个标本值得继续投入资源吗？"
  verdict: "GO"
  reason: "填补了重要缺口"
```

### 场景 2：发现新硬墙

```yaml
scenario: "发现新硬墙"
trigger: "审计层发现 GAP-004"
context:
  - 缺口描述: "..."
  - 证据: "..."
  - 类型: "未知"
  
human_action:
  type: "硬墙分类"
  question: "GAP-004 是可补疏漏还是不可补深渊？"
  verdict: "FIXABLE"
  reason: "只是 Lean API 缺失，不是数学难题"
  estimated_effort: "3天"
```

### 场景 3：发布前审核

```yaml
scenario: "发布前审核"
trigger: "准备发布 Specimen-002"
context:
  - 真值状态: "THEOREM-COND"
  - 硬墙: "GAP-001"
  
human_action:
  type: "伦理签字"
  question: "是否可以发布这个结果？"
  verdict: "APPROVE"
  conditions: 
    - "必须明确标注依赖 SchanuelAt"
    - "不得声称是无条件定理"
```

### 场景 4：季度重审

```yaml
scenario: "季度重审"
trigger: "2026-Q4 季度重审"
context:
  - 待重审标本: "10个"
  - 待重审硬墙: "3个"
  - 待重审CANCELLED: "2个"
  
human_action:
  type: "全部"
  question: "所有判定是否仍有效？"
  verdict: "CONFIRM_ALL"
  reason: "无重大进展，判定维持"
```

---

*人脑接地协议｜P19 域外势能相变引擎｜2026-10-11*

# 真值台账规范

> P19 域外势能相变引擎的真值层级与台账系统

## 真值层级体系

### 三级真值

| 层级 | 定义 | 升格条件 | 降格条件 |
|------|------|---------|---------|
| **EMPIRICAL** | 数值实证支持 | 多次独立实验支持 | 发现反例 |
| **THEOREM-COND** | 条件定理（有前提） | 形式化验证 + 条件明确 | 前提被证伪 |
| **THEOREM** | 定理（无条件） | 严格证明链闭合 | 不可降格 |

### 递归升级禁令

```
EMPIRICAL  ≠> THEOREM
```

**规则**：数值实证不能直接升格为定理。多次 EMPIRICAL 支持**不构成** THEOREM 的充分条件。

**原因**：数值收敛 ≠ 数学证明。PSLQ 找不到关系 ≠ 关系不存在。

### 硬墙标记（GAP-OPEN）

**定义**：当前无法证明的缺口，永久标记

**特征**：
- 数学硬墙：依赖未解决的猜想（如 Schanuel 猜想）
- 工程硬墙：当前工具/方法无法处理

**规则**：
- 硬墙必须永久保留，不得美化
- 硬墙不得被标记为 THEOREM
- 硬墙必须记录复活条件

---

## 台账结构

### 核心字段

```yaml
truth_ledger:
  version: "v2026.10.11.001"           # 版本号
  timestamp: "2026-10-11T..."          # 创建时间
  append_only: true                     # 追加式，不修改历史
  previous_version: "v2026.10.10.002"   # 前一版本哈希
  hash_chain: "sha256:xyz..."           # 哈希链
  
  entries:                              # 台账条目
    - id: "ENTRY-001"
      specimen_id: "Specimen-002"
      type: "truth_status"
      value: "THEOREM-COND"
      reason: "形式化验证通过，但依赖 SchanuelAt"
      human_signer: "human_001"
      timestamp: "2026-10-11T..."
      reversible: true
      reconsider_when: "Schanuel猜想被证明"
```

### 统计字段

```yaml
statistics:
  total_entries: 100
  by_type:
    truth_status: 50
    gap_classification: 30
    human_judgment: 20
  
  by_value:
    EMPIRICAL: 40
    THEOREM-COND: 8
    THEOREM: 2
    REJECT: 30
    CANCELLED: 20
  
  hard_walls: 3
  reversible: 15
```

---

## 红绿并存原则

### 核心规则

**REJECT 和 THEOREM-COND 并列存在，不掩盖**

**示例**：

```yaml
entries:
  # 绿条目
  - id: "ENTRY-001"
    specimen_id: "Specimen-002"
    type: "truth_status"
    value: "THEOREM-COND"
    reason: "形式化验证通过"
  
  # 红条目（并列，不删除）
  - id: "ENTRY-002"
    specimen_id: "Specimen-001"
    type: "truth_status"
    value: "REJECT"
    reason: "符号错误，Lean 类型检查失败"
  
  # 红条目（并列，不删除）
  - id: "ENTRY-003"
    specimen_id: "Specimen-003"
    type: "truth_status"
    value: "CANCELLED"
    reason: "发现更优替代方案"
```

**为什么红绿并存**：
1. 掩盖 REJECT 会造成虚假繁荣
2. 红条目是系统的诚实记录
3. 红条目可追溯、可审计

---

## 人脑接地协议

### 人脑新职责

| 职责 | 判定问题 | 输出 |
|------|---------|------|
| **意义锚点** | 这个命题值得继续投入吗？ | GO / NO-GO |
| **伦理签字** | 这个结果可以发布吗？ | APPROVE / REJECT |
| **硬墙分类** | 红点是可补疏漏还是不可补深渊？ | FIXABLE / ABYSS |

### 人脑**不做**的

- ❌ 真值裁判（由版本化台账维护）
- ❌ 形式化验证（由 Room-F 负责）
- ❌ 数值验证（由 Room-N 负责）
- ❌ 语义验证（由 Room-S 负责）
- ❌ 对抗验证（由 Room-A 负责）

### 增量裁决协议

```
v1.0：批量裁决（每小时），人脑判定真值
v1.1：增量裁决（按需），人脑签字意义+伦理，真值由台账维护
```

**流程**：

1. 系统检测到需要人脑介入的场景
2. 人脑收到通知，查看上下文
3. 人脑签字（意义/伦理/硬墙分类）
4. 系统更新台账，记录人脑签字
5. 人脑不需要记住历史判定，系统自动检测冲突

### 真值稳定性保障

**核心原则**：真值判定不依赖人脑的实时记忆，依赖**版本化台账**

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
```

---

## 版本化与哈希链

### 版本化

```yaml
ledger_versioning:
  current: "v2026.10.11.001"
  history:
    - version: "v2026.10.10.002"
      timestamp: "2026-10-10T..."
      changes: "新增 GAP-003"
    - version: "v2026.10.11.001"
      timestamp: "2026-10-11T..."
      changes: "CANCELLED M5-b; 新增 trdeg_API_调用指南"
  append_only: true
  hash_chain: "sha256:abc123..."
```

### 哈希链规则

1. **每次更新**：计算新版本哈希
2. **记录前版**：新版本记录前一版本哈希
3. **校验完整性**：定期校验哈希链完整性
4. **检测篡改**：哈希不匹配 = 篡改

---

## 季度重审协议

### 触发条件

| 触发条件 | 重审范围 | 执行者 |
|---------|---------|--------|
| 时间触发 | 每季度（90天） | 系统自动 |
| 外部触发 | Mathlib 大版本更新 | 系统自动 |
| 人工触发 | 人类主动发起 | 人类 + 系统 |

### 重审检查清单

```yaml
quarterly_review_checklist:
  - check: "AXIOM 是否仍不可证？"
    action: "检索最新文献，检查是否有新证明"
    output: "CONFIRM_BARRIER / UPDATE_STATUS"
    
  - check: "CANCELLED 是否仍应取消？"
    action: "检查替代方案是否仍有效"
    output: "CONFIRM_CANCELLED / RECONSIDER"
    
  - check: "sorry 是否仍被阻塞？"
    action: "检查依赖的硬墙是否被攻克"
    output: "CONFIRM_BLOCKED / ATTEMPT_FIX"
    
  - check: "三标记分类是否漂移？"
    action: "抽查 10% 标记，验证分类准确性"
    output: "NO_DRIFT / CORRECT_DRIFT"
    
  - check: "台账哈希是否完整？"
    action: "校验所有标本的哈希绑定"
    output: "HASH_OK / HASH_BROKEN"
```

### 重审结果处理

| 结果 | 处理 |
|------|------|
| CONFIRM_* | 更新 `last_reviewed` 时间戳 |
| UPDATE_STATUS | 创建新版本台账，保留旧版本 |
| RECONSIDER | 重新评估，可能复活 CANCELLED |
| ATTEMPT_FIX | 触发修复流程 |
| CORRECT_DRIFT | 修正分类，记录修正历史 |

---

## 防腐机制

### 防止判定标准漂移

| 风险 | 防腐机制 |
|------|---------|
| CANCELLED 标准放宽 | 强制元数据 + 季度重审 |
| AXIOM 被滥用 | 类型约束 + 来源追溯 |
| sorry 被滥用 | 阻塞缺口必须记录 |
| 真值层级混乱 | 递归升级禁令 + 硬墙标记 |

### 强制元数据

每个 `sorry/AXIOM/CANCELLED` 必须附带：
- `reason`：理由
- `evidence`：证据
- `reversible`：可复活性
- `reconsider_when`：复活条件
- `quarterly_review_due`：季度重审时间

---

*真值台账规范｜P19 域外势能相变引擎｜2026-10-11*

# 标本库说明

> P19 域外势能相变引擎的标本归档系统

## 标本类型

### 1. 阳性诚实标本（Positive Specimen）

**定义**：证明完成但包含硬墙（GAP-OPEN）的推理制品

**特征**：
- Lean 编译通过（EXIT=0）
- 公理集中包含硬墙标记
- 缺口分类为「数学硬墙」

**示例**：Specimen-002（π^π 超越性证明）

```yaml
specimen:
  id: "Specimen-002"
  type: "positive"
  exit_code: 0
  axioms:
    - "SchanuelAt"  # 硬墙
  gaps:
    - id: "GAP-001"
      description: "SchanuelAt → trdeg 推导"
      classification: "mathematical_barrier"
      fixable: false
  truth_status: "THEOREM-COND"
  human_signer: "human_001"
```

### 2. 阴性标本（Negative Specimen）

**定义**：包含符号错误或推理缺陷的推理制品

**特征**：
- Lean 编译失败（EXIT≠0）
- 或包含 CANCELLED 标记的任务
- 或触发审计层硬拦截

**示例**：Specimen-001（符号错误标本）

```yaml
specimen:
  id: "Specimen-001"
  type: "negative"
  exit_code: 1
  error_type: "symbolic_error"
  detected_by: "Room-F"
  audit_result: "REJECT"
  reason: "Lean 类型检查失败：存在未绑定的自由变量"
```

### 3. 被放弃标本（Cancelled Specimen）

**定义**：因发现更优替代方案而主动放弃的推理制品

**特征**：
- 标记为 `CANCELLED`
- 包含复活条件
- 不计入真值统计

**示例**：Specimen-003（M5-b Lindemann-Weierstrass 蓝图）

```yaml
specimen:
  id: "Specimen-003"
  type: "cancelled"
  cancelled_reason: "M6-04 证明缺口2-6全部有 Mathlib 现成解，无需 LW"
  evidence: "docs/M6-04_缺口456分析.md"
  alternative: "docs/trdeg_API_调用指南.md"
  reversible: true
  reconsider_when: "缺口1被攻克，需要 LW 级结果"
```

---

## 归档结构

```
specimens/
├── index.yaml              # 索引文件
├── positive/
│   ├── Specimen-002/
│   │   ├── specimen.yaml   # 标本元数据
│   │   ├── proof.lean      # Lean 证明文件
│   │   └── audit/          # 审计报告
│   │       ├── room_f.yaml
│   │       ├── room_n.yaml
│   │       ├── room_s.yaml
│   │       └── room_a.yaml
│   └── ...
├── negative/
│   ├── Specimen-001/
│   │   ├── specimen.yaml
│   │   ├── proof.lean
│   │   └── audit/
│   └── ...
└── cancelled/
    ├── Specimen-003/
    │   ├── specimen.yaml
    │   ├── plan.md
    │   └── evidence/
    └── ...
```

---

## 真值台账（Truth Ledger）

### 台账结构

```yaml
truth_ledger:
  version: "v2026.10.11.001"
  specimens:
    - id: "Specimen-001"
      hash: "sha256:abc123..."
      truth_status: "REJECT"
      reason: "符号错误"
      
    - id: "Specimen-002"
      hash: "sha256:def456..."
      truth_status: "THEOREM-COND"
      hard_wall: "GAP-001"
      
    - id: "Specimen-003"
      hash: "sha256:ghi789..."
      truth_status: "CANCELLED"
      alternative: "trdeg_API_调用指南"
  
  statistics:
    total: 3
    positive: 1
    negative: 1
    cancelled: 1
    
  append_only: true
  hash_chain: "sha256:xyz..."
```

### 台账规则

1. **追加式**：只追加，不修改历史记录
2. **红绿并存**：REJECT 和 THEOREM-COND 并列，不掩盖
3. **哈希绑定**：每个标本绑定 SHA256 哈希
4. **版本链**：每次更新记录前一版本哈希

---

## 三标记体系

### sorry

**含义**：证明未完成，依赖未解决的缺口

```yaml
sorry:
  reason: "依赖缺口1（SchanuelAt桥接）"
  classification: "数学硬墙依赖"
  blocking_gap: "GAP-001"
  fixable: false
```

### AXIOM

**含义**：外部公理，不可证明

```yaml
axiom:
  name: "SchanuelAt"
  type: "外部猜想公理"
  source: "Schanuel猜想（未证明）"
  truth_status: "HYPOTHESIS"
  can_be_proved: false
```

### CANCELLED

**含义**：主动放弃，有复活条件

```yaml
cancelled:
  reason: "发现更优替代方案"
  evidence: "M6-04分析文档"
  alternative: "替代方案文档"
  reversible: true
  reconsider_when: "条件描述"
```

---

## 季度重审协议

每季度（90天）执行以下检查：

| 检查项 | 动作 | 输出 |
|--------|------|------|
| AXIOM 是否仍不可证？ | 检索最新文献 | CONFIRM_BARRIER / UPDATE_STATUS |
| CANCELLED 是否仍应取消？ | 检查替代方案 | CONFIRM_CANCELLED / RECONSIDER |
| sorry 是否仍被阻塞？ | 检查硬墙状态 | CONFIRM_BLOCKED / ATTEMPT_FIX |
| 三标记分类是否漂移？ | 抽查 10% | NO_DRIFT / CORRECT_DRIFT |
| 台账哈希是否完整？ | 校验哈希链 | HASH_OK / HASH_BROKEN |

---

## 元数据 Schema

### sorry_metadata

```yaml
sorry_metadata:
  id: "SORRY-001"
  location: "ChainM3.lean:100"
  reason: "依赖缺口1（SchanuelAt桥接）"
  classification: "数学硬墙依赖"
  blocking_gap: "GAP-001"
  fixable: false
  estimated_effort: "N/A"
  created: "2026-10-11T..."
  last_reviewed: "2026-10-11T..."
  reviewer: "system_auto"
```

### axiom_metadata

```yaml
axiom_metadata:
  id: "AXIOM-001"
  name: "SchanuelAt"
  type: "外部猜想公理"
  source: "Schanuel猜想（未证明）"
  used_in: "step1_algIndep_pi_lnp, step3_algIndep_four, ..."
  truth_status: "HYPOTHESIS"
  can_be_proved: false
  proof_barrier: "需要Schanuel猜想的完整证明"
  created: "2026-09-30T..."
  last_reviewed: "2026-10-11T..."
  reviewer: "human_001"
  quarterly_review_due: "2027-01-11T..."
```

### cancelled_metadata

```yaml
cancelled_metadata:
  id: "CANCELLED-001"
  name: "M5-b Lindemann-Weierstrass蓝图"
  reason: "M6-04证明缺口2-6全部有Mathlib现成解，无需LW"
  evidence: "docs/M6-04_缺口456分析.md"
  alternative: "docs/trdeg_API_调用指南.md"
  reversible: true
  reconsider_when: "缺口1被攻克，需要LW级结果"
  cancelled_by: "system_auto"
  approved_by: "human_001"
  timestamp: "2026-10-11T..."
  last_reviewed: "2026-10-11T..."
  quarterly_review_due: "2027-01-11T..."
```

---

## 阴性标本压力测试

**目的**：验证系统能够正确拦截伪证明

**流程**：

1. **注入阴性标本**：故意注入包含错误的推理制品
2. **检测拦截**：审计层应硬拦截该标本
3. **记录结果**：标记为 REJECT，记录拦截原因
4. **验证统计**：阴性标本应出现在台账 REJECT 条目中

**测试用例**：

| 标本 | 错误类型 | 预期拦截层 |
|------|---------|-----------|
| 符号错误 | 自由变量未绑定 | Room-F（形式化） |
| 逻辑漏洞 | 缺少必要条件 | Room-S（语义） |
| 边界失效 | 极端情况反例 | Room-A（对抗） |
| 数值异常 | PSLQ 无关系 | Room-N（数值） |

---

*标本库说明｜P19 域外势能相变引擎｜2026-10-11*

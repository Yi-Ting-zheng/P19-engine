# GAP 台账（人读版）

> 单一可信源：`config/gap_registry.yaml`（append-only 注册表）
> 哈希链固化产物：`specimens/positive/Specimen-002/evidence/gap_ledger.yaml`（由 `tools/export_gap_ledger.py` 生成）
> 本文档为人读登记簿；条目变更必须先改注册表，再重跑导出工具，最后同步本文件。
> 最后更新：2026-10-13

---

## 1. 链完整性与版本过渡

| 项 | 旧链（v2026.10.13.001） | 新链（v2026.10.13.002） |
|----|------------------------|------------------------|
| 条目数 | 6 | 8 |
| registry_sha256 | `9c491e3a85695f8e90141fe22dced83a2a93452ce556e7a4f60285bf6cf31207` | `a7a7559bd843b5e365d1a9277af06c56ab4f46c5af07de776abda28345727a01` |
| tail_hash | `c802116f4cf3aaa135288588d60dd796b3c009b08f13cd78cf21def9853f2821` | `267ebde96725628f2caaba0d07ed505d29c294e5dd18b84e8c1f4431e74277e6` |

**过渡说明**：导出工具以注册表为唯一源全量重建哈希链；`registry_version` 参与每条 entry 的哈希计算，
故版本从 001 升至 002 时 seq 1–6 的条目哈希随之重算（**缺口内容字段零变更**，仅版本戳变化），
seq 7–8 为本次新增。旧链以本表锚定，可随时用旧版注册表复算核对。

复算核验：`python tools/export_gap_ledger.py` 后比对 `tail_hash` 与本文档一致。

---

## 2. 条目总表

| seq | id | 标题 | 分类 | 状态 | 威胁/阶段 | entry_hash（前16位） |
|-----|-----|------|------|------|-----------|---------------------|
| 1 | GAP-001 | Schanuel 猜想本体（trdeg 桥接硬墙） | mathematical_barrier | **OPEN（硬墙）** | — | `6f5c0fa6c119af3a` |
| 2 | GAP-002 | e^{lnπ} = π | complex_analysis | RESOLVED | — | `a1f422158f5f6218` |
| 3 | GAP-003 | e^{2πi} = 1 | euler_identity | RESOLVED | — | `55170c689fa84a50` |
| 4 | GAP-004 | 代数扩张 trdeg 不变 | commutative_algebra | SOLVABLE | — | `fff000f015f808a3` |
| 5 | GAP-005 | 代数元不增加 trdeg | commutative_algebra | SOLVABLE | — | `0986d234134a2855` |
| 6 | GAP-006 | trdeg ≥ 2 + 2 元生成 ⟹ 代数无关 | transcendence_theory | SOLVABLE | — | `5c9a553578535ac5` |
| 7 | GAP-007 | 房间外联未阻断（egress 仅标记） | isolation_egress | **OPEN** | T2 / 阶段 B | `0c0502d05feb0741` |
| 8 | GAP-008 | 房间资源配额缺失 | isolation_resource | **OPEN** | T5 / 阶段 B | `267ebde96725628f` |

统计：total=8 | open_barrier=1 | open_engineering=2 | resolved=2 | solvable=3

---

## 3. 本次新增条目（T2/T5 工程缺口）

> 来源：`docs/sandbox_isolation.md` 威胁模型（T1–T5）与阶段 A 落地记录 §5.4。
> 定性：**工程缺口**（EMPIRICAL 观测层级的已知残留），非数学硬墙，均可由阶段 B 容器方案收口。

### GAP-007 — 房间外联未阻断（egress 仅标记）

| 字段 | 值 |
|------|-----|
| classification | isolation_egress |
| status | OPEN |
| threat_ref | **T2**（房间外联污染观测正交性） |
| phase_target | B（容器 `--network=none`） |
| 现状 | 阶段 A worker 启动时 `egress_probe()`（0.3s，1.1.1.1:443）探测并写入 `claims.isolation_selfcheck.egress`，仅**诚实标记** OPEN/BLOCKED，不阻断 |
| 缺口 | 同用户进程级隔离无法阻止 worker 建立外联 socket |
| remediation | 容器 `--network=none` + 断言测试：worker 内 socket 连外网**必失败**（P19「域外势能只能来自声明通道」的工程闭环） |
| 验收标准 | 四房容器模式下 selfcheck.egress == BLOCKED 且探测连接被内核级拒绝（非超时偶然） |
| 关闭条件 | 阶段 B CI 容器流水线落地并通过断言测试后，本条目转 RESOLVED 并追加 resolved_by |

### GAP-008 — 房间资源配额缺失

| 字段 | 值 |
|------|-----|
| classification | isolation_resource |
| status | OPEN |
| threat_ref | **T5**（死循环/内存膨胀拖垮宿主） |
| phase_target | B（容器资源限制） |
| 现状 | 阶段 A 仅有 `collect(timeout)`——只保证 controller 不无限等待，不限制 worker 实际 CPU/内存/进程数占用 |
| 缺口 | 恶意或失控 worker 可 fork 炸弹 / 内存膨胀影响同宿主其他房间与 controller |
| remediation | 容器 `--pids-limit=64 --memory=512m --cpus=1`；进程级配额（Job Object）暂不投入 |
| 验收标准 | 四房并跑时单房超限即被 cgroup 杀死并记入 `missing`，不波及其他房 |
| 关闭条件 | 阶段 B 配置进入 CI 强制流水线后转 RESOLVED |

---

## 4. 硬墙条目指针（不变）

GAP-001（SchanuelAt / AXIOM-001）元信息完整归档于注册表 `hard_wall_meta` 段，
季度重审到期 `2027-01-13`，未证明时动作 `CONFIRM_BARRIER`。详见 `config/gap_registry.yaml`。

---

## 5. 变更纪律

1. **禁止**直接编辑 `specimens/**/evidence/gap_ledger.yaml`（导出产物，会被覆盖）。
2. 新增/变更缺口：改 `config/gap_registry.yaml` → 升 `registry.version` → 跑 `tools/export_gap_ledger.py` → 更新本文档表格与过渡记录。
3. 状态跃迁（OPEN→SOLVABLE→RESOLVED）必须附 `resolved_by` 或 `remediation` 证据指针。
4. 数学缺口（GAP-001..006）与工程缺口（GAP-007/008）分域登记，禁止混判：工程收口不改变数学硬墙真值层级。

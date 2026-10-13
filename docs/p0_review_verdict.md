# P0 交付评审裁决文档

> 评审对象：P19-engine P0 可运行原型骨架（含阶段 A 隔离加固）
> 评审日期：2026-10-13 | 评审人：望易（主控编排） | 裁决版本：v1.0
> 快照锚定：工作区未 commit 状态（等人类指示提交）；证据以本文档 §3 哈希/命令输出为准

---

## 1. 裁决摘要

**裁决：有条件通过（CONFIRMED-WITH-CONDITIONS）。**

P0 骨架在进程级隔离边界内达成全部预注册验收项：四房间单向通道闭环、
math_attack_rules 契约求值、SHA256 哈希链真值台账、阴性/阳性/取消三标本自校验、
阶段 A 目录枚举阻断与违规熔断。**允许进入提交与阶段 B（CI 容器）准备。**

同时登记 2 项工程缺口（GAP-007/T2、GAP-008/T5，见 `docs/gap_ledger.md`），
作为阶段 B 前置条件约束后续边界扩张。

---

## 2. 评审范围

### 在范围内（本次裁决覆盖）

| # | 交付物 | 位置 |
|---|--------|------|
| 1 | 单向 YAML 协议（token + SHA256 + room 校验） | `p19_engine/protocol.py` |
| 2 | 四房间独立子进程 + 随机目录（128-bit）+ inbox/outbox 单向通道 | `rooms.py` / `room_worker.py` |
| 3 | 阶段 A 隔离加固（icacls `(RD)` 枚举阻断 + 自检 + 违规 FREEZED） | `isolation.py` |
| 4 | 八状态相变状态机 | `state_machine.py` |
| 5 | math_attack_rules v0.6 求值器（13 规则 + 级联 + FP 禁式 + 白名单） | `audit.py` |
| 6 | SHA256 哈希链 Append-only 真值台账 | `ledger.py` |
| 7 | 公理静态探针 + 硬墙裁决 | `discovery.py` |
| 8 | 一键闭环自校验 CLI | `run_p0.py` |
| 9 | 标本 001/002/003 + 外部语料 004（IPTTT 五层契约） | `specimens/` |
| 10 | GAP 注册表 v002（8 条）+ 导出工具 + 人读台账 | `config/gap_registry.yaml` / `docs/gap_ledger.md` |
| 11 | 测试套件 56 项 | `tests/` |
| 12 | 隔离方案评估与阶段路线 | `docs/sandbox_isolation.md` |

### 不在范围内（明确排除）

- 容器级隔离（阶段 B）、Docker/gVisor、CI 流水线
- 异构基座接入（DeepSeek/Claude/MiMo 等）
- 网络 API 探针（`--network` 系列，明令未做）
- 人脑接地界面、台账可视化
- GAP-001（Schanuel 硬墙）的数学求解——仅归档，不求解

---

## 3. 证据矩阵

| # | 验收项 | 证据 | 结果 |
|---|--------|------|------|
| E1 | 测试全绿 | `python -m pytest tests/ -q` → **56 passed, 0 warnings**（Python 3.14 / win32 / 2026-10-13） | ✅ |
| E2 | 三标本闭环 | `python -m p19_engine.run_p0 --specimen all` → 001=REJECT / 002=THEOREM-COND / 003=CANCELLED，四房投票一致 | ✅ |
| E3 | 台账链完整 | `ledger verify: OK (chain intact (3 entries))`，run `p0_20261013T010956Z` | ✅ |
| E4 | 审计命中精确 | 002 rule_hits == [MA-006, MA-006b, EV-TRUTH-GRADE]，hard_wall=GAP-001 | ✅ |
| E5 | 隔离一致性（Windows） | `icacls (RD)` 后 listdir→PermissionError、绝对路径读写正常、`/remove:d` 释放恢复、`rmtree` 通过——opencode 与 pytest-of 两棵 ACE 结构不同的树上行为一致 | ✅ |
| E6 | 隔离违规熔断 | 伪造兄弟报告 → collect 记 invalid → FREEZED 不写台账；worker 报 `sibling_enumeration != BLOCKED` → FREEZED（测试覆盖） | ✅ |
| E7 | GAP 链固化 | 导出 8 条，`tail=267ebde96725628f2caaba0d07ed505d29c294e5dd18b84e8c1f4431e74277e6`，`registry_sha256=a7a7559bd843b5e365d1a9277af06c56ab4f46c5af07de776abda28345727a01` | ✅ |
| E8 | 协议防伪 | token 不匹配 / room 不匹配 / msg_hash 篡改 / 未知房间均被 `ProtocolError` 拒绝（单测覆盖） | ✅ |
| E9 | 文档同步 | README P0 组件表、ROADMAP（UTF-8 重写）、sandbox_isolation、gap_ledger、audit_windows、specimen_library §4 | ✅ |

**验收标准对照**（ROADMAP Phase 0 P0 骨架清单）：10/10 勾选项达成。

---

## 4. 裁决依据与真值层级声明

1. 本次评审结论定性为 **`EMPIRICAL`（观测层级）**：依据是本机可复现的测试与运行输出，
   不构成 `THEOREM` 级数学断言，也不构成对外部世界的独立确权。
2. **C-02 纪律声明**：评审者（主控编排）与实现（EXP 编排链）运行于同一模型基座，
   本次裁决属**同基座内部复核**，不构成独立验证。
   独立性增量仅来自：预注册验收标准（先于实现锁定）+ 机械可复算证据（pytest/run_p0/导出工具哈希），
   不来自角色拆分本身。
3. 阴性结果未被丢弃：001（REJECT）与 003（CANCELLED）作为一等公民进入台账，与 002 并列。

---

## 5. 通过条件（约束后续阶段）

| # | 条件 | 绑定 | 截止点 |
|---|------|------|--------|
| C1 | GAP-007（egress 仅标记）收口：容器 `--network=none` + 外联断言测试 | `docs/gap_ledger.md` §3 | 阶段 B CI 落地前，**任何第三方观测器代码接入前强制** |
| C2 | GAP-008（资源配额）收口：容器 `--pids-limit/--memory/--cpus` + 超限杀死记入 missing | 同上 | 同上 |
| C3 | 阶段 A 残留纪律：异常中断后残留 deny 须以 `python -m p19_engine.isolation --release <run_dir>/rooms` 清理，禁止带残留提交 | `docs/sandbox_isolation.md` §5.1 | 每次提交前 |
| C4 | 本裁决仅覆盖上述 §2 在范围内清单；任何清单外主张（如"防住恶意第三方代码""独立验证"）**自动失效**，需重新评审 | 本文档 | 持续 |

条件未满足时的降级路径：阶段 B 前若强行接入第三方观测器代码，须将系统状态标记为
`UNSAFE-BOUNDARY` 并冻结台账写入（人工复审解锁）。

---

## 6. 后续路径建议（非强制）

1. **提交 P0 首版**（含本裁决文档与 GAP-002 条目）——等待人类指示，禁止自动 commit。
2. **阶段 B 启动**：CI runner 方案确认（GitHub Actions 免费额度 vs 自建 Linux 机）后，
   落地四容器 `--network=none` 流水线，同步关闭 GAP-007/008。
3. 阶段 B 通过后，再评估异构基座接入与 Specimen-004 的五窗口轮换实跑（`docs/audit_windows.md`）。

---

## 7. 签署

| 角色 | 主体 | 结论 | 日期 |
|------|------|------|------|
| 实现编排 | EXP 链（望易编排） | 交付完成，自检通过 | 2026-10-13 |
| 评审裁决 | 望易（主控） | **有条件通过**（同基座内部复核，C-02 声明适用） | 2026-10-13 |
| 人类确认 | （待签署） | 待定 | — |

> 人类确认栏留空：本裁决按 `docs/human_protocol.md` 被动等待，不主动请求升级。

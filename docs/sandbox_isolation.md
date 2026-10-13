# 容器沙箱隔离方案评估（阶段 A 设计依据）

> 评估日期：2026-10-13 | 状态：阶段 A 已落地（见 §5）| 决策人：望易
> 威胁模型锚点：C-02 同系统多 Agent 无效审计推论、P19 观测维度正交性

---

## 0. 前提事实（评估时核查）

- 评估时开发机（Windows）**未装 Docker、未装 WSL 发行版** → 任何容器方案需先补环境。
- 房间通信已全部走**文件单向通道（inbox/outbox）**，worker 不需要网络 → 容器 `--network=none` 可零成本落地。
- 真值台账 / 仲裁只由 controller（房外）执行 → ledger 天然不进沙箱。

## 1. 威胁模型（决定要防什么）

| # | 威胁 | 来源 | 评估时状态 |
|---|------|------|-----------|
| T1 | 房间间串通 / 偷看兄弟 outbox | C-02 核心关切 | 同用户进程可读兄弟目录，**未防** |
| T2 | 房间外联（搜题 / 泄题 / 拉数据） | 观测正交性被污染 | 进程级**未防** |
| T3 | 房间代码打内核 / 宿主逃逸 | 现为一方代码风险低；**接第三方观测器后升高** | 未防 |
| T4 | 消息伪造 / 重放 | 恶意房间伪造 verdict | **已防**（token + SHA256 + room 校验） |
| T5 | 资源饥饿（死循环吃满 CPU） | worker 卡死拖垮全局 | 仅 timeout，**无配额** |

## 2. 候选方案矩阵

| 方案 | T1 横向 | T2 外联 | T3 逃逸 | Windows 本机可行 | CI 可行 | 启动开销 | 复杂度 | 许可 |
|------|--------|--------|--------|----------------|--------|---------|--------|------|
| 进程级（评估时基线） | 弱 | ✗ | ✗ | ✅ | ✅ | ~50ms | 已有 | 免费 |
| Docker + runc | ✅ namespace | ✅ `network=none` | △ 共享内核（runc CVE 史） | △ 需 Docker Desktop+WSL2 | ✅ 原生 | ~0.5–1s/房 | 低 | Desktop 超 250 人/1000 万美元收费 |
| Podman rootless | ✅ 同 runc | ✅ | △ | △ 免许可仍需 WSL2 | ✅ | 同上 | 低 | **免许可** |
| Docker + gVisor(runsc) | ✅ | ✅ | ✅ 用户态内核截 syscall | ✗ 不能原生跑 | ✅（Linux runner） | ~1–2s/房 | 中 | 免费 |
| Kata / Firecracker 微虚机 | ✅ | ✅ | ✅✅ 每房独立内核 | ✗ | ✅ | ~2–5s/房 | 高 | 免费 |
| Windows 原生（AppContainer/Hyper-V 隔离容器） | ✅ | △ | ✅ | ✅ Python 生态差 | ✗ runner 不便 | 中 | 高 | 免费 |

## 3. 决策：分层推进，不一步到位

**T1/T2 是现阶段主要矛盾（C-02 观测正交），T3 是将来接第三方代码才升级。**

| 阶段 | 方案 | 理由 |
|------|------|------|
| **A（本次落地）** | 进程级加固：每房独立 128-bit 随机目录 + `icacls` 父目录 deny-list 阻断枚举 + worker 隔离自检（兄弟枚举 / egress 探测标记）+ 隔离一致性测试 | 成本≈0，T1 收敛到「目录层不可枚举 + 协议层 token 拒伪造」双保险；T2 先标记（诚实可见），阶段 B 收紧 |
| **B（首选强制点）** | GitHub Actions `ubuntu-latest` + 4 容器并跑：`--network=none --read-only --cap-drop=ALL --security-opt no-new-privileges --pids-limit=64 --memory=512m --cpus=1`，specimen 只读挂入，inbox/outbox 用 tmpfs/bind | T1+T2+T5 全覆盖；隔离在 Linux 侧成立，开发仍在 Windows 跑进程级 |
| **C（本地容器，可选）** | Podman machine（免许可）或 Docker Desktop（注意许可证），WSL2 后端 | 本地复现容器行为时用 |
| **D（第三方观测器接入时）** | 升级 gVisor（runsc）；Kata 仅在跑不可信二进制时才值得 | T3 升级点 |

**否决项**：

- **Windows 原生容器**：Python 镜像生态差、CI 不便。
- **现在就上 Kata/Firecracker**：启动开销与复杂度对一方代码是浪费。

## 4. 关键实现约束

1. worker 参数传 host 绝对路径 → 容器模式（阶段 B）需 controller 先把 specimen 暂存进沙箱可见挂载点（dispatch 语义不变，只改路径映射）。
2. `--network=none` 下必须加**断言测试**：worker 内 socket 连外网必失败 —— 这是 P19「域外势能只能来自声明通道」的工程闭环（阶段 B 落实；阶段 A 以 egress 探测标记代替）。
3. 镜像基座 `python:3.12-slim` + `mpmath`；room code 只读挂载，避免房内改规则文件。
4. 台账 ledger **永不挂进容器**（controller 独占）—— 对应「房内无法自写真值」。

---

## 5. 阶段 A 落地记录（2026-10-13）

### 5.1 机制

| 项 | 实现 | 文件 |
|----|------|------|
| 每房独立随机目录 | `run_dir/rooms/<128-bit hex>/`，映射仅存于 controller 内存，不落盘 | `p19_engine/rooms.py` |
| 父目录枚举阻断 | `icacls rooms /deny "<DOMAIN\user>:(RD)"`（不可继承，**只拒 list-directory**）；listdir → `PermissionError`，绝对路径读写与 icacls 回读 DACL 均不受影响 | `p19_engine/isolation.py::apply` |
| 自校验 | apply 后 controller 亲自 `os.listdir` 必须失败，否则 `IsolationError` 立即 fail-fast | 同上 |
| 协议层防伪 | 房间 token（已有）+ 随机目录名不可猜（128-bit，listdir 已阻断）双保险 | `protocol.py` |
| worker 自检 | 启动时 `selfcheck()`：① 兄弟枚举 `BLOCKED/OPEN` ② egress 探测 `OPEN/BLOCKED`（0.3s 超时，连 1.1.1.1:443）；写入 `claims.isolation_selfcheck` | `p19_engine/room_worker.py` |
| 违规熔断 | Windows + ACL 模式下，任一 worker 报 `sibling_enumeration != BLOCKED` → FREEZED，不写台账 | `orchestrator.py` |
| 运行痕迹 | `run_dir/isolation.json`：runtime ACL 状态 + 四房自检 | 同上 |
| 幂等释放 | run 结束 `finally` 必调 `release()`（`icacls /remove:d`），否则残留 deny 会阻断 `rmtree`/pytest 清理；异常残留手动 `python -m p19_engine.isolation --release <run_dir>/rooms` | `isolation.py::release` |
| 平台回退 | 非 Windows：`mode=fallback`，诚实记录 `OPEN`，不熔断（Linux 侧强制力由阶段 B 容器承担） | `isolation.py` |

### 5.2 本机 ACL 实测结论（PowerShell + Python 双验证）

- `icacls <dir> /deny "FLYE\Administrator:(RD)"` 后：`os.listdir` → `PermissionError` ✅
- 子目录绝对路径读 / 写 / 新建（deny 之后新建也正常）✅
- 穿越父目录打开已知子路径 ✅（deny 只封枚举，不封已知路径）
- `/remove:d` 释放后 listdir 恢复，`rmtree` 正常 ✅

> **踩坑记录（(R) → (RD) 的原因）**：初版用 generic `(R)`，它把 `READ_CONTROL` 一并拒掉，
> 导致 `icacls /remove:d` 无法回读 DACL 而失败（rc=5 拒绝访问），释放不了、rmtree 清不掉。
> 且该现象**依赖目录树 ACE 结构**：`Temp\opencode`（命名用户 ACE）树上隐式 owner 权限可豁免，
> `Temp\pytest-of-Administrator`（`OWNER RIGHTS:(I)(OI)(CI)(F)` 结构）树上不可豁免——
> 同一命令、同一用户、同一机器，行为不一致，排查耗时。
> 最终方案 `(RD)` = 只拒 `FILE_LIST_DIRECTORY`：枚举被封、READ_CONTROL 保留、释放可靠，两棵树一致。
> 任何残留污染目录（旧 `(R)` 实验遗留）可用 `icacls <dir> /remove:d <user>` 或 takeown 后清理。

> 边界说明：deny-list 只能阻断**发现**兄弟路径；已知路径的直接打开仍受子目录自身 ACE 放行。
> 因此必须叠加 128-bit 随机名（不可猜测）+ 协议 token（打开也写不进）两层。

### 5.3 一致性测试清单（`tests/test_isolation_conformance.py` + e2e）

1. apply 后 rooms 根 listdir 必须 `PermissionError`，释放后恢复
2. 房间 ID 128-bit 随机且互不相同
3. worker argv 只含自身路径，不含任何兄弟房间路径
4. 自检在 ACL 下报告 `BLOCKED`
5. 伪造兄弟报告写入 outbox → collect 记为 invalid → FREEZED
6. 非 Windows 回退模式行为
7. e2e：四房 `isolation_selfcheck.sibling_enumeration == BLOCKED`，`isolation.json` 落盘

### 5.4 阶段 B 前的遗留

- [ ] T2 仍为「标记」而非「阻断」—— 容器 `--network=none` 落实时加断言测试
- [ ] T5 资源配额（容器 `--pids-limit/--memory/--cpus`；进程级暂缺）
- [ ] T3 等第三方观测器接入时升级 gVisor
- [ ] Linux 开发机上阶段 A 的 FS 层退化为 fallback（同 uid 不可 deny）→ 阶段 B 容器为强制点

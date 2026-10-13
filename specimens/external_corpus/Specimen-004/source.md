# 引理归档 — β ≤ 7/8 反证链（`beta_le_seven_eighths`）

> Family 003（准黎曼假设）核心矛盾引理的独立数学推导归档。
> Lean 主引理：`OAI.SevenEighths.HeckeCommonProbe.beta_le_seven_eighths`
> 源码：`math-main/lean/OAI/NumberTheory/DirichletL/Hecke/CommonProbe.lean:27`
> 归档性质：**EMPIRICAL（对既有 Lean 定理的重述，非新定理）**；严格化以机器验证为准。

---

## 0. 记号约定

K = ℚ(√−3)，O = 𝒪_K = ℤ[ζ₃]。χ 为 O 上有限阶乘法特征（`Character`），L(s, χ) 为其 Hecke L-函数（`Hecke/IdealBridge.lean:95`：`L χ s = 格系数级数 / 6`）。`signal_{χ,H}(x) = signal χ H c (x)` 为信号函数，c 为常数（核心推导取 c = −11/16）。

本推导只使用实数上确界、O-记号（asymptotic big-O at ∞）与全纯函数解析延拓。

---

## 1. 零点实部集合与 β（`Hecke/ZeroSupremum.lean`）

定义零点实部集合（排除主特征 s=1 处的极点）：

```
Z = { x ∈ ℝ | ∃χ, ∃s:ℂ, 0<Re s ∧ (s≠1 ∨ χ.residue≠1) ∧ L(s,χ)=0 ∧ Re s = x }
```

加入哨兵点 1/2 保证非空：

```
S = {1/2} ∪ Z,      β := sup S
```

导出事实（均已机械化）：

| 事实 | 内容 | Lean 位置 |
|---|---|---|
| (F1) | 1/2 ≤ β ≤ 1 | `ZeroSupremum.lean:33,36`（上界来自 Re s > 1 无零点） |
| (F2) | 任一零点实部 ≤ β：L(ρ,χ)=0 且非极点 ⟹ Re ρ ≤ β | `ZeroSupremum.lean:43` `zero_re_le_beta` |

**引理 L0（单侧判定）**：若 β < Re s 且 (s≠1 ∨ χ.residue≠1)，则 L(s, χ) ≠ 0。
*证明*：反设 L(s,χ)=0，则 Re s ∈ Z ⊆ S，由 (F2) 得 Re s ≤ β，与 β < Re s 矛盾。（`ZeroSupremum.lean:48`）

---

## 2. 压缩性假设 UniformCommonProbe（`CommonProbe.lean:13`）

针对**本原**特征（`FiniteFourier.IsPrimitiveOnIdeals`）的压缩契约 `PrimitiveContract ω σ`：

```
∀η 本原，∃(χ, H, J)：
  (M)  掩码：∀I, coeff_χ(I) = [IsCoprime(I, modχ)] · coeff_η(I)
                         （χ 仅保留 η 中与 modχ 互素的理想系数）
  (A1) H 在 {Re s > 7/8} 上解析，且 ‖H s − 1‖ ≤ 1/2
  (A2) J(x) = O(x^(3/16 + ω))
  (A3) J(x) − signal_{χ,H}(x) = O(x^(β − 11/16 − σ))
```

统一压缩性命题：

```
(UCP)  7/8 < β ⟹ ∃ω σ, 0<ω ∧ ω<β−7/8 ∧ 0<σ ∧ PrimitiveContract ω σ
```

> 注：UCP 非自由假设。由认证机器对每个 β>7/8 **构造**（`FinalAssemblyChosenData.lean:57` `common_probe_of_chosen_moments`）：取 ω=(β−7/8)/2、σ=D.sigma，经 `HighData D`（κ_plain=3/4+2Δ）与 SourceMoment 估计产出探针 J 与压缩因子 H。故下述反证的适用域严格为「UCP ⇒ β≤7/8」。

---

## 3. 反证主链：β ≤ 7/8（`CommonProbe.lean:27`）

反设 **7/8 < β**。由 (UCP) 取 ω, σ 满足 0<ω<β−7/8、0<σ、PrimitiveContract ω σ。

**Step 1 — 延拓余量 mg。**（`Supremum.lean:10`）

$$\mathrm{mg} := \min\big(\beta-\tfrac78-\omega,\ \sigma\big).$$

由 ω<β−7/8、σ>0 ⟹ **mg > 0**（`continuationMargin_pos`）；又 mg ≤ β−7/8−ω、ω>0 ⟹

$$\tfrac78 < \beta - \mathrm{mg}. \tag{boundary_gt}$$

**Step 2 — β 附近的本原零点。**（`PrimitiveSupremum.lean:46`）

β 亦为本原零点实部集合的上确界（`beta_eq_primitive_supremum`）。由 mg>0，上确界逼近给出**本原** η 与 ρ：

$$\text{Primitive}(\eta),\quad \tfrac12 \le \Re\rho \le 1,\quad (\rho\ne1 \lor \eta_{\text{res}}\ne1),\quad L(\rho,\eta)=0,\quad \boxed{\ \beta-\mathrm{mg}<\Re\rho\ }.$$

直观：β 是零点实部上确界，把 ε=mg 挤进 sup，零点的实部必落入 (β−mg, β]。

**Step 3 — 压缩到平凡 χ。**（`CommonProbe.lean:34`；`FiniteDeletion.lean:126`）

对 (Step 2) 的本原 η 施加 PrimitiveContract ⟹ (χ, H, J) 满足 (M)(A1)(A2)(A3)。由掩码：
- 特征互传：χ 主 ⇔ η 主（`principal_iff_of_mask`）⟹ ($\rho\ne1 \lor \chi_{\text{res}}\ne1$)；
- 零点保持：0<Re ρ，剔除系数仅差互素因子（`factors_ne_zero`）⟹

$$L(\rho,\chi)=L(\rho,\eta)\cdot\text{factors}=0. \tag{LFunction_eq_of_mask_nonpole}$$

得到关键项 **L(ρ, χ) = 0**。

**Step 4 — 探针非零引理（矛盾点）。（`SignalIdentity.lean:103`）**

引理 `nonzero_of_probe_bounds`（取 c=−11/16）的正前提：

```
β≤1,  0<ω<β−7/8,  0<σ,
H 在 {Re>7/8} 解析 且 ‖H s−1‖≤1/2,
J = O(x^(7/8+c+ω)),   J−signal = O(x^(β+c−σ)),
β−mg < Re ρ,   ρ≠1 ∨ χ非主
⟹  L(ρ, χ) ≠ 0
```

代入 c=−11/16：

- 7/8 − 11/16 = **3/16** ⟹ (A2) 恰为 J = O(x^{3/16+ω})；✓
- β − 11/16 ⟹ (A3) 恰为 J − signal = O(x^{β−11/16−σ})；✓
- β−mg<Re ρ 由 Step 2 给出；✓

故探针返回 **L(ρ, χ) ≠ 0**。

**Step 5 — 矛盾。** Step 3 给出 L(ρ,χ)=0，Step 4 给出 L(ρ,χ)≠0。反设 7/8<β 不成立：

$$\boxed{\ \beta \le \tfrac78.\ }$$

---

## 4. Step 4 内部机制：探针为何必然非零（`Continuation.lean:92,130`）

三步：主项吸收 → 解析恒等式延拓 → 端点代入。

**(i) 信号主项吸收**（`common_signal_bound`，`Continuation.lean:37`）。由 J 与 J−f 上界：

$$a := \beta-\mathrm{mg}, \qquad f = O\big(x^{\,a+c}\big).$$

故 Mellin 变换 $M(s)=\int_0^\infty f(x)\,x^{-(s+c)}\,dx$ 在 {Re s > a} 上解析（`signalMellin_analytic`）。

**(ii) 解析恒等式（半平面延拓）。** 引入正则化函数

$$\text{RegL}_\chi(s)=\begin{cases}\text{polRemoved}\,L_\chi(s),&\chi\ \text{主}\\ L(s,\chi),&\chi\ \text{非主}\end{cases}, \qquad R_\chi(s)=\begin{cases}s-1,&\chi\ \text{主}\\ 1,&\chi\ \text{非主}\end{cases}$$

满足 $\text{RegL}_\chi(s)=R_\chi(s)\,L(s,\chi)$；且对 Re s > max(a,1) 有乘积恒等式（`poleRemoved_mul_signalMellin`）：

$$\text{RegL}_\chi(s)\cdot M(s)=R_\chi(s)\cdot\underbrace{e^{(s-5/6)^2}H(s)}_{\text{gaussianMultiplier}}.$$

两端在 {Re s > a}（连通半平面）上解析且于子开集相等 ⟹ 处处相等（`product_identity_on_halfPlane`）。因 a<Re ρ，恒等式在 ρ 处成立。

**(iii) ρ 处代入得非零。** 反设 **L(ρ,χ)=0**，则左端

$$\text{RegL}_\chi(\rho)\cdot M(\rho)=R_\chi(\rho)\,L(\rho,\chi)\cdot M(\rho)=0.$$

右端三项均非零：
- $R_\chi(\rho)\ne0$：由 ρ≠1 ∨ χ非主（`targetRegularizer_ne_zero`）；
- $e^{\cdot}\ne0$；
- $H(\rho)\ne0$：‖H(ρ)−1‖≤1/2（`multiplier_ne_zero`）。

右端 ≠ 0，矛盾 ⟹ **L(ρ,χ) ≠ 0**。∎

---

## 5. 矛盾链完整骨架（认证 → 结论）

```
detector_certified_bands : DetectorCertifiedBands     …巨型认证计算（掩码/能量/矩估计）
   ↓ certified_terminal / source_moments
fine_moments_of_certified : FineMomentInput
   ↓ chosen_input_of_fine
chosen_moments_of_certified : ChosenMomentInput        …选定 HighData D, κ_plain=3/4+2Δ
   ↓ common_probe_of_chosen_moments  (FinalAssemblyChosenData.lean:57)
UniformCommonProbe                                     …§2 压缩性被构造
   ↓ beta_le_seven_eighths（§3 反证）
β ≤ 7/8
   ↓ (§1 L0) ∀χ, β<Re s ⟹ L(s,χ)≠0
hecke_ne_zero_of_common_probe / dirichlet_of_common_probe / zeta_of_common_probe
   ↓ (Dirichlet→Hecke 乘积, Hecke/Dirichlet.lean:158,171)
dirichlet_nonzero / zeta_nonzero                      …无 β 的绝对非零定理
```

一句话版：

> 反设零点上确界 β 越过 7/8 ⟹ 能量/压缩机器在 β 附近产出「压缩零点」(Step3) ⟹ 探针引理在同一 ρ 上强制非零 (Step4) ⟹ 矛盾 ⟹ β≤7/8 ⟹ Re s>7/8 无零点。

---

*归档：Family 003 · β≤7/8 反证链 · 依附审计 AUDIT-003 · 性质 EMPIRICAL（定理复述）*
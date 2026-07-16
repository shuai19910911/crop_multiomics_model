# 作物多组学预训练研究进展

- 文档版本：v2.0
- 最后更新：2026-07-16
- 总体状态：阶段0 `COMPLETE`；阶段1 `READY / NOT STARTED`；模型训练 `NOT STARTED`
- 配套文件：[研究计划](RESEARCH_PLAN.md) · [候选模型架构](MODEL_ARCHITECTURE.md)

> 最重要的事实：目前完成的是研究治理和执行前检查体系，不是模型训练。真实训练run=0、参数更新=0、GPU小时=0、checkpoint=0、性能指标=0。

## 0. 零基础读者如何阅读本页

建议按顺序阅读：

1. “当前状态总览”——项目究竟做到哪里；
2. “已经完成了什么”——每项完成工作的实际含义；
3. “尚未完成的工作”——避免把治理完成误解为模型完成；
4. “训练曲线”——为什么有坐标轴但没有曲线；
5. “当前阻塞及解除条件”——还差什么证据；
6. “下一步执行清单”——接下来按什么顺序做。

状态不是一条混合刻度，而是四个独立轴；同一工作流可同时写成`VERIFIED / COMPLETE / AUTHORIZED / FROZEN`等组合：

| 状态轴 | 允许值 | 白话含义 |
|---|---|---|
| 证据轴 | `VERIFIED` / `UNKNOWN` | 已有可核机器证据 / 尚无证据，不能猜 |
| 执行轴 | `NOT STARTED` / `READY` / `RUNNING` / `COMPLETE` / `ERROR` / `BLOCKED` | 尚未开始 / 前提已备 / 正在执行 / 已完成 / 执行错误 / 前置条件不足 |
| 授权轴 | `AUTHORIZED` / `NOT AUTHORIZED` | 当前规则允许 / 禁止进入该动作 |
| 设计轴 | `CANDIDATE` / `FROZEN` | 候选方案 / 已由合同和hash冻结 |

`READY`不等于`AUTHORIZED`，`COMPLETE`也不等于整个项目完成；例如阶段0可为`VERIFIED / COMPLETE`，阶段1检索为`READY / AUTHORIZED`，训练则为`NOT STARTED / NOT AUTHORIZED`。

本页高频术语：

| 术语 | 白话解释 |
|---|---|
| run | 一次有唯一ID、配置和日志的独立运行 |
| optimizer update | 优化器根据梯度真正修改一次模型参数 |
| checkpoint | 某一步保存的模型参数文件 |
| manifest | 登记样本/文件身份、版本和来源的清单 |
| receipt | 带路径、时间和hash的机器执行证据 |
| seal | 把外测来源、样本、标签和访问规则绑定后封存 |
| consumer | 读取数据并影响训练、预处理或模型选择的程序 |
| headline task | 论文主结论直接依赖的核心任务 |
| pilot | 只在validation范围运行的小预算试验，不是正式测试 |
| P0 / P1 | 阻断级问题 / 高优先级问题 |

“写了计划”不等于“执行了任务”，“空表有表头”不等于“已经有数据”，“测试通过”也不等于“模型精度通过”。

同样，单个脚本、图件或表格通过检查只叫“组件PASS”；只有某阶段全部输入、产物、receipt、统计和失败出口闭合，才能叫“阶段/Gate PASS”。

## 1. 当前状态总览

### 1.1 一句话状态

项目已完成阶段0的资源边界以及统计、许可、外测和防泄漏**规则/治理代码**，并通过R13终审；尚未审查任何真实训练数据、真实模型结果或正式外测。现在只允许实现阶段1缺失接口、运行check-only和有界首屏smoke；完整分页、证据处理和最终receipt仍为`TBD / MANUAL-BLOCKED`。不允许数据晋升、GPU训练、大规模下载或正式测试。

### 1.2 工作流状态

| 工作流 | 当前状态 | 已经有什么 | 还缺什么 | 变为PASS的条件 |
|---|---|---|---|---|
| 阶段0治理 | **COMPLETE** | 91项冻结闭包、R13终审、完成receipt | 无 | 已满足 |
| 系统文献检索 | GOVERNANCE READY / EXECUTION BLOCKED | 来源、12个query族、check-only/首屏smoke组件、双筛规则 | 完整分页/证据处理/final receipt producer及全部真实run | 阶段1 gate PASS |
| 现有模型核验 | GOVERNANCE READY / EXECUTION BLOCKED | 候选名称、核验字段和流程设计 | 可执行证据处理接口，以及官方论文、代码、权重、模型卡和许可 | 五类证据均核验；缺失项显式记`ABSENT` |
| 数据目录 | BLOCKED | 92列样本schema、官方来源probe计划 | 非空元数据、accession.version、访问receipt | 阶段2获授权且目录非空 |
| 许可审计 | BLOCKED | 许可状态机和receipt格式 | 条款文本、证据定位、人工复核 | 用途明确允许或限制已满足 |
| 多组学配对 | BLOCKED | P1—P4/PX和重复折叠规则 | 实体ID、split aliquot或官方映射 | 可核验配对范围形成 |
| MVP范围 | NOT STARTED | 三方案决策框架 | 阶段1—2证据和用户评审 | 作物、模态、任务、单位、基线冻结 |
| 模型架构 | CANDIDATE / NOT FROZEN | 概念图和候选模块 | 数据形态、任务、token、规模、loss | 阶段3—4合同PASS |
| 统计功效 | BLOCKED | 联合power函数和pilot协议待阶段4冻结 | 阶段5后真实validation pilot和baseline winner | 阶段6 power receipt通过 |
| 训练 | NOT STARTED | 实验注册schema和门禁 | 数据、许可、split、架构、power、预算 | 前置门禁全部PASS |
| 正式外测 | NOT AUTHORIZED | seal、防火墙、freeze、一次性claim协议 | task/seal/consumer/power、stage6/7总receipt及winner/随机初始化/强基线完整比较矩阵 | formal-pretest PASS＋唯一claim |
| 论文/最终交付 | NOT STARTED | 结论边界和交付要求 | 真实结果、失败分析、数据卡/模型卡 | 阶段8证据闭合 |

### 1.3 关键数字

| 指标 | 当前值 | 正确解释 |
|---|---:|---|
| 阶段0终审文件 | 91 | 冻结审查范围，不是数据样本数 |
| P0/P1问题 | 0/0 | 没有阻断级或高优先级终审问题 |
| 规范测试 | 56项通过 | 验证治理代码，不验证模型性能 |
| 模型训练run | 0 | 没有启动模型训练 |
| optimizer update | 0 | 参数没有更新过 |
| GPU小时 | 0 | 没有消耗GPU训练时间 |
| checkpoint | 0 | 没有模型权重可选择或发布 |
| 训练曲线观测点 | 0 | CSV只有表头，无模拟点 |
| 正式测试次数 | 0 | 外测标签从未获准打开 |

## 2. 机器证据快照

| 证据 | 当前值 |
|---|---|
| 阶段 | `STAGE0` |
| 状态 | `COMPLETE` |
| Review ID | `STAGE0-20260716-R13` |
| 冻结manifest SHA-256 | `1fcc6811af07b805d328c9bdf06b898e3af95a31c70eed0964e456809de40633` |
| 终审receipt SHA-256 | `dc6e815672df33425542f723c3336f7fc8645338dfabcc345be594dd119274da` |
| Reviewed file count | 91 |
| 阶段1治理授权 | `true` |
| 阶段2数据晋升授权 | `false` |
| GPU/大下载授权 | `false` |
| Formal test授权 | `false` |

哈希相当于内容的数字指纹。被冻结内容改变后，哈希也会改变，旧终审不能自动为新内容背书。本公开仓库只发布脱敏摘要和hash，不发布内部审计工作区路径；因此外部读者仅凭本页不能独立复验91文件和R13内容，必须取得对应内部manifest/receipt后才能用hash核对。这里的hash是治理证据摘要，不是模型效果证据。

## 3. 已经完成了什么

### 3.1 项目从零重启和范围边界

**状态：VERIFIED**

项目从空白状态重新设计，不继承旧项目的数据、代码、模型、结论或路线。旗舰作物、模态、token单位、headline任务、架构、参数量和“基础模型”资格均保持开放。

**为什么重要？** 防止先选模型再寻找能证明模型有效的问题和数据。

### 3.2 资源与运行环境审计

**状态：VERIFIED**

已对登录节点、计算节点、Slurm、共享文件系统、软件环境、网络和容器做轻量只读审计。当前唯一experiment记录是工程审计：

- ID：`AUDIT-S0-0001`；
- purpose：计算节点只读资源与环境审计；
- data：`NO_DATA`；
- model：`NO_MODEL`；
- GPU：`NONE`；
- GPU hours：0；
- 结果：PASS。

它只证明运行环境经过有限检查，不证明数据可用、模型可训练或性能达标。

### 3.3 阶段1系统文献检索准备

**状态：GOVERNANCE READY / EXECUTION BLOCKED**

已完成的是开放来源角色、12个query族、单来源check-only/首屏smoke组件，以及全矩阵、重试、去重、版本链、双筛裁决、全文—代码—权重—模型卡—许可核验的**配置和流程设计**。完整分页、证据处理和final receipt producer仍为`TBD / MANUAL-BLOCKED`，不能把设计稿称为可执行脚本；所有真实任务均未完成，尚无阶段1 PASS。

尚未完成：没有真实search receipt、命中数、导出、双筛、全文核验或可复用模型结论。因此不能声称“综述发现某模型最好”或“某权重可直接使用”。

### 3.4 数据身份和样本manifest设计

**状态：READY / BLOCKED FOR REAL DATA**

已建立92列空样本manifest schema，要求记录数据库与Study/BioProject/BioSample/Run/file ID、物种与种质、site-year-trial、plot/individual、biological sample、组织/时期/处理、随机化/block/重复/复合取样、assay/平台/批次、assembly/注释/坐标版本、许可、配对、QC、split和外测状态。

该schema只是空表结构，不是样本数据。表头完整不代表字段已经取得。

### 3.5 许可治理

**状态：READY / BLOCKED FOR EVIDENCE**

已定义：

`UNKNOWN_NO_TRAIN → LOCATED → TEXT_CAPTURED → REVIEWED_ALLOWED / REVIEWED_RESTRICTED / REVIEWED_FORBIDDEN / NEEDS_PERMISSION`

每次变化必须保留前后状态、条款快照、hash、时间、reviewer和证据位置；下载、训练、商业使用、衍生权重、数据/权重再分发分别判断。当前无真实数据集进入复核，未来数据默认`UNKNOWN_NO_TRAIN`。

### 3.6 多组学配对和重复折叠

**状态：READY / BLOCKED FOR REAL IDENTITIES**

P1表示同一实体/明确分样，P2表示近似条件，P3表示非配对同分布，P4表示弱锚，PX表示冲突/证据不足。严格cross-modal alignment只允许P1。

已预警常见伪配对：同品种跨个体/年份、bulk和单细胞只按组织名、处理时间不一致、不同assembly同名基因、多倍体homeolog误折叠、跨库重复提交。当前没有真实配对边，不能报告P1数量。

### 3.7 统计和模型选择合同

**状态：READY / BLOCKED FOR TASK AND PILOT**

每个headline task在formal test前要冻结候选全集、五类标签证据、独立单位、重复折叠、split最小单位、主要指标、最小效应、最强baseline、配对比较、95% CI、Holm校正、至少5 formal seeds和联合power receipt。阶段4只冻结函数/协议，真实pilot和power必须在阶段5数据冻结后的阶段6产生。

当前任务和pilot尚未冻结，不能填写任务指标或power。

### 3.8 外部测试seal和防泄漏

**状态：GOVERNANCE READY / REAL TEST NOT AUTHORIZED**

已建立外测六类hash绑定、真实consumer输入登记、11类泄漏轴检查、winner/同架构随机初始化/预注册强基线完整比较矩阵冻结、stage6/7聚合Gate receipt、非外测fixture `formal_pretest_gate.json`、external identity＋claim两级append-only registry和后置formal-claim核验。当前这些都只是治理合同：无真实seal、stage6/7/pretest receipt、consumer receipt、registry消费记录或claim，正式测试访问仍为false。

### 3.9 R13终结审查

**状态：VERIFIED / COMPLETE**

阶段0经实现一致性、科学/统计和TDD三路复核，最终拒绝悬空符号链接、FIFO等非普通文件进入闭包。结果为P0=0、P1=0、91文件闭包稳定、completion=`COMPLETE`。只允许进入阶段1治理。

## 4. 尚未完成的工作

- 未执行真实系统文献检索；
- 未形成文献证据矩阵；
- 未核验任何模型可复用；
- 未建立非空数据目录；
- 未完成人工许可复核；
- 未形成真实P1配对；
- 未选旗舰作物/MVP模态；
- 未冻结headline任务、标签和独立单位；
- 未冻结架构、参数量、loss和训练预算；
- 未运行baseline、pilot或训练smoke；
- 未保存checkpoint；
- 未进行validation/formal test；
- 没有模型性能或生物学发现。

## 5. 数据和模型结果表

当前没有结果，用`N/A`而不是0，避免被误解为“性能等于0”。

| 类别 | 项目 | 当前值 | 原因 |
|---|---|---|---|
| 数据 | 训练样本数 | N/A | 数据未准入 |
| 数据 | P1严格配对数 | N/A | 身份审计未执行 |
| 数据 | 外测独立单位数 | N/A | 外测未seal |
| 模型 | 参数量 | N/A | 架构未冻结 |
| 模型 | 训练token/样本数 | N/A | 输入单位/数据未冻结 |
| 训练 | train loss | N/A | 0训练run |
| 训练 | validation score | N/A | 0训练run |
| 训练 | checkpoint | N/A | 未训练 |
| 评价 | baseline指标 | N/A | baseline未运行 |
| 评价 | 预训练指标 | N/A | 模型未实现 |
| 评价 | 外测指标 | N/A | formal test未授权 |
| 统计 | 95% CI | N/A | 无真实配对预测 |
| 统计 | power | N/A | 无validation pilot |

## 6. 训练曲线和数据来源

![Training progress](docs/assets/figure_generations/6a0047ecb939a2b119aef75ef1d29d9bd1a4c9332e2452c7430d6829cd195e09/training_progress.png)

下载：[PNG](docs/assets/figure_generations/6a0047ecb939a2b119aef75ef1d29d9bd1a4c9332e2452c7430d6829cd195e09/training_progress.png) · [PDF](docs/assets/figure_generations/6a0047ecb939a2b119aef75ef1d29d9bd1a4c9332e2452c7430d6829cd195e09/training_progress.pdf) · [源CSV](docs/assets/training_curve_source.csv) · [状态JSON](docs/assets/training_status.json)

### 6.1 为什么有坐标轴但没有线？

坐标轴预留未来真实曲线位置；`NO OBSERVATIONS`表示0 run、0 update、0 GPU小时、0 checkpoint、0模拟loss、0模拟validation score。

### 6.2 为什么不画示意曲线？

图片脱离正文后，示意曲线容易被误认为结果。本项目只发布可追溯点，因此源CSV当前只有表头。

### 6.3 第一条真实曲线需要哪些证据？

每个点至少绑定：experiment/run ID、数据manifest/hash、split ID/hash、模型配置/hash、code commit、环境锁、seed、日志/checkpoint/hash、selection set/metric、Slurm Job ID、GPU和资源记录。

未来图A显示训练mini-batch loss，图B显示冻结validation指标。正式测试指标不进入训练曲线，也不参与checkpoint选择。

## 7. 已回答和开放问题

### 已回答

- 是否从零开始？——是。
- 阶段0是否完成？——是，R13 COMPLETE。
- 是否允许阶段1？——允许治理和检索。
- 是否允许GPU/大下载？——不允许。
- 是否有模型性能？——没有。
- 外测能否反复查看？——不能。
- 许可UNKNOWN的数据能否训练？——不能。

### 仍开放

旗舰作物、首版模态、token单位、headline任务、独立单位、fusion路线、预训练目标、模型规模/预算、是否复用权重、是否满足“基础模型”资格。

## 8. 当前阻塞及解除条件

| Blocker | 为什么阻塞 | 解除证据 | 解除后允许 |
|---|---|---|---|
| B1 无检索receipt | 不知道证据覆盖是否真实 | query、导出、hash、双筛、全文核验 | 证据综合 |
| B2 无非空官方元数据 | 不知道样本/模态是否存在 | accession.version、官方响应、访问receipt | 建数据目录 |
| B3 许可未知 | 可能不允许训练/发权重 | 条款、证据定位、人工receipt | 合规准入 |
| B4 实体配对未知 | 可能把不同样本当同样本 | BioSample/aliquot身份边和条件一致性 | 评估P1/P2 |
| B5 任务未冻结 | 无法决定标签/split/指标 | headline task和统计合同 | baseline/pilot |
| B6 架构未冻结 | 无法解释输入输出和预算 | 阶段3决策＋阶段4合同 | 实现MVP |
| B7 无pilot | 无法估计方差/power | validation-only baseline/pilot预测 | power receipt |
| B8 外测未seal | 正式结果可能泄漏 | seal、registry、防泄漏receipt | formal-pretest |

解除一个blocker不自动解除其他blocker。找到数据不等于许可允许，也不等于样本可配对。

## 9. 下一步执行清单

当前唯一允许推进的是阶段1：

| 顺序 | 动作 | 产物 | 完成判据 | 失败时 |
|---:|---|---|---|---|
| 1 | 合同/脚本check-only | PASS/BLOCKED输出 | 无网络无写入且一致 | 修合同，不检索 |
| 2 | Europe PMC×Q1 smoke | export、receipt、run行 | query/时间/命中/hash完整 | 保留ERROR/retry |
| 3 | 检查smoke可复现性 | checksum、重复ID拒绝 | 可回读且不覆盖 | 停止全矩阵 |
| 4 | 开放来源×Q1—Q12 | 每run导出/receipt | 所有声明项有证据 | 标ERROR/BLOCKED |
| 5 | 去重/版本链 | 唯一记录＋version chain | 不丢更正/撤稿 | 修规则再审计 |
| 6 | 双人筛选 | 两份独立判断 | 分歧全裁决 | 保持BLOCKED |
| 7 | 全文/模型四联核验 | 文献矩阵、模型表 | 数字/许可可定位 | 标UNKNOWN |
| 8 | 证据综述 | 范围建议和缺口 | 事实/推断/建议分开 | 范围保持OPEN |
| 9 | 阶段1 gate | `stage1_gate.json` | PASS | 按blocker闭合 |
| 10 | 更新GitHub三文档 | 计划/进展/架构 | 状态证据一致 | 不申请阶段2 |

## 10. 当前禁止事项

前置门禁未通过前，不得：下载全量原始组学；把元数据行数当独立样本；把同品种/组织当P1；使用UNKNOWN许可训练；声称作物/任务/架构已冻结；启动GPU；生成模拟曲线/性能；打开外测标签；宣称模型超过基线或发现机制。

## 11. 三份核心文档更新机制

- `RESEARCH_PLAN.md`回答“准备怎么做、为什么、如何验收”；
- `RESEARCH_PROGRESS.md`回答“真实做了什么、证据在哪里、还卡在哪里”；
- `MODEL_ARCHITECTURE.md`回答“候选/冻结模型如何工作、哪些确定/未知”。

### 强制更新事件

- gate状态改变或PASS被撤销；
- 新数据、许可或配对结论；
- MVP/task/split/架构冻结；
- 任一baseline、pilot、训练run或checkpoint；
- 训练失败、OOM、数据错误或泄漏；
- formal test；
- 历史指标/结论更正。

### 里程碑更新模板

```text
日期：
里程碑/阶段：
状态变化：旧状态 → 新状态
执行了什么：
机器证据：run/job/receipt/commit/hash
真实结果：
失败或异常：
可以支持的结论：
仍不能支持的结论：
对计划的影响：
下一步和完成标准：
训练曲线/架构图是否更新：
```

若发现历史错误，不静默删除：标记受影响run/图/表/结论，说明根因和范围，提供修复证据/hash，明确仍有效结论，并写入日志。

## 12. 进展更新日志

| 日期 | 版本 | 变化 | 训练状态 |
|---|---|---|---|
| 2026-07-16 | v1.0 | 首次发布阶段0状态、空训练曲线和候选架构链接 | 0 runs |
| 2026-07-16 | v2.0 | 增加机器证据、逐工作流状态、结果空值、blocker解除条件、逐Gate执行卡、符号张量/mask/训练步序、维护模板和FAQ | 仍为0 runs |

## 13. 小白常见问题

### Q1：阶段0 COMPLETE是不是项目完成？

不是。只表示启动规则、资源边界和审查体系完成，文献、数据、模型和外测仍在后面。

### Q2：56项测试通过，为什么没有模型结果？

这些测试验证治理脚本和安全规则，不是模型精度测试。

### Q3：为什么不先训一个小模型？

如果身份、许可和split错误，小模型也会产生误导。先审计后smoke更有意义。

### Q4：空曲线会不会显得没进展？

它准确表达“治理完成但训练未开始”；伪造示意曲线会破坏可信度。

### Q5：何时出现第一条真实曲线？

阶段1—5 PASS且阶段6有界MVP pilot获授权后，才会出现第一条真实曲线。该曲线及保存预测正是阶段6估计真实variance/power的输入；因此power PASS是进入阶段7的条件，不是产生首批阶段6 pilot曲线的前置条件。

### Q6：架构图是否定稿？

不是。所有模块是候选设计，最终结构由文献、真实数据和阶段3—4决策决定。

### Q7：复杂模型不如XGBoost怎么办？

如实报告，并按预注册规则简化或停止。复杂不等于更科学。

### Q8：何时能称“基础模型”？

只有多任务、少样本、迁移、缺失模态、缩放、强基线、多seed、严格外测和完整审计等硬条件全部满足后；否则降级命名。

### Q9：项目预计什么时候完成？

目前不能诚实给出固定日期，因为文献命中量、官方数据可访问性、许可和严格配对规模均未知。先完成阶段1真实smoke和阶段2元数据审计，再用真实吞吐、失败率和候选规模估算后续时间；在此之前按阶段和gate报告，不用主观百分比或虚假日期。
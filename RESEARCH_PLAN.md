# 作物多组学预训练研究计划

- 文档版本：v2.0
- 最后更新：2026-07-16
- 当前阶段：阶段0已完成；阶段1已获治理授权但尚未执行
- 维护原则：阶段、范围、数据、模型、评价或结论发生变化时，本文件必须同步更新

> 一句话概括：先证明“问题值得做、数据能合法且正确地配在一起、评价不会泄漏”，再决定训练什么模型。不能为了尽快得到曲线而跳过证据和数据门禁。

## 0. 零基础读者先看这里

### 0.1 这个项目要解决什么问题？

同一株作物可以从多个角度测量：DNA及变异、基因调控、基因表达、蛋白、代谢物、田间表型以及生长环境。这些数据通常分散在不同数据库、实验和样本中。本项目要研究：能否通过预训练，让模型学习这些信息之间可迁移的共同规律，并在少样本、跨物种、跨环境或缺少某些模态时仍有用。

研究链条是：

`基因组与变异 → 调控/表观组 → 转录组 → 蛋白/代谢组 → 组织/整株表型 → 环境与管理 → 育种决策`

### 0.2 什么是预训练和多组学？

- **预训练（pretraining）**：先让模型在较通用的数据上学习表示，再用于具体任务。训练过大数据不自动等于“基础模型”，必须证明它对新任务和新场景有稳定帮助。
- **多组学（multi-omics）**：同时研究基因组、转录组、表观组、蛋白组、代谢组等层次。严格多组学配对要求测量来自同一生物实体或有明确分样证据；仅仅“品种名相同”或“组织名相似”不够。

### 0.3 为什么现在还没有训练？

因为以下问题还没有真实证据：

1. 哪个作物最适合作为首版旗舰作物；
2. 哪些模态有足够、合法、可正确配对的数据；
3. 哪些任务有独立测试和足够统计功效；
4. 复杂模型是否比经典方法和简单融合更值得训练；
5. 训练、验证和外部测试能否真正隔离。

先回答这些问题，可以避免花费大量GPU后才发现样本错配、许可不允许、测试泄漏或任务没有统计意义。

## 1. 常用术语白话解释

| 术语 | 白话解释 | 本项目要求 |
|---|---|---|
| 模态（modality） | 一类测量，如转录组或代谢组 | 每类有独立来源、版本、质量和许可 |
| 表征（representation） | 模型把复杂输入变成可计算特征 | 必须证明对真实任务有用 |
| tokenizer | 把原始数据切成模型可读单位 | 单位可能是碱基、变异、基因或样本，尚未冻结 |
| encoder | 把输入单位变成向量的模块 | 不同模态原则上先独立编码 |
| fusion | 合并不同模态信息的方法 | 必须与简单拼接、early/late fusion比较 |
| baseline（基线） | 简单或公认有效的对照方法 | 复杂模型必须在公平预算下超过强基线 |
| ablation（消融） | 拿掉一个模块，看它是否有贡献 | 防止“模块很多但不知道谁有效” |
| seed（随机种子） | 控制训练随机性的编号 | 不能只报告最好的一个seed |
| train/validation/test | 训练集/验证集/测试集 | 训练拟合，验证选择，测试只做最终评价 |
| external test（外测） | 来自独立来源的最终测试 | 不得进入训练、预处理或模型选择 |
| leakage（泄漏） | 模型选择提前看到了测试信息 | 任一泄漏都会削弱或推翻性能结论 |
| checkpoint | 某一步保存的模型参数 | 只能根据验证集选择 |
| receipt（回执） | 带文件路径和哈希的机器证据 | 证明操作真实执行且内容未被替换 |
| gate（门禁） | 判断能否进入下一阶段的检查 | `PASS=0`、`ERROR=1`、`BLOCKED=2` |
| hash/checksum | 文件内容的数字指纹 | 内容变化后指纹变化，用于发现漂移 |
| power（统计功效） | 真实有效时把效果检测出来的概率 | 默认目标≥0.80，需真实pilot估计 |
| MMED（最小有意义效应） | 小于它即使“显著”也没有足够实际价值的最低改善 | 每个主任务在看正式结果前冻结 |
| 95% CI（置信区间） | 用重采样表示效应不确定范围 | 按最高层独立生物单位重采样，不把seed当新样本 |
| block/hierarchical bootstrap | 按study、site-year-trial或谱系等整组重采样 | 保留真实层级，禁止逐行假装独立 |
| Holm校正 | 同时检验多个确认性主张时收紧通过阈值 | 任务/指标/基线组成的family须预先冻结 |
| winner / tie-break | 按冻结公式选出的候选 / 分数相同时的固定决胜规则 | 只读validation，不读external test |
| manifest（清单） | 逐行登记数据、文件或样本身份的表 | 必须有版本和hash，不能只凭文件名 |
| site-year-trial | 某地点、某年份、某次完整田间试验 | 同一试验内样本通常不能随意跨split |
| G×E | 基因型与环境互作，即材料在不同环境表现不同 | 评价必须显式保留环境和试验结构 |
| headline task | 论文主结论直接依赖的核心任务 | 指标、seed、外测和统计规则要优先冻结 |
| consumer | 会读取数据并影响训练或模型选择的程序/流程 | 实际读取的manifest必须登记并做防泄漏检查 |
| seal / formal claim | 外测封存记录 / 一次性正式访问声明 | 防止外测被反复查看和调参 |
| P0 / P1问题 | 阻断级 / 高优先级审查问题 | 阶段0终审要求两者均为0 |
| P1配对等级 | 同一实体或有明确分样证据的跨模态配对 | 与“P1高优先级问题”不是同一概念 |
| MVP / pilot | 最小可行完整流水线 / 小预算验证试验 | pilot只能用于validation、资源和功效估计 |
| release | 经过检查、可由后续阶段引用的一组不可变产物 | 需manifest、hash、状态和来源闭合 |
| access | 读取文献、元数据或正式测试的受控动作 | 需登记用途、范围、时间和receipt |
| split | 把独立单位分到train/validation/test的规则和结果 | 必须在看测试结果前冻结 |
| shard | 为高效读取而分块的数据文件 | 只是存储单位，不能改变样本身份或split |
| microbatch | 一次放进GPU并前向/反向的小批数据 | 多个microbatch可累积成一次参数更新 |
| optimizer step | 优化器真正修改一次参数 | 需绑定有效token数、学习率和checkpoint步号 |

统计门禁的白话链条是：先在每个真实独立单位上计算“候选模型−冻结强基线”的配对差值 → 按study/site-year-trial/谱系等最高层整组重采样得到95% CI → 对预先登记的任务/指标/基线family做Holm校正 → 同时要求效应达到MMED → 只用validation按winner/tie-break选模型。不同seed只是同一算法的重复运行，用于观察训练方差，不能把生物样本数乘以seed数来缩小CI。

## 2. 总体目标和可证伪假设

### 2.1 总体目标

建立一个可审计、可复现、可证伪的作物多组学预训练体系，检验统一但分层的表示学习能否在多任务、少样本、跨域和缺失模态场景中产生稳定收益。

### 2.2 待检验假设

以下是假设，不是结果：

- **H1 预训练增益**：相同架构和预算下，预训练权重比随机初始化在至少两类任务上有稳定增益。
- **H2 多模态增益**：正确配对的多模态模型优于最佳单模态和简单拼接。
- **H3 条件建模增益**：显式建模组织、时期、处理、地点和年份，比把条件当普通末端协变量更稳健。
- **H4 少样本增益**：在1%、5%、10%标注量下，预训练相对收益仍存在。
- **H5 跨域能力**：模型在至少两个独立迁移轴上保持收益，例如跨物种和跨环境。
- **H6 缺失模态鲁棒性**：缺少至少两类模态时，门控或modality dropout比直接填零更稳定。

任何假设失败都要记录；不能只保留有利任务、seed或指标。

## 3. 研究范围和明确不做的事

### 3.1 计划覆盖

- 植物/作物序列、变异和多组学表示学习；
- 分子状态、表型与G×E（基因型×环境）预测；
- 基因/变异优先排序；
- 跨物种、跨环境、少样本和缺失模态评估；
- 经典统计、机器学习、简单融合和随机初始化对照；
- 多seed、置信区间、严格外测和泄漏审计。

### 3.2 当前不承诺

- 不预设旗舰作物、模态组合、层数、参数量或模型名称；
- 不把相关性预测写成因果推断；
- 不承诺一定形成“基础模型”；
- 不使用许可、身份或配对证据不明的数据训练；
- 不用测试集选择超参数、checkpoint、阈值或模型版本；
- 不因已有代码、权重或热门模型倒推科学问题；
- 阶段0—4不进行正式预训练，GPU预算为0。

## 4. 当前治理边界

截至2026-07-16：

- 阶段0：`COMPLETE`；
- 阶段1治理：允许启动；
- 阶段2数据晋升：未授权；
- GPU或大规模下载：未授权；
- formal test（正式测试）访问：未授权。

阶段0完成只代表研究规则和门禁已经建立，不代表找到数据、实现模型或证明模型有效。

## 5. 十阶段总路线

| 阶段 | 核心问题 | 主要产物 | 进入下一阶段的必要条件 | 当前状态 |
|---|---|---|---|---|
| 0 治理与资源 | 能否安全、可审计地启动？ | 资源审计、治理合同、终审receipt | R13终审P0=0、P1=0 | **COMPLETE** |
| 1 系统证据综述 | 已有研究真正做到了什么？ | 检索回执、双筛、文献矩阵、模型许可清单 | 阶段1 gate PASS | GOVERNANCE READY / EXECUTION BLOCKED |
| 2 数据可用性审计 | 哪些数据合法、身份明确且可配对？ | 数据目录、样本manifest、许可ledger、配对矩阵 | 至少一个可行范围且gate PASS | BLOCKED |
| 3 MVP范围冻结 | 第一版做哪个作物、模态和任务？ | 三方案矩阵、MVP合同 | 用户评审＋机器检查 | 未开始 |
| 4 架构与统计设计 | 模型、预算和统计是否具体？ | 模型/任务合同、pilot与power计算合同 | 设计字段冻结；真实power待阶段6 | 未开始 |
| 5 数据冻结 | split是否可复现且无泄漏？ | 内容寻址数据、split、外测seal | 泄漏门禁PASS | 未开始 |
| 6 端到端MVP | 最小流水线能否训练、恢复和评价且有足够功效？ | smoke、强基线、最小模型、power receipt、失败分析 | 结果可恢复/复算且power gate闭合 | 未开始 |
| 7 预训练与缩放 | 收益是否稳定且可扩展？ | 多规模×多比例×多seed证据 | 选择规则闭合 | 未开始 |
| 8 正式外部评估 | 未见外测上是否仍优于基线？ | 一次性formal test、CI、多重校正 | formal claim闭合 | 未开始 |
| 9 生物学解释与交付 | 结果是否有意义且可复现？ | 数据卡、模型卡、论文图表、复现包 | 证据与措辞一致 | 未开始 |

依赖链是0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9。阶段1未完成前不申请阶段2，阶段5未完成前不训练，阶段8未授权前不查看正式外测。

从来源到结论的完整链条是：`官方来源 → 访问receipt → 身份/许可审计 → approved release → split与shard → 训练run → validation选择 → winner冻结 → 一次性formal claim → 外测结果 → 有边界的科学结论`。任一箭头缺证据，后面的结论都必须降级或阻塞。

所有未完成阶段都使用三态出口：`PASS`表示全部必要证据闭合；`BLOCKED`表示脚本可正常工作但前置证据/授权不足，只能补前置条件；`ERROR`表示执行、输入格式或系统本身出错，需保留错误证据并修复后重试。单个脚本、表格或图件通过检查，不等于整个阶段PASS。

本计划当前不写一个看似精确但没有证据支持的完成日期。阶段1命中量、官方元数据可访问性、许可审批和P1配对规模都尚未知，它们会直接决定后续路线和工作量。阶段1真实smoke和阶段2元数据审计产生吞吐、失败率和候选规模后，再在本节增加基于证据的时间估算；在此之前只按门禁依赖报告进度，不把日期当作完成证据。

## 6. 阶段0：治理、资源和安全边界（已完成）

### 输入

空白重启的项目目录、当前Slurm/共享文件系统/软件环境，以及项目的科学使命和高风险科研要求。

### 已执行

1. 只读审计登录节点、计算节点、Slurm、BeeGFS、环境和网络；
2. 定义数据身份、许可、配对、统计、外测和失败关闭规则；
3. 定义实验注册、内容哈希、冻结manifest和终审流程；
4. 建立阶段1/2计划和机器检查脚本；
5. 完成R13三路独立终审。

### 产物和验收

- 91项冻结闭包；
- P0=0、P1=0；
- `stage0_completion.status=COMPLETE`；
- 只授权阶段1治理，不授权数据晋升、GPU、大下载或formal test。

### 白话解释

项目已经有“交通规则、检查站和黑匣子记录”，但还没有正式数据和模型。

## 7. 阶段1：系统文献检索和可复用模型核验

### 目标

回答：已有植物/作物模型覆盖哪些任务；结果是否有严格划分、强基线和独立外测；代码和权重是否真实可得；数据、代码和权重许可是否允许复用。

**为什么不能跳过：** 不检索就无法知道科学空白、强基线和可复用权重，容易重复已有工作或把宣传性结果当证据。

### 输入

- 已配置的12个query族（Q1—Q12）；
- Europe PMC、PubMed、arXiv等开放来源；
- Crossref只作DOI元数据扩展；
- 付费来源只在有合法凭据或官方人工导出时使用；
- 候选模型名只是检索种子，不是已核验事实。

进入本阶段后不可静默改变的输入是query配置、来源注册表、截止日期、筛选规则、纳排标准和许可核验字段；如需修改，必须升版本并使旧检索结论失效。

**当前实现边界：** 内部runner只实现合同检查和单次`FIRST_PAGE`有界网络/export smoke；尚未实现分页游标闭合、失败run/ERROR receipt持久化、去重、版本链、双筛/裁决、证据矩阵或最终receipt producer。现有总gate只是只读validator，把JSON写到stdout/Slurm日志，不会原子生成`stage1_gate.json`。因此下面第4—11步是必须实现并测试的研究合同，不是当前可直接执行的现成功能；在这些接口变为非TBD前，阶段1保持`BLOCKED`，任何首屏`COMPLETED`都不能解释为“该来源已系统检索完成”。

### 具体步骤

1. 合同和脚本`check-only`；
2. Europe PMC×Q1小规模真实smoke；
3. 核对query、响应、命中数、导出、时间、重试和SHA-256；
4. 串行运行开放来源×Q1—Q12，不并发覆盖登记表；
5. 按DOI、数据库ID、规范题名/作者/年份去重；
6. 把预印本、正式版、更正和撤稿连成版本链；
7. 两名reviewer独立筛选，分歧由第三方裁决；
8. 核验训练数据、split、指标、强基线、外测和局限；
9. 核验官方代码commit/release、权重、模型卡；
10. 数据、代码、权重三类许可分别判断；
11. 运行阶段1 gate并保存receipt。

第4步必须逐来源分页至官方终止游标，并核对声明总命中数、导出记录数、页数和最终游标；第5—10步需要各自的输入/输出schema、命令、测试和append-only receipt；第11步需要独立producer以no-replace方式绑定合同、输入表、文件hash、blocker、时间、代码commit和输出路径。未实现前不得用人工补写文件伪造PASS。

### 必须产出

检索run表、原始导出、search receipt、筛选表、版本链、文献证据矩阵、可复用模型表、参考文献库、证据综述和`stage1_gate.json`。

### 完成标准

- 每个“已检索”来源都有真实query、导出和checksum；
- 双筛、冲突裁决和版本链完整；
- 关键模型完成论文、官方代码、权重、模型卡（缺失也须显式记`ABSENT`）和许可五类证据核验；
- 关键数字可定位到页码、图表、补充材料或仓库路径；
- 连续两轮新检索不再出现会改变范围决策的新工作；每一轮固定为“已登记开放来源×Q1—Q12×同一纳排/去重规则”的完整矩阵，绑定独立截止日期和配置hash，由两名reviewer判断是否出现会改变范围的新证据；
- 机器门禁返回`PASS`。

### 阻塞和失败处理

无凭据付费源标`ACCESS_BLOCKED`；全文不可访问标`FULLTEXT_ACCESS_BLOCKED`；名称不唯一标`NAME_UNRESOLVED`。未来完整runner必须把网络/解析失败写入append-only ERROR/retry receipt；当前runner只打印stdout错误，不满足该合同，所以发生错误时只能保留日志并维持阶段1`BLOCKED`，不能把日志当正式receipt。任何这些情况都不能伪写成“已检索/已证实”。阶段1失败时不下载组学数据、不训练模型，只报告证据缺口。

`BLOCKED`后的下一动作是取得合法凭据/官方导出、补全文或解析名称；`ERROR`后的下一动作是按同一query和来源修复网络、解析或登记问题，保留失败run后创建新run。执行任何真实请求前必须冻结source级connect/read timeout、最大attempt数、429/5xx可重试集合、退避序列、总调用数、最大页数/字节数和总walltime；每页必须保存cursor、记录数、累计hash和append-only部分进度receipt，并拒绝重复cursor、游标回退或连续无新增记录。预算耗尽但已保存一致进度时记`BLOCKED`并等待人工续跑授权；cursor循环、响应漂移或hash不一致记`ERROR`。两者都禁止无限新建run，只有官方终止cursor闭合且最终receipt PASS才算来源检索完成。只有阶段1总gate PASS才申请阶段2。

## 8. 阶段2：数据身份、许可和多组学配对审计

### 目标

先回答每个文件来自谁、测了什么、能否合法训练、能否和其他模态正确配对、能否作独立外测，而不是先追求数据量。

**为什么不能跳过：** 文件名、品种名或组织名相同不能证明来自同一样本；许可不清和实体错配都会让后续训练失去法律或科学意义。

本阶段不可静默改变的输入包括阶段1 PASS receipt、官方来源注册表、92列schema、配对等级、许可状态机、重复折叠规则、资源上限和阶段2授权。任何变化需新版本和新receipt。

### 身份层级

`物种 → 种质/群体/系谱 → site-year-trial → plot/individual → biological sample/aliquot → assay/batch → file`

即先确定材料和试验，再确定小区/个体、生物样本、检测批次，最后才是文件。

### 具体步骤

1. 从论文数据声明和官方数据库找到稳定accession.version；
2. 只取元数据和合同允许的少量样例；
3. 填充92列样本manifest，包括随机化、block、重复、复合取样和批次；
4. 统一参考组装、注释、基因ID、坐标和表型单位；
5. 跨库去重，保留重复提交的来源关系；
6. 保存许可条款、定位、时间、reviewer和hash；
7. 按P1—P4/PX评定配对；
8. 先折叠重复提交和技术重复，再计算独立单位；
9. 按许可、身份、配对、质量、规模、成本、外测价值等评分；
10. 输出A/B/C/NO-GO范围建议和外测候选。

外测候选一经提名，必须立即建立**早期identity embargo（身份禁运记录）**：阶段2—4只允许读取来源、稳定ID、版本、许可、study/assay/tissue、地点/年份、测量是否存在和独立单位计数；禁止读取目标类别、表达/表型值、效应大小、结局、正式阈值及任何结果汇总。每次访问都写角色、用途、字段、时间和receipt。阶段5再对最终字节、manifest、标签和访问策略做正式seal；阶段5前必须有“外测标签访问次数=0”的机器证明。

### 配对等级

| 等级 | 含义 | 允许用途 |
|---|---|---|
| P1 | 同一生物实体或有证据的split aliquot，条件一致 | 严格跨模态对齐候选 |
| P2 | 条件近似但不是同一实体 | 敏感性分析，不作严格配对 |
| P3 | 无实体配对的同分布数据 | 单模态预训练或分布比较 |
| P4 | 只有同源/通路等弱锚 | 弱监督探索 |
| PX | 身份冲突或证据不足 | 不进入配对训练 |

### 许可状态

`UNKNOWN_NO_TRAIN → LOCATED → TEXT_CAPTURED → REVIEWED_ALLOWED / REVIEWED_RESTRICTED / REVIEWED_FORBIDDEN / NEEDS_PERMISSION`

许可要分别回答下载、训练、商业使用、衍生权重、数据再分发和权重再分发。只要仍为UNKNOWN，就不能训练。

### 完成标准

目录、访问日志、评分和许可表非空且外键一致；真实样本manifest非空；配对能回到官方ID/样本表；重复折叠后有足够独立单位；至少一个外测候选可seal且已有identity embargo/零标签访问receipt；所有数字可追溯；最终no-replace `stage2_gate.json`对当前全部输入hash返回PASS。validator日志不能替代该receipt。

### 资源限制

阶段2 GPU=0；阶段2首个数据审计检查点前原始样例<50,000,000,000 bytes；项目新增107,374,182,400 bytes触发软审查；单次新下载超过200,000,000,000 bytes必须用户确认。

阶段2输出是内容可追溯的数据目录、非空样本manifest、ID crosswalk、配对矩阵、许可ledger/receipt、访问日志、重复折叠统计、A/B/C/NO-GO评分、外测候选及其identity embargo/零标签访问receipt，以及最终`stage2_gate.json`。`BLOCKED`时只能补官方元数据、身份边、许可或授权；`ERROR`时修复解析/schema/外键/下载边界并重新审计；不得用扩大下载掩盖身份缺失。

## 9. 阶段3：MVP范围冻结

MVP（最小可行版本）是用最小范围完整回答核心科学问题，不是单纯把模型做小。

### 目标和不可跳过原因

把阶段1—2的证据收敛成一个可执行主方案和一个降级方案。若不冻结，作物、模态、任务和成功标准会在看到结果后漂移，产生选择偏差。

### 不可变输入

阶段1/2 PASS receipt、数据评分、许可、P1/P2规模、外测候选identity embargo/零标签访问receipt、资源审计、强基线清单和用户评审记录。

### 有序动作

1. 只从通过许可/身份门禁的候选构建A/B/C方案；
2. 对每个方案计算独立单位、模态覆盖、P1/P2、外测、存储和预计计算；
3. 为每个headline task写标签、独立单位、split和主要指标草案；
4. 比较科学价值、最小有效效应、强基线、泄漏风险和降级路径；
5. 选择一个主方案和一个明确触发条件的降级方案；
6. 冻结范围合同、决策记录和hash。

### 三方案矩阵

至少比较：

- **A 严格P1小范围**：样本少但身份最可信；
- **B P1主分析＋P2敏感性**：兼顾可信度和覆盖；
- **C 单模态大规模预训练＋小规模配对适配**：配对不足时的降级路线。

统一比较科学价值、独立单位、许可、配对、外测、计算成本、基线强度、泄漏风险和可解释性。

### 必须冻结

旗舰范围、首版模态、token单位、headline task、独立统计单位、主要指标、最小有意义效应、强基线、split最小单位、候选架构A/B/C、预算和停止规则。

### 完成标准

用户评审选定主方案和降级方案；机器合同完整；任何关键项仍为UNKNOWN都应阻塞训练。

**输出：** 范围决策矩阵、MVP合同、headline任务草案、预算上限、停止/降级规则和decision receipt。`BLOCKED`表示无方案同时满足非空任务、许可、独立单位和外测；下一步只能缩小主张或补数据证据。`ERROR`表示矩阵/schema/计算不可复算；修复工具后重新冻结。

## 10. 阶段4：架构、资源和统计分析合同设计

### 目标和不可跳过原因

把候选架构、pilot协议和统计成功函数变成机器唯一的设计合同。阶段4不拟合baseline、不产生预测、不做optimizer update，也不声称已有真实power；真实pilot和power必须等阶段5数据/split release冻结后在阶段6产生。

### 不可变输入

MVP范围receipt、approved数据schema、headline任务/标签证据草案/独立单位、metadata-only split字段合同、外测identity embargo、候选架构A/B/C、baseline清单和资源快照。

### 有序动作

1. 写清单样本从输入到每个head的shape/mask/路由；
2. 冻结tokenizer、encoder、fusion、condition、missingness和loss构造；
3. 独立复算参数量、显存、吞吐、checkpoint和恢复；
4. 为每个任务冻结标签证据层级、主要指标、比较单位、MMED（最小有意义效应）和多重校正；
5. 冻结metadata-only split builder允许字段、group规则、外测排除和零标签访问检查；
6. 冻结强baseline全集、公平搜索预算、validation-only pilot协议和保存预测schema；
7. 冻结联合power模拟/正式成功函数、planned formal seeds、tie-break和资源上限；
8. 只做schema、符号shape、参数、静态泄漏和合成fixture检查；不得读取真实目标值或运行真实pilot。

### 模型设计

冻结每模态输入/tokenizer/encoder、fusion路线、条件注入、缺失模态策略、预训练目标、任务头/loss/路由、至少两个模型规模、显存/吞吐/walltime/GPU小时、checkpoint/恢复/日志规则。

### 统计设计

每个headline task必须冻结：候选全集；标签版本；`direct/curated positive`、`proxy/heuristic positive`、仅在明确callable universe成立的`operational negative`、`unlabeled`、`unknown/unmeasured/unmappable`五类标签证据；覆盖分母、重复证据折叠和零分母处理；独立单位、重复折叠、split最小单位、主要指标、MMED、baseline候选全集、配对比较单位、显著性水平、同一多重比较family、block或hierarchical bootstrap 95% CI、Holm校正、seed策略和`formal_seed_count>=5`。proxy默认只进入预注册次要/敏感性分析，除非主张明确降级到proxy语义。

seed是算法重复，不是新增生物独立单位。每个seed先在同一冻结独立单位上生成配对预测/差值，再按预注册等权或其他冻结权重聚合；CI必须重采样最高层生物cluster，并把seed作为交叉的算法重复纳入方差，而不能把`seed × sample`当独立观测。生物层级不确定性和seed间方差分开报告；失败seed保持失败/缺失状态，按冻结成功函数处理，不得替换。

联合power函数必须与阶段8共用独立单位聚合、配对差值、MMED、CI下界、Holm family和正式成功函数，并预定义总计及各关键层级的最小独立单位输出。阶段4只验证函数/schema，真实variance、baseline winner、样本量和power receipt在阶段6由冻结train/validation release产生；联合正式成功概率低于0.80或任一最低单位数不足即阶段6`BLOCKED`，不能用边际检验代替。

### 完成标准

模型、任务、split builder、pilot、预算和联合power函数合同全部通过静态/fixture检查。power状态必须明确写`PENDING_REAL_PILOT`；阶段4 PASS只允许进入阶段5数据冻结，不授权正式训练或宣称power达标。

**输出：** 模型/张量合同、参数账本、任务/标签证据合同、metadata-only split builder合同、pilot协议、联合power函数、资源估算和阶段4设计receipt；不包含真实baseline winner、预测或power值。`BLOCKED`表示设计字段、合法数据schema或可执行预算不足；只能补合同/证据或降低主张。`ERROR`表示shape/函数/schema/静态检查出错；修复后重审，不进入阶段5。

## 11. 阶段5：数据冻结和泄漏门禁

### 目标和不可跳过原因

把数据、标签和split发布为后续训练唯一可消费的不可变release，并证明外测未进入任何训练/选择路径。没有这一Gate，随机split、重复样本或全数据预处理可制造虚假高分。

### 不可变输入

阶段2 approved数据/许可receipt、阶段3范围、阶段4任务/统计/模型合同、身份图和外测候选。

### 有序动作

1. 折叠重复提交、文件别名和技术重复；不得默认折叠克隆/无性系在不同plot、地点、年份或处理下的真实生物观测；克隆基因型以group ID关联，并按预注册estimand决定保留、整组分配、层级建模或阻断；
2. split builder只能读取冻结白名单metadata（身份、来源、study、site-year-trial、plot/individual、谱系/同源group、assay/tissue/condition和measurement-presence），禁止读取目标标签、类别比例、原始组学/表型值、效应量、全数据结局统计或formal external bytes；
3. 先选定并no-label seal `formal_external_test`身份，再对剩余独立单位生成`train/validation`并hash；本计划不另设可反复查看的“internal test”；
4. split hash和external identity seal冻结后才连接train/validation标签；formal external标签继续隔离；
5. 仅用train拟合归一化、插补、PCA、亲缘矩阵、词表和特征选择；
6. 物化record manifest和必要shard，并保持sample/split ID不变；
7. 给数据、标签、split、预处理、代码和环境生成SHA-256；
8. 单独封存formal external标签、manifest和访问策略；
9. 登记所有训练/选择consumer的实际input manifest；
10. 对每个consumer逐轴检查与formal external交集；
11. 运行split builder正/负向测试和独立泄漏审计后，原子发布带`READY`的data release与receipt。

外测不得进入预训练、微调、标准化、插补、PCA、亲缘矩阵、图边、辅助目标、特征选择、阈值、checkpoint或ensemble选择。

### 输出、PASS和失败出口

输出是data/split release、预处理状态、formal external seal、consumer registry、split-builder字段访问receipt、防泄漏receipt和阶段5总receipt。PASS要求identity embargo访问日志从候选提名连续闭合至seal时间且外测标签访问计数为0；formal external seal完整；split builder只访问白名单metadata且禁止字段/外测bytes负测均PASS；每个真实consumer有实际manifest；11类泄漏轴交集为0；文件/hash/模式均可回读。

`BLOCKED`表示身份、许可、consumer或seal证据不足，回阶段2—4补证据；`ERROR`表示hash漂移、外键、原子发布或交集计算异常，隔离坏release并重建。两种状态下都不能训练。

## 12. 阶段6：端到端MVP

### 目标和不可跳过原因

用冻结data/split release和最小预算证明“读取→前向→反向→恢复→预测→复算指标→联合power”闭环真实可用。它是首次允许的真实拟合/pilot阶段；直接正式预训练会把接口、恢复、指标或功效错误放大成昂贵失败。

### 不可变输入

阶段5 data/split release/external seal、防泄漏receipt、阶段4冻结模型/任务/split-builder/pilot/power/预算合同、环境锁和已批准的CPU/GPU资源范围。

### 执行顺序

1. 数据smoke：极小样例走到指标输出；
2. 训练smoke：前向、反向、保存和恢复；
3. 经典基线：rrBLUP/GBLUP、反应规范等；
4. 强表格基线：XGBoost/LightGBM；
5. 简单融合：拼接、early fusion、late fusion；
6. 同架构随机初始化；
7. 最小预训练模型；
8. 保存逐独立单位预测，用冻结联合函数估计variance、层级支持量和power；
9. 冻结pilot baseline winner、formal seed矩阵和tie-break；
10. 中断、坏样本、缺失模态等失败注入。

### 完成标准

配置可复跑；中断可恢复；指标/power能从保存预测复算；资源不超预算；基线和复杂模型使用公平数据/搜索预算；外测保持零访问；失败实验也登记。进入阶段7还要求联合power≥0.80、关键层级最低单位数满足且formal seed矩阵冻结。MVP通过只代表流水线和正式设计可信，不代表论文级优势。

**输出：** 数据smoke receipt、单步/固定步训练run、checkpoint与恢复对比、逐单位预测、复算指标、资源telemetry、强基线/pilot winner、联合power receipt、formal seed矩阵、失败注入记录，以及no-replace、内容寻址的`stage6_gate.json`。该总receipt绑定全部上游PASS、输入hash、必需run终态、恢复/指标/power、预算和输出hash；只有它为当前字节的PASS才能进入阶段7。`BLOCKED`表示资源、上游release、独立单位或power不足；不得进入阶段7，只能按预注册规则补合规validation证据或降低主张。`ERROR`表示NaN/OOM/恢复不一致/指标或power不可复算，保留失败run，修根因后用新run复测。

## 13. 阶段7：正式预训练、缩放和适配

### 目标和不可跳过原因

检验收益是否跨seed、数据量、模型规模、标注量、迁移轴和缺失模态稳定，而非来自一次幸运run。

### 不可变输入

当前字节对应且为PASS的`stage6_gate.json`、冻结数据/split/model/task/winner/预算合同、完整run矩阵和停止规则。

### 最小实验矩阵

至少2个模型规模、3个数据比例、多个预注册seed、1%/5%/10%/100%标注比例、2个独立迁移轴、2类缺失模态，并与同架构随机初始化和强基线比较。

### 选择规则

只看validation；winner公式在test前冻结；不按测试结果回头改变训练轮数、loss或规模；展示全部预注册seed；每个曲线点绑定run、数据、split、配置、代码、seed、日志和checkpoint。

### 停止/降级

“validation不改善”必须在阶段3—4冻结为：预注册主指标相对强基线的配对改善未达到MMED，或95% CI下界未高于0，并持续达到冻结的checkpoint/seed观察窗口；“持续不如单模态”使用同一窗口和统计函数。触发后停止扩大；多模态持续不如单模态则转单模态＋任务适配；配对不足则缩小P1或走非配对路线。“实质不同修复方向”必须登记为不同根因类别，例如数据/身份与配对、目标/模型结构、训练优化/评价实现；仅换学习率或延长同一run不算新方向。每个方向的最大尝试数、总GPU小时、walltime和观察窗口在阶段3—4预算合同中冻结；达到任一上限，或三个已登记方向均不能改善预注册核心validation指标时，终止/降级路线并发布全部失败分析。

### 有序动作、输出和出口

按预注册矩阵创建run → 启动前核input/hash → 训练并原子保存checkpoint → 从保存预测计算validation → 汇总全部seed/成本 → 按冻结winner公式选择 → 运行消融/迁移/缺失压力测试 → 发布候选winner release → no-replace发布绑定完整run矩阵、预算/停止判定、winner和输出hash的`stage7_gate.json`。

PASS要求矩阵完整、缺失seed有真实状态、winner不读formal external且恢复/指标可复算，并且`stage7_gate.json`对当前字节返回PASS。`BLOCKED`表示预算、power或必需run不完整；`ERROR`表示训练、数据或恢复失败；均不得偷偷删run或补造seed。

## 14. 阶段8：一次性正式外部评估

反复查看外测并改模型会把外测变成验证集，因此使用不可覆盖claim和两级append-only registry（追加式登记册）。第一级`external_identity_registry`同时维护canonical identity-family和每个实体：family由稳定官方accession/version、标签语义、最高层独立单位ID集合及其来源关系定义；实体再绑定数据/标签实际字节和内容hash。重编码、重压缩、列重排、单位别名、切片、子集/超集和派生副本必须登记到同一family或显式派生边。创建claim前要同时检查family、稳定ID和最高层独立单位集合；与任何已消费family存在别名、派生或非空重叠都不能成为新确认性外测，只能`REUSED_BENCHMARK / DESCRIPTIVE_ONLY`。第二级`claim_registry`以`freeze manifest + canonical external identity-family/entity + 完整正式评价矩阵`为键。矩阵至少为`task × model_role/model_id × release/checkpoint/config × formal seed或deterministic N/A`，其中`model_role`必须同时包含winner、同架构随机初始化和每任务预注册最佳强基线。

两个registry必须位于受限写权限的durable存储，no-replace、不可删除并有独立审计日志。claim创建事务必须在读取任何外测字节前先验证canonical family/entity未消费且与已消费独立单位零重叠，再原子写入“已消费”family/entity和claim记录，fsync文件及父目录，并绑定唯一结果目标。任一记录存在，无论状态为RUNNING、PASS、FAILED、ERROR、崩溃或超时都永久阻断同一family、其派生/别名或任何重叠集的再次确认性访问；换编码、目录、seal、task、winner或比较模型均不能绕过。只有来源独立、稳定ID与已消费集合零重叠且从未暴露的新family/entity才可建立新的确认性claim；复用旧benchmark只能明确标为`REUSED_BENCHMARK / DESCRIPTIVE_ONLY`，不得进入确认性CI/Holm、基础模型资格或主要新颖性主张。一个claim覆盖完整矩阵而不是单个winner或seed；任一单元失败都保留终态且不得补跑。可发布“部分完成/失败”的诚实报告，但不能把不完整比较矩阵称为formal PASS，formal seed不足也不满足“基础模型”资格。

**formal-pretest producer：** 阶段7 PASS后，由冻结正式runner在合成fixture和冻结train/validation fixture上运行，禁止打开formal external路径或标签。它以no-replace方式生成内容寻址的`formal_pretest_gate.json`，绑定阶段5 seal identity（只绑定hash，不读字节）、stage6/7总receipt、完整比较矩阵、代码/环境/统计实现hash、资源上限和最新零标签访问日志。PASS要求所有模型可加载、推理/预测schema/统计dry-run可复算、矩阵单元完整、hash一致且external open/read attempt计数为0；`BLOCKED`表示receipt/资源/矩阵不全，`ERROR`表示加载、schema、统计或hash失败。两者都不得创建claim或打开外测。

### 目标、输入和有序动作

目标是在完全冻结且未见的外测上同时评价最终winner、同架构随机初始化和预注册强基线。输入是阶段5 seal、当前PASS的`stage6_gate.json`、`stage7_gate.json`与`formal_pretest_gate.json`、winner及全部比较器release、task/model-role/seed/power/统计合同、全部consumer防泄漏receipt，以及两个append-only registry的当前快照/权限审计。

顺序是：在非外测fixture上生成并验证formal-pretest receipt → 重验所有hash、阶段6/7总receipt和registry权限/未消费状态 → 原子标记external identity已消费并创建唯一claim → 才允许读取外测bytes → 在同一已消耗attempt中运行完整冻结比较矩阵 → 保存每个单元的逐样本预测和资源/失败状态 → 按预注册函数计算配对指标/CI/Holm → 运行后置formal-claim gate → 发布不可变结果receipt。

### 执行前

冻结task、model role、每个winner/随机初始化/强基线的release、checkpoint/config及seed或deterministic N/A；power≥0.80，否则必须在打开标签和创建claim前`BLOCKED`；需要算法随机性的每任务/模型至少5 formal seeds；seal和全部防泄漏receipt完整；阶段6/7总receipt与`formal_pretest_gate.json`均PASS；external identity未消费且registry不可删/权限审计PASS；freeze manifest不可变。

### 报告

主/次指标、与基线的配对差值、block/hierarchical bootstrap 95% CI、Holm校正；最高单seed与多seed稳定性分开；失败、超时和缺失seed不补造。

PASS要求唯一claim、所有预注册`task × model role/model × config × seed/N/A`单元状态完整、预测与release/hash匹配、统计可复算且后置gate通过。`BLOCKED`只能发生在开标签前，需补前置receipt；claim创建后的崩溃/超时是已消耗的失败结果，不是可重试BLOCKED。`ERROR`必须原样报告，不得换模型/checkpoint或再次开测试。

`CONSUMED_ERROR`或`FORMAL_FAILED`不算阶段8性能PASS，但必须沿唯一失败出口进入阶段9的failure-only reporting（仅报告已消耗claim、错误/部分结果、影响范围和不可重试事实），不得形成正向性能主张或“基础模型”资格。

## 15. 阶段9：生物学解释和交付

### 目标和不可跳过原因

把统计结果转换成不过度主张、可复现、可供同行检查的科学结论。只给一个最高分会隐藏失败、成本和适用边界。

### 输入和有序动作

输入是全部formal结果/预测、baseline、消融、迁移、失败run、资源记录、数据/模型/许可release和预注册合同。

依次：复算主表 → 分层检查物种/环境/模态/缺失/seed → 做错误与敏感性分析 → 区分相关/排序/因果 → 生成图表及源数据 → 写数据卡/模型卡/局限 → 核对许可决定可发布内容 → 独立复核结论与证据 → 发布复现包。

结论分三层：相关性预测；候选优先排序；因果效应。只有扰动、近等基因系、独立遗传设计或湿实验支持时才使用因果措辞。

最终产物包括数据卡、模型卡、训练/评价/资源日志、主结果/基线/消融/迁移/失败实验、PNG/PDF图件和源数据、环境锁/配置/脚本/checkpoint哈希、公开GitHub文档及许可允许的模型或复现包。

PASS要求每个主张能定位到task、数据、split、run、预测和统计receipt，所有负结果、缺失seed和限制可见，图表可由源数据重建，发布内容符合许可。`BLOCKED`表示许可或证据不足，只发布允许且可支持的子集；`ERROR`表示复算、链接、hash或图表不一致，修复并重审后才能交付。

## 16. 基线、成功和“基础模型”资格

### 必做基线

rrBLUP/GBLUP或任务适用经典模型；XGBoost/LightGBM；单模态；简单拼接、early/late fusion；同架构随机初始化；去条件、去跨模态目标、去门控和去层级表示消融。

### 成功不等于

训练loss下降、单seed最高值、参数更多、训练更久、只超过弱基线、反复看测试调参，或直接比较不同任务/指标的绝对值。

### 基础模型资格

只有同一个冻结预训练release同时满足：预定义的至少3类任务、至少5 formal seeds、完整少样本曲线、至少2个迁移轴、2类缺失模态、2个模型规模×3个数据比例、严格外测、泄漏审计、数据卡和模型卡；并且在预先指定而非事后挑选的至少2类任务上，相对“最佳冻结强基线”和“同架构随机初始化”的Holm-adjusted同时95% CI下界都达到预注册MMED，才有资格讨论“作物多组学基础模型”。任一条件不满足都按证据降级命名，不能用极小但显著的差异或事后挑任务取得资格。

## 17. 角色和责任

| 角色 | 主要责任 | 不得单独决定 |
|---|---|---|
| 作物遗传育种/多组学 | 科学问题、条件轴、育种价值、因果边界 | 不得绕过统计/外测 |
| 数据工程 | 身份、版本、ID、配对、许可、QC | 不得把名称相似直接当同一样本 |
| 模型架构 | tokenizer、encoder、fusion、目标、消融 | 不得先定模型再找任务 |
| HPC/Slurm | 环境、资源、恢复、吞吐、日志 | 不得在门禁前启动GPU |
| 项目负责人/审稿人 | 预注册、基线、公平性、泄漏、措辞 | 不得隐藏负结果/缺失seed |

## 18. 主要风险和预案

| 风险 | 早期信号 | 预案 |
|---|---|---|
| 数据多但不能配对 | 只有品种/组织名，没有实体ID | 降级P2/P3或缩小到P1 |
| 许可不允许训练 | 条款模糊或需协议 | 保持NO_TRAIN，找替代或申请许可 |
| 重复提交夸大样本 | 多库记录指向同一文件 | accession＋checksum折叠后重算 |
| split泄漏 | 同品种、谱系、study或近重复跨split | 扩大分组单位并重新冻结 |
| 复杂模型不如基线 | 多seed validation无稳定增益 | 停止放大、简化或报告负结果 |
| 少数seed驱动结论 | 方差大、均值不稳 | 增加预注册seed或降级结论 |
| GPU预算失控 | 吞吐低、恢复失败 | 优化MVP并重做资源gate |
| 结论超出证据 | 用相关性写因果 | 降级措辞并独立复核 |

## 19. 三份核心文档维护规则

- `RESEARCH_PLAN.md`：计划、范围、门禁、指标或停止规则变化时更新；
- `RESEARCH_PROGRESS.md`：每个真实里程碑、作业、阻塞、错误或训练结果后更新；
- `MODEL_ARCHITECTURE.md`：输入、模块、任务、loss、规模、接口或冻结状态变化时更新。

### 强制更新触发器

1. gate状态变化；
2. 旗舰作物、模态、任务或独立单位确定；
3. 数据集进入A/B/C/NO-GO；
4. 许可或配对结论变化；
5. 架构、目标或规模冻结；
6. 产生第一条真实训练曲线/checkpoint；
7. baseline、pilot、formal test或失败路线完成；
8. 发现泄漏、撤回数据、错误指标或更正结论。

### 每次更新必须写清

日期/版本、变化的事实、机器证据、仍未知项、对下一阶段影响、图表是否同步、历史结论是否改变。不得静默删除旧错误，重要修订进入进展日志。任何会改变gate语义、输入集合、状态或PASS条件的修订都使受影响的旧receipt失效；必须生成新版本/hash并重做对应Gate和独立审查，旧R13不能自动为新合同背书。

### 版本记录

| 日期 | 版本 | 主要变化 |
|---|---|---|
| 2026-07-16 | v1.0 | 首次发布十阶段路线摘要 |
| 2026-07-16 | v2.0 | 增加零基础术语、来源到结论链、逐Gate输入/动作/产物/PASS/失败出口、统计/基线/停止规则、风险、现有接口边界和立即执行清单 |

## 20. 当前立即执行清单

当前只执行阶段1：

1. 运行合同和依赖`check-only`；
2. Europe PMC×Q1真实小规模smoke；
3. 核对receipt、导出、SHA-256和run登记；
4. 串行执行开放来源×Q1—Q12；
5. 去重并建立版本链；
6. 双人独立筛选和裁决；
7. 核验关键模型的论文/代码/权重/三类许可；
8. 生成证据综述和`stage1_gate.json`；
9. 同步更新三份核心文档；
10. 只有阶段1 PASS后才申请阶段2。

在这些步骤完成前，训练曲线应继续保持0个观测点。

## 21. 实施切片和命令状态

下表区分“内部审计工作区中真实存在的接口”和“未来阶段才定义的接口”。本公开GitHub仓库是文档交付，不包含阶段1/2执行脚本；下列命令只能在绑定R13证据的内部工作区运行，不能从本公开仓库直接复制执行。`TBD`不是可执行命令，也不是完成证据。

| 切片 | 当前文件/接口 | 目的 | 当前可用命令 | 成功信号 | 允许的下一步 |
|---|---|---|---|---|---|
| 阶段1单来源检查 | 内部：`scripts/stage1/run_literature_source.py` | 无网络/无写入核对source和query合同 | `python scripts/stage1/run_literature_source.py --source europe_pmc --query-id Q1 --check-only` | JSON `status=PASS`、exit 0 | 真实smoke |
| 阶段1真实smoke | 同上 | 仅验证首屏有界网络/export，不代表来源检索完成 | `python scripts/stage1/run_literature_source.py --source europe_pmc --query-id Q1 --execute --run-id <新建且唯一的run_id>`；仅在检查和网络前提满足后执行 | `FIRST_PAGE COMPLETED`＋唯一run/export；当前ERROR仅stdout | 只能实现/测试完整分页 |
| 阶段1完整分页 | `TBD / MANUAL-BLOCKED` | 在页数/字节/walltime硬预算内到官方终止cursor；检测重复/回退/no-progress | 当前无可执行命令 | 分页fixture、部分进度receipt、续跑和终止cursor测试PASS | 去重/版本链 |
| 阶段1证据处理 | `TBD / MANUAL-BLOCKED` | 去重、版本链、双筛/裁决、证据矩阵 | 当前无可执行命令 | 各步骤schema/receipt/外键PASS | 最终gate |
| 阶段1总gate validator | 内部：`jobs/stage1_completion_gate.sbatch` | 只读检查部分完成条件；当前只打印JSON日志 | `sbatch jobs/stage1_completion_gate.sbatch` | validator JSON；即使PASS也只是组件证据 | 实现final receipt producer |
| 阶段1最终receipt | `TBD / MANUAL-BLOCKED` | no-replace生成`stage1_gate.json`并重算全部hash/分页/饱和轮次 | 当前无可执行命令 | 最终receipt和独立审查PASS | 才可申请阶段2 |
| 阶段2来源检查 | 内部：`scripts/stage2/probe_metadata_source.py` | 无网络/无写入核对官方元数据probe合同 | `python scripts/stage2/probe_metadata_source.py --source <已登记来源> --check-only` | JSON PASS或真实BLOCKED | 获授权后元数据probe |
| 阶段2总gate validator | 内部：`jobs/stage2_completion_gate.sbatch` | 只读检查目录/身份/许可/配对闭合；当前只提供validator证据 | `sbatch jobs/stage2_completion_gate.sbatch` | validator JSON/日志；即使PASS也不是晋级receipt | 实现final receipt producer |
| 阶段2最终receipt | `TBD / MANUAL-BLOCKED` | no-replace生成`stage2_gate.json`，绑定stage1 receipt、授权、目录/身份/许可/配对/访问日志及全部文件hash | 当前无可执行命令 | 原子receipt、失败receipt和独立复验PASS | 才可进入阶段3 |
| 阶段3—9 | `TBD（在对应上游Gate PASS后命名）` | 避免计划伪装成已实现代码 | 当前无可执行命令 | 未来文件、测试、锁和命令经审查冻结 | 仅进入对应下一Gate |

命令是否存在、单个命令exit 0、图件能打开都只是组件证据；阶段PASS还必须满足该阶段全部输入、输出、receipt和失败出口。
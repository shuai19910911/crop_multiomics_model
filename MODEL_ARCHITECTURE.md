# 作物多组学候选模型架构

- 文档版本：v2.0
- 最后更新：2026-07-16
- 架构状态：**CANDIDATE / NOT FROZEN（候选，尚未冻结）**
- 训练状态：0 runs、0 optimizer updates、0 checkpoints
- 配套文件：[研究计划](RESEARCH_PLAN.md) · [研究进展](RESEARCH_PROGRESS.md)

> 本文解释“如果证据和数据支持，模型可能怎样组织”，不是已经实现或验证的最终模型。层数、宽度、参数量、token数、模态组合、损失权重和任务路由均未冻结。

## 0. 零基础读者先看这里

### 0.1 模型架构是什么？

模型架构是数据在模型内部的路线图：输入什么，怎样转换成模型可读单位，每种数据如何提取特征，在何处融合，通过什么目标学习，怎样用于表型等任务，以及怎样隔离测试信息。

### 0.2 为什么仍是候选方案？

当前尚未完成系统文献检索和真实数据审计。只有知道数据来自哪些作物、有哪些模态、怎样配对、缺失率多少和任务是什么，才能决定结构。现在给出固定层数或参数量会是假精确。

### 0.3 当前真正确定的原则

- 不同模态先分别编码；
- 物种、种质、组织、时期、处理、环境和批次是显式条件轴；
- 多模态融合必须处理缺失模态；
- 复杂融合必须与单模态、简单拼接、early/late fusion比较；
- 预训练收益必须与同架构随机初始化比较；
- 外部测试完全独立，不是模型输入或选择信号。

## 1. 两个架构图版本

### 1.1 Python可复现候选全集图

由仓库脚本确定性生成，用于展示候选组件全集，不表示五类输入、分层fusion、门控、三个目标和四类任务已被同时选中或实现。冻结前以本文状态表为准；未来只有阶段4机器合同和冻结配置才是可执行权威。

![Python candidate architecture](docs/assets/figure_generations/6a0047ecb939a2b119aef75ef1d29d9bd1a4c9332e2452c7430d6829cd195e09/model_architecture_python.png)

下载：[PNG](docs/assets/figure_generations/6a0047ecb939a2b119aef75ef1d29d9bd1a4c9332e2452c7430d6829cd195e09/model_architecture_python.png) · [PDF](docs/assets/figure_generations/6a0047ecb939a2b119aef75ef1d29d9bd1a4c9332e2452c7430d6829cd195e09/model_architecture_python.pdf) · [生成脚本](scripts/figures/render_public_figures.py)

### 1.2 GPT视觉概念图

用于帮助理解生物学层次和视觉关系，不是机器可执行结构合同。

![GPT candidate architecture](docs/assets/figure_generations/6a0047ecb939a2b119aef75ef1d29d9bd1a4c9332e2452c7430d6829cd195e09/model_architecture_gpt.png)

下载：[PNG](docs/assets/figure_generations/6a0047ecb939a2b119aef75ef1d29d9bd1a4c9332e2452c7430d6829cd195e09/model_architecture_gpt.png) · [PDF](docs/assets/figure_generations/6a0047ecb939a2b119aef75ef1d29d9bd1a4c9332e2452c7430d6829cd195e09/model_architecture_gpt.pdf)

### 1.3 怎样读图？

从左到右：五类候选输入→各自tokenizer/encoder→条件感知分层融合→候选预训练目标和任务表示→四类下游任务。这是一张“设计空间地图”，不是当前已选单一路径。最底部红色区域画的是未来必须建立的评价防火墙；`frozen split`、`external seal`和`leakage audit`目前都未生成，状态为`PLANNED / NOT YET VERIFIED`，红色区域不向训练回流。

图为避免拥挤省略了条件到encoder/fusion/head的候选箭头，也未画出单模态、early/late fusion对照。环境模态指天气、土壤、管理等实际测量；条件轴指物种、组织、时期、处理和试验上下文。平台、实验室和batch默认用于审计、分层或校正，不自动作为预测特征；只有任务合同允许且通过捷径检查后才能输入模型。

两张图只列出masked reconstruction、cross-modal matching和contrastive alignment三个核心候选目标；第12.4节的条件/层级目标只是图外探索性辅助probe，阶段4未证明有效前不能加入正式拓扑。

## 2. 术语白话解释

| 术语 | 白话解释 |
|---|---|
| token | 模型一次处理的基本单位，如碱基窗口、变异或基因 |
| embedding | 把ID、数值或类别转成向量 |
| encoder | 从一种模态中提取信息的模块 |
| fusion | 把多种模态表示合并 |
| mask | 告诉模型哪些位置/模态有效、哪些缺失 |
| gating（门控） | 根据可用信息决定让哪些通路贡献多少 |
| objective/loss | 训练时模型要最小化的误差 |
| task head | 把通用表示转换成某个任务输出的小模块 |
| contrastive learning | 让应相近的表示靠近、真正不同的表示分开 |
| early/late fusion | 较早/较晚合并模态 |
| checkpoint | 某个训练步骤保存的参数 |
| ablation | 移除模块以检验其真实贡献 |
| P1配对 | 两种测量来自同一生物实体或有明确分样证据，可作严格跨模态正例 |
| P2配对 | 条件近似但不是同一实体，只作敏感性分析 |
| P3配对 | 无实体配对的同分布数据，只作单模态训练或分布比较 |
| P4配对 | 只有同源/通路等弱锚，只作预注册弱监督探索 |
| PX配对 | 身份冲突或证据不足，不进入配对训练 |
| G×E | 基因型与环境互作，即材料在不同环境中的表现差异 |
| orthogroup | 不同物种中来自共同祖先的一组同源基因 |
| homeolog | 多倍体不同亚基因组中的对应基因副本，不能随意合并 |
| train / validation / external test | 用于拟合 / 用于选择 / 只用于最终独立评价的数据 |
| valid mask | 当前位置是否属于真实token，而不是padding |
| callable mask | 原始测量在该位置是否具备可靠检测能力 |
| unknown/loss mask | 标签未知或不应计入loss的位置 |
| reset mask | 序列边界处是否必须清空递归/状态空间记忆 |
| microbatch | 一次在设备上前向和反向的小批样本 |
| gradient accumulation | 多个microbatch梯度累积后才做一次optimizer step |

## 3. 架构冻结状态

| 决策 | 当前状态 | 候选范围 | 冻结证据 |
|---|---|---|---|
| 旗舰作物 | UNKNOWN | 单作物或多作物 | 文献、数据、许可、外测价值 |
| 首版模态 | UNKNOWN | 基因组、转录、调控、蛋白/代谢、环境 | 非空目录和配对矩阵 |
| token单位 | UNKNOWN | 碱基、窗口、变异、基因、同源组、样本 | 任务、稳定性、成本 |
| 每模态encoder | CANDIDATE | 序列、集合/表格、图或混合 | 数据形状和pilot |
| 条件表示 | CANDIDATE | embedding＋分层交互 | 去条件消融和跨环境结果 |
| fusion | CANDIDATE | early、late、hierarchical | 公平预算validation消融 |
| 缺失模态 | CANDIDATE | mask、门控、modality dropout | 真实缺失分布和压力测试 |
| 预训练目标 | CANDIDATE | masked、matching、contrastive | 配对证据和负迁移pilot |
| 模型规模 | UNKNOWN | 至少比较两个规模 | 吞吐、显存、样本和缩放 |
| 任务头/路由 | UNKNOWN | 四类候选任务 | headline task合同 |
| loss权重 | UNKNOWN | 仅在train/validation选择 | 任务尺度和稳定性 |
| 参数量 | UNKNOWN | 不预设 | 宽度、深度、词表冻结后计算 |
| checkpoint规则 | READY / NOT FROZEN | 只用validation选择 | winner合同 |
| 外测访问 | NOT AUTHORIZED | Stage5 seal、Stage6/7总Gate、power、完整比较矩阵、formal-pretest、双registry均PASS后的一次性claim | canonical identity-family及独立单位零重叠，claim原子消费成功 |

## 4. 一个样本如何流过模型

以下只是概念示例，不代表已找到这类真实数据。

假设某个身份核验后的作物样本有基因型、叶片转录组、同一叶片split aliquot代谢组以及处理时间/环境记录：

1. 身份层确认文件是否属于同一个individual/biological sample；
2. 条件层记录物种、品种、组织、时期、处理、site-year-trial和batch；
3. tokenizer把变异、基因表达和代谢物分别变成token；
4. 三个encoder分别提取表示；
5. mask标记调控组/蛋白组缺失，而不是把“未测”伪装成真实0；
6. fusion在条件和生物层级约束下合并已有模态；
7. 预训练目标只对证据允许的配对计算loss；
8. task head从表示生成冻结任务的预测；
9. validation用于选择；
10. external test保持封存，直到一次性正式评价。

如果转录和代谢只是同品种同组织、但来自不同个体，就不能按P1严格配对计算cross-modal matching。

### 4.1 当前符号张量合同

真实模态和长度尚未冻结，因此这里使用符号，不填假数字。阶段4只能依据阶段2已批准的metadata/schema给出维度上界，并用不含真实值的合成最大shape fixture替换TBD、独立复算显存和参数；不得读取尚未由阶段5冻结的真实输入。阶段5发布唯一data/split release后，阶段6再用其中真实最大长度样本确认该合同。

| 符号 | 含义 | 候选shape |
|---|---|---|
| `B` | microbatch中的样本数 | 整数，TBD |
| `T_m` | 模态`m`每个样本的最大token数 | 整数，按模态TBD |
| `F_m` | 原始token特征维 | 整数，按模态TBD |
| `D_m` | 模态encoder隐藏维 | 整数，按模态TBD |
| `X_m` | 模态原始输入 | `[B, T_m, F_m]`或离散ID `[B, T_m]` |
| `H_m` | 模态token表示 | `[B, T_m, D_m]` |
| `z_m` | 模态样本表示 | `[B, D_m]` |
| `z_condition` | 条件表示 | `[B, D_c]`，`D_c` TBD |
| `z_fused` | 融合样本表示 | `[B, D_f]`，`D_f` TBD |
| `ŷ_task` | 任务预测 | `[B, Y_task]`或token级shape |

### 4.2 四类mask不能混用

| mask | True表示 | 可以控制 | 不能替代 |
|---|---|---|---|
| `mask_valid[B,T_m]` | 真实token、非padding | attention/pooling/有效token计数 | 测量是否可检测 |
| `mask_callable[B,T_m]` | 该位置测量可靠 | 负例资格、可评价范围 | token是否存在 |
| `mask_loss[B,T_m]` | 标签已知且允许算loss | loss分子/分母 | 序列边界 |
| `mask_reset[B,T_m]` | 此位置前必须重置状态 | recurrent/SSM片段隔离 | padding或未知标签 |

如果未来采用双向递归或状态空间encoder，反向分支不能简单翻转`reset-before`标记；必须先按正向边界生成segment ID，反转有效token和segment ID，再从相邻反向segment重新生成reset，并分别测试左右片段互不影响。

### 4.3 最大shape设计与真实样本确认模板

阶段4先用metadata/schema维度上界和合成fixture填写设计模板：`fixture/hash → T_m/F_m → 四类mask计数 → tokenizer输出 → 每层shape → fusion输入/输出 → 每个head输入/输出 → 估算显存/耗时`；这只能把架构从CANDIDATE推进到DESIGN FROZEN。阶段5 PASS后，阶段6才从冻结release取真实最大长度样本，补充`sample_id/hash → 各模态source/version → P1/P2等级`并生成真实trace receipt；未完成时不得声称实现已确认。若真实trace推翻shape/预算合同，必须回阶段4修订并重发阶段5 release。

## 5. 输入层

### 5.1 基因组和变异

可能输入：参考序列、SNP/indel、结构变异、单倍型、基因型剂量、基因/调控坐标。

候选token：单碱基、序列窗口、变异位点、单倍型block、基因/调控区域、orthogroup。

必须记录assembly accession.version、参考/替代等位、链、坐标、剂量和注释版本。主要风险是assembly错配、同名基因跨版本不等价、亲缘跨split、序列近重复/反向互补泄漏、多倍体homeolog误合并。

### 5.2 转录组

可能输入：bulk RNA-seq、单细胞/单核、空间、时间序列表达。

候选token：基因、转录本、细胞、伪bulk样本或通路。

必须记录组织/细胞、时期、处理、时间、平台、建库、实验室、batch、归一化和注释版本。风险包括技术重复当生物重复、bulk与单细胞只按组织名配对、全数据归一化和测试标签参与过滤。

### 5.3 调控和表观组

可能输入：ATAC-seq、甲基化、组蛋白修饰、染色质互作、调控元件。候选token是peak、窗口、元件、基因邻域或基因—元件边。

必须记录组织/细胞、处理、时间、协议、peak caller、assembly和坐标。不同协议/peak集合不能直接比较；用全体数据构建统一peak universe也可能泄漏。

### 5.4 蛋白组和代谢组

可能输入：蛋白丰度、肽段、代谢峰、已鉴定代谢物、通路。候选token是蛋白、肽、代谢物、峰或通路。

必须记录平台、离子模式、鉴定置信度、批次、内标、单位、组织、时间和处理。风险是未鉴定峰难对齐、同名代谢物不是同一实体、缺失语义不一、batch大于生物信号。

### 5.5 环境和实验设计

输入可含地点、年份、天气、土壤、管理、处理、剂量、随机化、block和对照。环境不是普通附加列：同一基因型在不同环境可产生不同表达和表型。

风险包括site/year/trial误拆、同一trial的plot跨split、未来天气/结果衍生变量泄漏、batch与处理完全混杂。

## 6. 输入合同

每种模态进入模型前必须冻结：

| 字段 | 要回答的问题 |
|---|---|
| source | 来自哪个官方来源/版本？ |
| entity | 每行或token对应哪个生物实体？ |
| unit | 最小输入单位是什么？ |
| namespace/version | ID体系和版本是什么？ |
| shape | sample、token、feature维怎样定义？ |
| missingness | 缺失表示什么，mask怎样编码？ |
| preprocessing | 哪些变换只在train拟合？ |
| pairing level | P1/P2/P3/P4/PX中的哪一级？ |
| conditions | 哪些条件必须随输入进入？ |
| license | 是否允许训练/衍生权重？ |
| split restrictions | 哪些group绝不能跨split？ |
| checksum | manifest及内容hash是什么？ |

关键字段缺失时应fail closed，而不是猜默认值。

## 7. Tokenizer

DNA、表达、代谢物和环境的单位/尺度/缺失语义不同，不能无条件共用tokenizer。

新手可把模态前端理解为五步：`原始record → 身份/版本核对 → 只在train拟合的预处理 → 切成token单位 → 数值/类别embedding → encoder`。token单位回答“一个token代表什么”，切分/聚合回答“怎样得到token序列”，embedding回答“怎样变成向量”；三者不能混称。下表为节省篇幅列的是候选前端组合，阶段4必须把三部分分别冻结。

| 模态 | 候选前端（token单位/切分/embedding） | 优点 | 风险 |
|---|---|---|---|
| DNA | k-mer、BPE、碱基、长窗口 | 学习局部/长程序列 | 序列长、重复和版本复杂 |
| 变异 | 位点、单倍型、基因聚合 | 对应个体基因型 | 稀疏、assembly/剂量敏感 |
| 表达 | 基因token＋丰度embedding | 保留基因身份 | 跨平台归一化复杂 |
| 表观组 | peak、窗口、基因邻域 | 保留调控位置 | peak universe可能泄漏 |
| 蛋白/代谢 | 实体或通路token | 可利用知识 | ID不稳、未鉴定峰多 |
| 环境 | 连续值＋类别embedding＋时间编码 | 显式条件 | 缺测、时间泄漏、尺度问题 |

阶段4根据覆盖、任务、版本稳定性、吞吐和显存选择，而不是按流行度。

## 8. 模态特异Encoder

概念接口：

`X_m → Encoder_m(X_m, condition_m) → H_m`

`m`表示模态，`H_m`是该模态表示；数值维度尚未冻结。

候选包括序列Transformer/卷积/状态空间模型、稀疏变异集合encoder、基因/样本集合Transformer、有证据图的GNN，以及环境/表格的MLP或树模型。低样本模态优先轻量encoder以减少过拟合。

统一输出至少包含token级表示、entity/sample级表示、有效token mask、modality-present mask、条件表示及输入版本/hash引用。

不允许encoder隐式使用全体数据归一化、把缺失静默填0、加载未登记外部知识、根据外测调整词表或静默丢弃无法映射实体。

## 9. 条件编码

条件轴候选至少包括物种、生态型、品种/种质、群体/系谱、组织/细胞、时期、时间、处理、剂量、地点、年份、天气、土壤、管理和block。平台、实验室和batch默认是技术审计/校正变量，不是生物学条件或预测特征；若任务合同允许输入，必须证明模型没有靠技术捷径取得表面高分。与“环境模态”重叠的字段必须在冻结合同时指定唯一角色，禁止同一信息重复进入两条通路。

候选注入：

1. 输入级条件embedding与token组合；
2. 用条件调制层内归一化/门控；
3. gene→sample→tissue→environment层级交互；
4. 任务头读取冻结条件表示；
5. 完全去条件对照。

必须比较无条件、末端拼接、输入条件化、分层条件交互，并在跨环境/年份split上检查。如果条件只改善随机split却损害跨环境泛化，应降低结论。

## 10. 三个Fusion候选路线

### 10.1 Early fusion

较早把模态映射到共同空间并合并。交互充分，但依赖严格配对，缺失和尺度差异难处理，计算可能较大。

### 10.2 Late fusion

各模态独立深度编码，在任务头附近合并表示/预测。对缺失更友好、易复用单模态，但可能错过细粒度交互。

### 10.3 Condition-aware hierarchical fusion

保留模态内结构，再按gene/entity、sample、tissue、environment层级融合，用条件和缺失mask控制交互。它符合候选生物层级，但更复杂、需要可靠身份图，也可能不如简单模型稳定。

### 10.4 选择规则

三条路线在相同数据、split、核心参数预算、训练步数和调参预算下比较。按多seed validation、资源、缺失鲁棒性和跨域表现选择，不按单任务最高值。

## 11. 缺失模态处理

“没有测量”不等于真实数值0。表达0可能是无表达，也可能未检出；整种组学不存在是模态缺失，三者必须区分。

候选机制：modality-present mask、token missing mask、missing-modality gating、modality dropout、可用模态路由、late fusion；模型生成的伪模态不能冒充真实测量。

至少测试完整模态、每次缺一类、缺两类、训练常见但测试少见的缺失组合，并与填零、均值填充和最佳单模态比较。缺失模式按真实分布报告，不能只构造有利随机缺失。

## 12. 候选预训练目标

概念总损失：`L_total = Σ λ_i × L_i`。`L_i`为目标，`λ_i`为权重；具体目标和权重未冻结，只能在train/validation选择。

### 12.1 Masked reconstruction

遮住序列窗口、基因或条件，让模型恢复。必须检验恢复能力是否转化为下游收益，不能只看重构loss。

### 12.2 Cross-modal matching

判断模态是否来自同一实体/兼容条件。正例原则上需P1；负例不能把同一克隆、谱系或重复提交当真正独立负例。配对错误会让模型学习数据库/batch捷径。

### 12.3 Contrastive alignment

让应相近的表示靠近，真正不同的表示分开。必须冻结正例、负例、温度、采样和身份排除。错误负例会破坏表征。

### 12.4 条件/层级探索性辅助目标（图中未列）

可探索组织、处理、环境或同源组一致性，但要排除模型只学到batch的可能。

### 12.5 多目标负迁移

比较单目标、两目标、全目标、固定/动态权重，并逐任务/模态报告。平均分不能掩盖某任务明显下降。

### 12.6 目标样本构造和调度合同

| 目标 | 正例/可计算位置 | 排除项 | 必须冻结的调度 |
|---|---|---|---|
| masked reconstruction | train内`valid ∩ callable ∩ loss-allowed`位置 | padding、未知、外测和禁用条件 | mask比例/跨度、每模态配额、随step变化 |
| matching | 有证据的P1同实体/条件兼容配对 | P2—PX、重复提交、同克隆假负例 | 正负比例、难负例阶段、模态对 |
| contrastive | P1或预注册同源/条件正例 | 身份重叠、测试来源、未核验知识边 | 温度、队列/批内范围、每物种配额 |
| 条件/层级 | train内具备冻结条件标签的单位 | batch捷径、未知条件、外测标签 | 任务采样概率、warm-up和loss权重 |

多GPU时每个loss必须先分别累加有效分子和分母，再跨rank汇总后归一化；不能把各rank均值再平均，否则不同有效token数会改变权重。具体构造函数、RNG、seed和权重schedule均在阶段4冻结。

## 13. 下游任务头和路由

### 13.1 分子状态预测

根据基因型、条件或其他模态预测表达、调控、蛋白或代谢状态。必须冻结预测单位、标签、条件、指标和独立样本单位。

### 13.2 表型和G×E预测

预测材料在环境中的产量或抗逆表型。防止同品种、地点、年份或trial跨split；亲缘矩阵不能使用测试材料。基线包括rrBLUP/GBLUP、反应规范和强表格模型。

### 13.3 基因/变异优先排序

输出候选分数/排序。必须定义候选全集、正例、操作性负例、未知、Top-k、指标和独立block。高分只支持“优先验证”，不自动支持因果。

### 13.4 跨物种和少样本迁移

明确训练/目标物种、同源映射、标签一致性和迁移单位。少样本至少报告1%、5%、10%、100%，并与随机初始化比较。

### 13.5 路由合同

每个任务必须写明读取单模态还是融合表示、读取token还是sample表示、是否读环境、缺失时走哪条路径。不能出结果后临时改变。

## 14. 模型输出接口

| 输出 | 符号 | 用途 |
|---|---|---|
| 模态token表示 | `H_m[token]` | token重构和解释 |
| 模态样本表示 | `z_m` | 单模态任务/late fusion |
| 融合表示 | `z_fused` | 多模态任务 |
| 条件表示 | `z_condition` | 环境/组织/处理条件化 |
| 模态mask | `mask_modality` | 缺失门控 |
| 任务预测 | `ŷ_task` | 下游评价 |
| loss分项 | `L_i` | 诊断各目标贡献 |

正式实现还要输出run ID、数据/split/config/code hash和checkpoint身份，防止预测与模型版本失配。

### 14.1 下游head参数闭合模板

| head | 输入拼接 | 输出 | 参数闭合要求 |
|---|---|---|---|
| 分子状态 | `z_fused[D_f] + z_condition[D_c]`或冻结token表示 | `Y_mol`维回归/分类 | 写明Norm、每层`in×out`、bias、激活和总参数 |
| 表型/G×E | `z_genotype[D_g] + z_environment[D_e] + z_condition[D_c]` | trait数`Y_trait` | 环境编码、交互层和每trait损失逐项列出 |
| 基因/变异排序 | entity表示`H_entity[D_e] + query[D_q] + condition[D_c]` | 每候选一个score | query表、adapter、pooling和候选数上限纳入参数 |
| 跨物种适配 | 冻结/可训练表示＋species/orthogroup adapter | 任务特定输出 | 冻结参数与可训练参数分开计数 |

基础算式示例：带bias的`Linear(a,b)`参数为`a×b+b`，含scale和bias的`LayerNorm(a)`参数为`2a`。阶段4必须把所有符号替换成整数，逐层求和并与框架实际参数逐名比较；任何未列出的projection、query table、adapter或norm都使冻结失败。

## 15. 基线和消融矩阵

| 类别 | 必做比较 | 回答的问题 |
|---|---|---|
| 经典统计 | rrBLUP/GBLUP、反应规范 | 是否超过领域强方法 |
| 表格机器学习 | XGBoost/LightGBM | 是否超过强非深度模型 |
| 单模态 | 各模态最佳模型 | 多模态是否增加信息 |
| 简单融合 | 拼接、early、late | 分层fusion是否必要 |
| 预训练对照 | 同架构随机初始化 | 增益来自预训练还是架构 |
| 条件消融 | 无条件、末端、分层 | 条件建模是否必要 |
| 目标消融 | 去masked/matching/contrastive | 哪个目标有效/负迁移 |
| 门控消融 | 填零、无门控、门控、dropout | 缺失策略是否有效 |
| 层级消融 | 逐层移除 | 生物层级是否贡献 |
| 规模/数据 | ≥2规模×≥3数据比例 | 是否存在缩放证据 |

预算公平包括相同数据、split、主要训练资源和调参机会，不能复杂模型调很多次而基线只跑默认。

## 16. 训练更新、恢复和评价防火墙

### 16.1 一个optimizer step的候选顺序

1. sampler只从冻结train release取一个microbatch，并返回sample/split ID；
2. 校验数据、配置和code hash，建立四类mask；
3. sampler先物化一个由`K`个microbatch组成的optimizer window并冻结RNG/样本顺序；在不更新参数的objective-selection预遍历中，为每个目标实际生成并记录随机masked位置、matching配对、contrastive anchor/positive及其他objective-specific eligibility；如选择依赖当前表示，则做可复放的no-grad首遍并绑定选择hash。四类mask只是生成这些选择的输入，不能单独充当分母；
4. 从记录的实际objective选择计算每个目标在全部`K×rank`上的精确有效项数并all-reduce；分母为0按冻结合同跳过该目标或报ERROR，禁止除零/补数。随后前向必须复用同一选择hash，只生成对应objective分子，按“该分子÷全window对应分母”及冻结`λ_i`反向；DDP平均/求和缩放规则必须与单进程全window参考实现逐梯度一致；
5. 累积完`K`个microbatch后再做一次更新；日志使用全window的`Σ numerator / Σ denominator`，禁止先算microbatch均值再平均；
6. 到更新边界后unscale、检查NaN/Inf、按冻结规则裁剪梯度；
7. optimizer真正更新一次参数，scheduler按累计有效token或step推进；
8. `zero_grad`，记录step、有效token、各loss、学习率、梯度/吞吐/显存；
9. 到保存点时，在临时目录写模型、optimizer、scheduler、scaler、sampler/RNG、dataloader位置和hash；
10. fsync并原子发布checkpoint及`READY`，发布后不修改。

microbatch大小、`K`、optimizer、学习率、scheduler、精度、梯度裁剪、更新/保存间隔均未冻结。它们在阶段4必须成为配置和测试，而不是留给运行时默认值。

### 16.2 精确恢复

同一checkpoint恢复后，下一批sample ID、mask、随机增强、loss、学习率和随后固定若干step的参数必须与不中断参考run一致（在冻结容差内）。只恢复模型权重、不恢复optimizer/RNG/sampler不算精确恢复。SIGTERM/超时/OOM后的run状态必须真实记录，不能覆盖原run。

### 16.3 train/validation/formal external test权限

- **训练集**：计算梯度和更新参数；归一化、插补、词表、PCA、亲缘矩阵、特征选择原则上只在训练范围拟合。
- **验证集**：选择checkpoint、超参数、loss权重、阈值和模型版本；不得计算梯度。
- **正式外测**：这是唯一test角色；本项目不另设可反复查看的internal test。它只做冻结后的最终评价，不得反向修改模型，标签需seal并由canonical identity-family、完整比较矩阵和两级append-only registry原子消费的一次性claim开放。

图底部红色防火墙专指external/formal-test标签、预测和指标：它们只能用于最终报告，不能指回tokenizer、encoder、fusion、loss或checkpoint。validation不在红色外测禁区内，可按预注册规则单向用于checkpoint/超参数/model selection，但不得计算梯度或改变已冻结split/外测seal。

### 16.4 Metadata-only split防火墙

split构建器只可读取冻结白名单metadata：record身份、来源、study、site-year-trial、plot/individual、谱系/同源group、assay/tissue/condition和measurement-presence；assembly坐标、目标类别、效应大小、表达/表型/原始组学值、类别比例、全数据结局统计或formal阈值都不得读取。split冻结后，validation阶段才能检查真实标签支持量；支持不足只能BLOCKED或按预注册规则降级，不能看标签后重新分组制造平衡。formal external值在唯一claim前始终不可读。

## 17. 架构冻结合同

正式实现前，以下必须从UNKNOWN/TBD变为具体值。

### 数据和输入

物种/数据版本、模态/配对等级、token/词表、输入shape、条件轴、缺失编码、train-only预处理、split、seal引用。

### 模型

每个encoder类型/层数/宽度/参数、fusion位置、condition注入、缺失机制、任务头/路由、loss定义/样本/权重、总参数/可训练参数/初始化来源。

### 优化

optimizer、学习率/scheduler、batch/梯度累积、精度、步数/epoch、checkpoint、early stopping、seed、OOM和恢复策略。

### 选择和统计

主要validation指标、winner公式、baseline搜索预算、formal seed数、CI/block、最小效应和power receipt。

任一关键字段为空、TBD或无法回读时，正式训练gate应`BLOCKED`。

## 18. 实现里程碑

M0—M9是总体研究阶段3—8内部的架构实施子里程碑，不替代研究计划中的阶段0—9；每个M项必须引用所属总体阶段和Gate receipt。

| 里程碑 | 内容 | 通过条件 | 状态 |
|---|---|---|---|
| M0 接口草案 | 符号输入/输出/mask | 文档一致、无假参数 | 本文完成 |
| M1 数据fixture | 极小结构测试 | schema/mask/身份边可测 | 未开始 |
| M2 静态设计冻结 | 张量、条件、fusion、loss、pilot/power函数；仅metadata维度上界和合成fixture | 阶段4设计receipt完整；不读取真实值、不训练 | 未开始 |
| M3 数据/split冻结 | metadata-only split、formal external seal、train-only预处理 | 阶段5泄漏门禁PASS | 未开始 |
| M4 单模态baseline | 每模态最小模型/强基线 | 阶段6冻结数据流/指标可复算 | 未开始 |
| M5 简单融合 | 拼接、early、late | 阶段6公平validation | 未开始 |
| M6 smoke与validation pilot | 前向/反向/恢复、真实最大长度trace、强基线、多seed小预算 | 阶段6方差/power可复算 | 未开始 |
| M7 pilot后合同确认 | winner、formal seeds和架构合同确认 | 若设计改变则回阶段4并重发阶段5 release | 未开始 |
| M8 正式训练 | 多规模×多比例 | run全部登记 | 未开始 |
| M9 formal test | 完整winner/随机初始化/强基线矩阵的一次性外测 | Stage5 seal、Stage6/7 Gate、power、formal-pretest、canonical identity-family与双registry均PASS；claim原子消费和后置gate PASS | 未开始 |

合成fixture只检查代码形状和错误处理，不能产生科研结果。

### 18.1 模块—测试矩阵

| 模块 | 最小正向测试 | 必须失败的负向测试 | 当前状态 |
|---|---|---|---|
| 数据读取/身份 | 同一sample和P1边可回读 | 伪P1、版本错配、跨split重复 | 未实现 |
| split builder | 白名单metadata可稳定生成`train/validation/formal_external_test` | 读取标签/组学/效应/外测bytes必须失败；支持量不足只能BLOCKED | 未实现 |
| tokenizer | token/shape/词表hash确定 | 未登记ID、test拟合词表、静默截断 | 未实现 |
| 四类mask | 手工fixture逐位一致 | valid/callable/loss/reset互相替代 | 未实现 |
| encoder | 最大长度前向/反向shape正确 | padding影响pool、片段跨reset串扰 | 未实现 |
| fusion/缺失 | 全模态和缺一/二模态可运行 | 未测模态被当真实0、无mask访问 | 未实现 |
| objective | 分子/分母和跨rank结果可复算 | P2假正例、同克隆假负例、test样本 | 未实现 |
| task head | 拼接维、输出、loss和参数和一致 | 未知标签进loss、未登记projection | 未实现 |
| trainer | 不等有效分母的`K×rank`累积逐梯度等于单进程全window参考step | mean-of-means、NaN仍更新、scheduler错位、seed漂移 | 未实现 |
| checkpoint | 中断恢复固定step一致 | 缺optimizer/RNG/sampler仍标完整 | 未实现 |
| evaluator | 保存预测可重算指标/CI | validation写梯度、external参与选择 | 未实现 |

上表任何一行通过只是组件PASS；架构Gate还需全部冻结合同、真实最大样本trace、资源/power和跨组件闭环。

## 19. 失败模式和诊断

| 现象 | 可能原因 | 先检查 | 不能直接下的结论 |
|---|---|---|---|
| train loss降、validation不升 | 过拟合/任务不匹配 | split、重复、正则、baseline | 多训练就会好 |
| 多模态不如单模态 | 错配、噪声、负迁移 | P1、模态/目标消融 | 多组学无用 |
| 随机split好、跨环境差 | 记住品种/site/batch | group split、条件消融 | 泛化很好 |
| 某seed特别高 | 方差或偶然选择 | 全seed、日志、CI | 只报最高seed |
| 缺模态时崩溃 | 依赖全模态 | mask、dropout、门控 | 用填充掩盖 |
| contrastive好、下游差 | 目标任务不一致 | 正负例、P1、目标消融 | 表征一定好 |
| 复杂模型只略高且昂贵 | 效率低 | 配对CI、GPU小时、简单基线 | 只看最高分 |
| 外测低于validation | 漂移或过拟合 | seal、group、选择次数 | 回头调外测 |

## 20. 架构文档维护

以下事件必须更新本文和架构图：旗舰作物/模态冻结；token确定；encoder/fusion/路由变化；目标加入/删除；规模/参数/预算冻结；缺失策略变化；消融证明模块无效；配对/许可/泄漏导致降级；状态从CANDIDATE变FROZEN；formal test后结论降级。

每次同步修改版本、状态表、图、冻结合同、实现里程碑、进展日志和研究计划。GPT图不能单独作为结构变更依据；Python图和机器合同先更新。

## 21. 版本记录

| 日期 | 版本 | 状态 | 变化 |
|---|---|---|---|
| 2026-07-16 | v1.0 | CANDIDATE | 首次发布五类输入、分层融合、三目标、四任务、防火墙 |
| 2026-07-16 | v2.0 | CANDIDATE | 增加符号张量、四类mask、真实最大样本模板、目标样本构造、head参数闭合、optimizer step/精确恢复、metadata-only split、模块测试矩阵和FAQ |

## 22. 小白常见问题

### Q1：五类输入是不是第一版全用？

不是。它们是候选，首版只选许可清楚、配对可信且对任务有价值的模态。

### Q2：为什么每种模态各自编码？

DNA、表达、代谢和环境单位不同；分开编码保留结构，也便于模态缺失时工作。

### Q3：fusion越早越好吗？

不一定。早融合交互多但依赖配对；晚融合更稳。必须公平比较。

### Q4：预训练loss最低就是最好吗？

不是。最终看冻结任务、强基线、跨域和外测。

### Q5：参数越多越强吗？

不是。可能更过拟合且更昂贵；要比较规模和资源。

### Q6：缺失模态为何不能填0？

0可能是真实生物值；“没测”需mask/门控区分。

### Q7：GPT图能直接实现吗？

不能。实现以Python图、冻结合同、配置和代码为准。

### Q8：何时从CANDIDATE变FROZEN？

阶段1—3确定数据/任务，阶段4冻结模块/loss/规模/资源/统计并通过gate后。

### Q9：分层fusion不如拼接怎么办？

选择更简单方案并如实报告。目标是可信结论，不是保护复杂架构。

### Q10：为何外测单独放底部？

它只做最终评价，不能向设计、训练或选择反馈。
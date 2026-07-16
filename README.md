# Crop Multi-Omics Model

面向作物多组学预训练的可审计研究工程。目前已完成阶段0治理封版；系统文献检索、数据许可/配对审计和模型架构冻结仍待执行。

> 当前没有训练结果。仓库中的“训练曲线”忠实显示0个训练run、0次参数更新和0 GPU小时，不含模拟或补造指标。

## 当前状态

| 项目 | 状态 |
|---|---|
| 阶段0：治理、资源与终结审查 | **COMPLETE** |
| 阶段1：系统文献与现有模型核验 | 已授权启动，尚未执行 |
| 阶段2：数据身份、许可与配对审计 | BLOCKED |
| 模型架构 | CANDIDATE / NOT FROZEN |
| 训练 | NOT STARTED |
| 正式外测、GPU和大规模下载 | NOT AUTHORIZED |

## 公开文档

- [研究计划](RESEARCH_PLAN.md)
- [研究进展（含训练曲线状态图）](RESEARCH_PROGRESS.md)
- [候选模型架构（含GPT概念图与Python可复现图）](MODEL_ARCHITECTURE.md)

## 一图概览

### 训练进展

![Training progress](docs/assets/training_progress.png)

### 候选架构（Python权威图）

![Candidate architecture](docs/assets/model_architecture_python.png)

## 科学边界

- 旗舰作物、首版模态、基本表征单位、核心下游任务、最终拓扑和参数规模均未冻结。
- “基础模型”不是预设名称；只有多任务、少样本、跨域、缺失模态、缩放、强基线和严格外测全部闭合后才有资格使用。
- 成功判据不是训练loss下降，而是相对同架构随机初始化和强基线的稳定、配对、可重复增益。
- 测试集不得用于checkpoint、阈值、损失权重、超参数或模型版本选择。

## 图件下载

| 图件 | PNG | PDF | 来源 |
|---|---|---|---|
| 训练进展 | [PNG](docs/assets/training_progress.png) | [PDF](docs/assets/training_progress.pdf) | [CSV](docs/assets/training_curve_source.csv) |
| Python候选架构 | [PNG](docs/assets/model_architecture_python.png) | [PDF](docs/assets/model_architecture_python.pdf) | [脚本](scripts/figures/render_public_figures.py) |
| GPT候选架构 | [PNG](docs/assets/model_architecture_gpt.png) | [PDF](docs/assets/model_architecture_gpt.pdf) | 视觉概念版，非拓扑权威 |

## 复现图件

```bash
python scripts/figures/render_public_figures.py
```

图件脚本只读取仓库内公开源数据，不下载数据、不调用GPU、不产生训练指标。

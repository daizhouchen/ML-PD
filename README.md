<p><img src="docs/assets/research-cover.svg" alt="ML-PD · 从探索性 Notebook 到可复现实验" width="100%"></p>

# ML-PD · 代谢组学分类研究工作流

[![Research workflow checks](https://github.com/daizhouchen/ML-PD/actions/workflows/ci.yml/badge.svg)](https://github.com/daizhouchen/ML-PD/actions/workflows/ci.yml)
![Python 3.12](https://img.shields.io/badge/Python-3.12-32635B)
[![License: MIT](https://img.shields.io/badge/License-MIT-B7793D)](LICENSE)

围绕健康对照、前驱期与帕金森病三组代谢组学数据，提供从输入校验到模型比较、结果追踪和交互展示的可复现实验流程。

> 原始合作数据未公开，新流程尚未在该数据上重新验证。公开图表来自固定种子的**合成数值数据**，用于验证程序流程，不代表真实代谢物、患者或临床效果；横断面分类不等于病程预测。

## 从这里开始

| 你想做什么 | 入口 |
|---|---|
| 先看项目和交互结果 | **[打开研究展示 →](https://daizhouchen.github.io/ML-PD/)** |
| 在本地跑一次实验 | [下面的快速开始](#五分钟开始) · [完整运行指南](guides/quickstart.md) · [Notebook](notebooks/01_reproduce.ipynb) |
| 理解实验是否可靠 | [方法与指标](guides/methodology.md) · [数据接入契约](guides/data-contract.md) |
| 阅读或修改代码 | [模块地图](guides/architecture.md) · [贡献指南](CONTRIBUTING.md) |
| 追溯早期实验 | [历史文件索引](archive/README.md) · [历史方法审查](guides/legacy-audit.md) |

## 当前流程

**4 个分类任务 × 7 个对照模型**：三分类及三组两两分类；类别先验基线、逻辑回归、线性 SVM、随机森林、决策树、GBM 与 XGBoost。

```mermaid
flowchart LR
    A[数据契约与校验] --> B[按受试者隔离外层测试]
    B --> C[内层重新学习预处理与 RFE]
    C --> D[内层选择模型参数]
    D --> E[外层评估与结果留痕]
```

输出包含各折指标、折间标准差、OOF 混淆矩阵、逐类 ROC、特征入选频率和数据/版本指纹。完整定义见[方法说明](guides/methodology.md)，产物位置见[运行指南](guides/quickstart.md#一次运行留下什么)。

## 五分钟开始

使用 Python 3.12，在仓库根目录执行：

```bash
git clone https://github.com/daizhouchen/ML-PD.git
cd ML-PD
python -m venv .venv
# macOS / Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .

mlpd demo --output data/demo --samples 180 --seed 2026
mlpd validate --data data/demo/synthetic.csv --schema data/demo/schema.json
mlpd run --data data/demo/synthetic.csv --schema data/demo/schema.json --output runs/quick --models dummy logistic --outer-folds 3 --inner-folds 2
```

这会用两个模型跑完四个任务，输出 `runs/quick/report.json` 和 SVG 图。再次运行请换一个输出目录。需要全部模型、私有数据、Notebook 或本地网页预览，继续看[完整运行指南](guides/quickstart.md)。

## 仓库布局

```text
ML-PD/
├── src/mlpd/          当前 Python 实现：数据 → 模型 → 评估 → 报告
├── tests/             数据边界、训练范围、受试者隔离与运行测试
├── configs/           数据 schema 示例
├── notebooks/         当前流程的交互复现入口
├── guides/            运行指南、实验方法、数据契约与模块地图
├── docs/              GitHub Pages 展示站点
│   ├── assets/        样式、交互脚本与视觉资源
│   └── results/       自动导出的合成聚合结果与图表
├── archive/           原始 Notebook 与旧素材，只用于追溯
├── .github/workflows/ 持续集成
├── pyproject.toml     包元数据、依赖范围与 CLI 入口
└── requirements-lock.txt  已验证的依赖版本
```

运行时产生的 `data/` 和 `runs/` 默认不纳入 Git。研究说明集中在 [guides/](guides/README.md)，网页维护说明在 [docs/](docs/README.md)，旧实验不作为新版运行入口。

## 开发与后续研究

```bash
python -m pytest -q
python -m build
```

下一阶段需要原始未泄漏数据重跑、批次与混杂因素敏感性分析、候选特征稳定性检验以及独立外部队列评估。参见[方法边界](guides/methodology.md#后续验证)和[变更记录](CHANGELOG.md)。

MIT · [戴宙辰的实验集](https://github.com/daizhouchen)

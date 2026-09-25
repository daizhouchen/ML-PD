# 运行指南

[文档目录](README.md) · [项目首页](../README.md) · [数据契约](data-contract.md)

下面的命令都从仓库根目录执行，默认使用合成数据。已有 `data/demo` 时可直接复用；`demo` 不覆盖已有文件，`run` 不接受非空输出目录。

## 安装环境

```bash
git clone https://github.com/daizhouchen/ML-PD.git
cd ML-PD
python -m venv .venv
# macOS / Linux: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-lock.txt
python -m pip install --no-deps -e .
mlpd --help
```

先确认 `python --version` 为 3.12。`requirements-lock.txt` 固定复现环境；`requirements.txt` 是它的便捷入口；`pyproject.toml` 定义包信息、支持的依赖范围和可选 Notebook 依赖。若未激活虚拟环境，使用其中的 Python 路径并把 `mlpd` 换成 `python -m mlpd`。

## 快速验证

```bash
mlpd demo --output data/demo --samples 180 --seed 2026
mlpd validate --data data/demo/synthetic.csv --schema data/demo/schema.json
mlpd run --data data/demo/synthetic.csv --schema data/demo/schema.json --output runs/quick --models dummy logistic --outer-folds 3 --inner-folds 2
```

最后一条运行四个任务、两个模型。再次运行时，将输出改成新的目录，例如 `runs/quick-02`，保留上次记录。

## 全部模型与常用选项

```bash
mlpd run --data data/demo/synthetic.csv --schema data/demo/schema.json --output runs/full --outer-folds 3 --inner-folds 3
```

| 参数 | 可选值或默认行为 |
|---|---|
| `--tasks` | `three-class`、`pd-control`、`prodromal-control`、`pd-prodromal`；默认全部 |
| `--models` | `dummy`、`logistic`、`svm`、`forest`、`tree`、`gbm`、`xgboost`；默认全部 |
| `--outer-folds` / `--inner-folds` | 默认 5 / 3；公开合成演示使用 3 / 3 |
| `--seed` | 默认 2026 |
| `--jobs` | 内层参数搜索并行度，默认 1 |

例如，只跑 PD–Control 对照：

```bash
mlpd run --data data/demo/synthetic.csv --schema data/demo/schema.json --output runs/pd-control --tasks pd-control --models dummy logistic --outer-folds 3 --inner-folds 2
```

正式研究应在看结果前，按独立受试者数确定折数和种子。详细参数可用 `mlpd run --help` 查询。

## 一次运行留下什么

```text
runs/<run-name>/
├── report.json             # 配置、环境、数据指纹、任务与模型结果
├── fold_metrics.csv        # 每个外层测试折的指标
├── feature_stability.csv   # 跨外折入选频率
├── split_assignments.csv   # 本地样本/受试者与外折归属，不应公开
└── figures/                # 带数据类型标注的 SVG 图
```

从 `report.json` 看完整记录，从 CSV 查各折数值，从 `figures/` 查看图表。折间 SD 不是置信区间，特征入选频率不等于生物标志物结论；具体解释见[指标说明](methodology.md#指标)。

## 本地展示与公开导出

只查看仓库已有的展示，不需要重新训练：

```bash
python -m http.server 8000 --directory docs
```

访问 `http://localhost:8000`，不要直接双击 HTML，因为浏览器需要通过 HTTP 读取结果 JSON。

完成上面的全部模型实验后，可更新展示结果：

```bash
mlpd publish-demo --report runs/full/report.json --output docs/results
```

此命令会更新 `docs/results/` 中的公开聚合产物；提交前检查差异。展示界面按四个任务设计，应使用包含全部任务的报告。导出仅接受带合成数据标记和合成特征名的报告，不复制样本级划分。网页文件与维护方式见[展示站点说明](../docs/README.md)。

## Notebook 入口

```bash
python -m pip install -e ".[notebook]"
jupyter lab notebooks/01_reproduce.ipynb
```

选择刚安装的虚拟环境作为 kernel，从上到下执行。[当前 Notebook](../notebooks/01_reproduce.ipynb) 调用相同 CLI，为每次运行创建带时间戳的目录。历史 Notebook 保存在 [archive/](../archive/README.md)，不参与当前复现。

## 接入真实数据

先读[数据契约](data-contract.md)，参照 [`configs/schema.example.json`](../configs/schema.example.json) 在 `data/private/schema.json` 中建立自己的配置，并将 `data_kind` 设为 `private`。保留原始缺失状态，显式列出特征和受试者标识。

```bash
mlpd validate --data data/private/cohort.csv --schema data/private/schema.json
mlpd run --data data/private/cohort.csv --schema data/private/schema.json --output runs/private-study
```

`data/` 和 `runs/` 被 Git 忽略。不要将真实输入或受试者划分复制到 `docs/results/`；真实研究结果需要单独审查披露内容。

## 常见运行问题

| 提示或现象 | 排查方式 |
|---|---|
| 找不到 `mlpd` | 确认已激活环境并完成可编辑安装；可改用该环境的 `python -m mlpd` |
| 输出目录已存在 | 使用新的实验目录，保留原运行记录 |
| 某类受试者数量不足 / 某折缺类 | 检查独立受试者数和预先指定的划分设计，不复制样本凑数 |
| 网页没有加载结果 | 通过 HTTP 服务访问，确认 `docs/results/demo-results.json` 存在 |

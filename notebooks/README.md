# 当前流程的 Notebook 入口

[返回项目首页](../README.md) · [完整运行指南](../guides/quickstart.md) · [历史实验归档](../archive/README.md)

[`01_reproduce.ipynb`](01_reproduce.ipynb) 是当前唯一的交互复现教程：生成合成数据，调用同一套 CLI 跑四个任务的基线与逻辑回归，再读取结果和图表。

先按[运行指南](../guides/quickstart.md#安装环境)安装 Python 3.12 环境，再在仓库根目录执行：

```bash
python -m pip install -e ".[notebook]"
jupyter lab notebooks/01_reproduce.ipynb
```

为 Notebook 选择该虚拟环境的 kernel，从上到下执行。输出写入带时间戳的 `data/notebook-*` 和 `runs/notebook-*` 目录，不写回源码。

新增教程应调用 `src/mlpd/` 的实现，避免复制训练逻辑；提交时清除执行输出，不把研究数据、受试者标识或旧实验输出带入当前教程。

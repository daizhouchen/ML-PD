# 开发与贡献

[项目首页](README.md) · [模块地图](guides/architecture.md) · [方法说明](guides/methodology.md)

## 开始修改

使用 Python 3.12，按[运行指南](guides/quickstart.md#安装环境)安装锁定依赖与可编辑包。当前实现放在 `src/mlpd/`，复现教程放在 `notebooks/`；历史文件保存在 `archive/`，不继续作为功能开发入口。

| 变更类型 | 同步内容 |
|---|---|
| 数据规则 | 数据契约、schema 示例与相关测试 |
| 预处理、划分、模型或评分 | 方法说明与能发现泄漏/口径错误的回归测试 |
| CLI 或产物格式 | 运行指南、Notebook 示例及消费该格式的报告/网页 |
| 网页内容或资源 | [站点说明](docs/README.md)中的交互、链接与布局检查 |
| 目录或命名 | README、文档内相对链接与网页的 GitHub 链接 |

## 验证

```bash
python -m pytest -q
python -m build
```

涉及实验实现时，再执行一次合成 CLI 实验，使用新的数据和结果目录，例如：

```bash
mlpd demo --output data/dev-check --samples 90
mlpd validate --data data/dev-check/synthetic.csv --schema data/dev-check/schema.json
mlpd run --data data/dev-check/synthetic.csv --schema data/dev-check/schema.json --output runs/dev-check --models dummy logistic --outer-folds 3 --inner-folds 2
```

持续集成入口是 [`.github/workflows/ci.yml`](.github/workflows/ci.yml)。仅文档或目录调整应检查链接与文件完整性；实验逻辑变化需验证实际运行。

## 研究记录

不要让测试数据进入拟合或参数选择，也不要依据更好看的分数改种子与划分。方法变更记录在 `guides/methodology.md` 和 `CHANGELOG.md`，不静默改写历史结果。

合作数据、受试者标识及本地 `runs/` 文件不能提交。公开展示必须说明数据性质；`docs/results/` 由合成报告生成，不手改指标或混入真实数据。新增公开研究数据需记录来源、许可及研究设计。

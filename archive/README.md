# 历史实验归档

[返回项目首页](../README.md) · [当前复现入口](../notebooks/README.md) · [历史方法审查](../guides/legacy-audit.md)

这里保留早期探索性实验的源码和原输出。整理时只移动和重命名文件，**8 份 Notebook 内容保持原样**；文件内部仍可能出现旧路径与历史依赖。

这些实验依赖未公开的合作数据，部分特征筛选与指标实现存在方法问题，因此不能直接作为新版复现入口或临床效果证据。新版计算逻辑在 [`src/mlpd/`](../src/mlpd/)，新旧分数不用于计算改善率。

## 目录

```text
archive/
├── notebooks/
│   ├── classification/     三分类与三组两两分类的模型实验
│   └── feature-selection/  三分类与三组两两分类的 RFE 实验
└── assets/hero.png         旧版展示素材，保留供溯源
```

## 原路径与现路径

| 原位置 | 当前归档位置 |
|---|---|
| `ML.ipynb` | [notebooks/classification/three-class.ipynb](notebooks/classification/three-class.ipynb) |
| `ML - 二分类/model-pd-control.ipynb` | [notebooks/classification/pd-control.ipynb](notebooks/classification/pd-control.ipynb) |
| `ML - 二分类/model-prodromal-control.ipynb` | [notebooks/classification/prodromal-control.ipynb](notebooks/classification/prodromal-control.ipynb) |
| `ML - 二分类/model-prodromal-pd.ipynb` | [notebooks/classification/prodromal-pd.ipynb](notebooks/classification/prodromal-pd.ipynb) |
| `RFE.ipynb` | [notebooks/feature-selection/three-class.ipynb](notebooks/feature-selection/three-class.ipynb) |
| `RFE - 二分类/RFE-control-prodromal.ipynb` | [notebooks/feature-selection/control-prodromal.ipynb](notebooks/feature-selection/control-prodromal.ipynb) |
| `RFE - 二分类/RFE-pd-control.ipynb` | [notebooks/feature-selection/pd-control.ipynb](notebooks/feature-selection/pd-control.ipynb) |
| `RFE - 二分类/RFE-pd-prodromal.ipynb` | [notebooks/feature-selection/pd-prodromal.ipynb](notebooks/feature-selection/pd-prodromal.ipynb) |

文件名保留原实验的组别顺序；例如旧 `prodromal-pd` 与当前 CLI 的 `pd-prodromal` 指向同一组两两比较，但不表示两者的标签编码或实验设计相同。当前任务定义以 [`data.py`](../src/mlpd/data.py) 为准。

历史审查以提交 [`20275fb`](https://github.com/daizhouchen/ML-PD/tree/20275fb9f5547c7004a183ccdbc80bb480c6ecde) 为基线。查某个文件的变更历史时，可用 `git log --follow -- archive/notebooks/classification/three-class.ipynb` 跟随重命名。

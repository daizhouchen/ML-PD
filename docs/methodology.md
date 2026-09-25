# ML-PD 方法说明

## 研究问题与边界

当前问题是区分 Control、Prodromal、PD 的横断面分类，不是诊断系统，也没有估计未来病程或发病时间。原始合作数据未公开，旧 Notebook 输出不能补足独立验证。新图表来自 make_classification 合成数值数据，特征名使用 synthetic_feature_*。

## 评估设计

1. 显式 schema 限定特征与标签，检查重复样本、无穷值、错误标签及受试者标签冲突。
2. 固定种子 2026；独立样本采用 StratifiedKFold，重复受试者采用 StratifiedGroupKFold。内外层均检查受试者无交叉、训练和测试包含所有类别。
3. 外层测试完全隔离。内层只使用相应外层训练集，以 balanced accuracy 选择超参数。
4. 每个内层训练折重新学习：去除缺失比例超过 40% 的列、常量列 → 中位数填补 → 标准化 → RFE → 模型。
5. 最佳流程在相应外层训练集重拟合，仅预测一次该外层测试折。
6. 每个样本恰好成为一次外层测试样本，保留配置、依赖版本、数据/schema SHA-256 和 Git 状态。

公开演示使用 3×3 嵌套 CV；CLI 研究默认 5×3，均为预先指定配置。不自动降折、丢弃失败折或用训练分数填补测试分数。

## 特征选择

RFE 以 class-weighted LogisticRegression 为共同排序器，每步移除 25% 特征；内层比较保留 50% 与全部特征。特征数量与模型参数在完整 Pipeline 中一起选择。

这不是“发现了最优代谢物子集”：线性排序可能漏掉非线性交互；相关特征可互相替代；入选频率依赖数据和搜索空间。稳定性只表示外折重拟合的选择一致性，不等于生物学有效性、因果作用或临床标志物。

| 模型 | 固定设置 | 内层搜索 |
|---|---|---|
| Dummy | 训练集类别先验 | 无 |
| Logistic | balanced class weight，max_iter=2500 | C∈{0.1,1} |
| Linear SVM | linear kernel，balanced class weight | C∈{0.1,1} |
| Random forest | 100 trees，balanced class weight | min_samples_leaf∈{2,5} |
| Decision tree | balanced class weight | max_depth∈{2,4} |
| GBM | 80 trees，max_depth=2 | learning_rate∈{0.03,0.1} |
| XGBoost | 80 trees，max_depth=2，learning_rate=0.05，subsample/colsample=0.9 | reg_lambda∈{1,5} |

非 Dummy 模型还搜索 RFE 保留比例。小型搜索空间便于审查和复现，并非全面调优。模型共用外层划分，差异仅作描述性对照。

## 指标

- Balanced accuracy：各类召回率平均，预先指定的主要指标。
- Macro F1：各类 F1 等权平均；accuracy 仅作补充。
- Macro OVR AUC：各类 one-vs-rest AUC 平均；二分类平均两个方向。
- 均值和 SD 来自外折。SD 不是置信区间，折间训练数据重叠，不能将折分数当独立样本作简单显著性检验。
- 混淆矩阵行是真实标签、列是预测标签，汇总 OOF 预测。
- ROC 对每折 TPR 插值后平均，不把不同折 SVM margin 当已校准概率汇总。
- 重复受试者的划分相互隔离，但指标为样本加权，不自动等同受试者级性能。

## 后续验证

批次/站点效应、年龄性别混杂、代谢物质控、批间校正和缺失机制需要真实数据与研究协议。当前不擅自做全队列归一化、SMOTE 或批次校正。已全局填补的数据必须回到未处理版本，新 Pipeline 不能修复之前的泄漏。

参考：[数据泄漏](https://scikit-learn.org/stable/common_pitfalls.html)、[nested CV](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html)、[StratifiedGroupKFold](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html)。

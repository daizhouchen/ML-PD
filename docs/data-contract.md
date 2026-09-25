# 数据接入契约

输入为 UTF-8 CSV 与 JSON schema。示例为 [`configs/schema.example.json`](../configs/schema.example.json)。只有 feature_columns 显式列出的数值列进入模型，不再依赖列位置。

| 字段 | 要求 |
|---|---|
| sample_id_column | 每行唯一、非空 |
| subject_id_column | 真实受试者标识；同人多样本共享此值，不能用 sample ID 冒充受试者 ID |
| label_column | 通过 label_mapping 映射为 Control、Prodromal、PD |
| feature_columns | 至少两列；唯一名称、数值或空值；不得包含标签或标识符 |
| data_kind | private / public / synthetic；合作数据设为 private |

拒绝重复列、重复样本 ID、完全重复特征行、未知标签、无限值、全缺失样本、同受试者冲突标签。重复行应先调查，不得改 ID 绕过。同人不同随访标签需另行设计纵向验证。

## 预处理与划分

保留原始缺失状态，不把 0 自动视为缺失。检测下限与临床混杂变量由研究协议定义。不得先在全队列填补、标准化或筛特征。全缺失/常量列由各训练折自行判断，过滤后不足两列或折中缺类即中止，不静默填造数据或跳过折。

## 公开边界

data/、runs/、CSV、Parquet、Excel、序列化模型均默认 Git 忽略。split_assignments.csv 含本地样本和受试者 ID，不能公开。

publish-demo 只接受标注 synthetic 且使用 synthetic_feature_* 名称的报告，只导出聚合 JSON 和图，不复制样本级划分。这是防误操作校验，不是脱敏系统；不能把真实数据改标签后公开。真实研究结果需单独披露审阅。

# 历史实验审查

审查基线：20275fb。历史文件保留供溯源，新版入口为 mlpd CLI。新旧流程不同，分数不能直接用来计算改善率。

| 发现 | 源码证据 | 新版处理 |
|---|---|---|
| 全量筛选先于测试划分 | RFE.ipynb 的 RFECV.fit(X,y) 在 train_test_split(U,y) 前 | 全部预处理与 RFE 进入内层训练 Pipeline |
| precision/recall 语义颠倒 | 主 Notebook 手工函数对行和、列和的解释颠倒 | sklearn classification_report；行真实、列预测 |
| 划分未固定、未分层 | train_test_split 没有 random_state/stratify | 固定种子、分层、受试者隔离 |
| 特征名称可能错位 | RFE 后继续按原 feat_labels 索引重要性 | 追踪过滤与 RFE support 掩码 |
| 输入无法独立复现 | CSV 未公开，文件名显示预填补版本 | 显式 schema、指纹、合成运行 |
| 文案强于代码证据 | 声称完整预处理、病程预测 | 明确横断面范围、真实重跑未完成 |
| 环境未锁定 | 旧 Notebook 依赖历史接口 | 锁定 Python 3.12 环境，测试与 CI |

历史输出只证明当时执行过步骤，不能证明无泄漏或具有独立泛化性能。新版尚未使用原始合作数据验证，因此没有可以宣称的真实准确率提升。

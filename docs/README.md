# 交互研究展示

[在线访问](https://daizhouchen.github.io/ML-PD/) · [项目首页](../README.md) · [研究文档](../guides/README.md)

这个目录是 GitHub Pages 的发布根目录，展示静态聚合结果。它不需要 Node.js 构建或后端服务。

| 位置 | 用途 | 如何修改 |
|---|---|---|
| [`index.html`](index.html) | 页面内容、结构、导航与文档入口 | 手动编辑 |
| [`assets/site.css`](assets/site.css) | 配色、排版与响应式布局 | 手动编辑 |
| [`assets/site.js`](assets/site.js) | 读取结果，切换任务、模型与指标，绘制图表 | 手动编辑 |
| `assets/` 内 SVG | 图标与 README 封面 | 按用途维护 |
| [`results/demo-results.json`](results/demo-results.json) | 合成演示的聚合报告 | 使用 `mlpd publish-demo` 生成 |
| `results/figures/` | 可下载的 SVG 图表 | 与同一次报告一起生成 |
| `.nojekyll` | 直接发布静态文件 | 保留 |

## 本地预览

从仓库根目录执行，然后访问 `http://localhost:8000`：

```bash
python -m http.server 8000 --directory docs
```

更新公开结果的命令与要求见[运行指南](../guides/quickstart.md#本地展示与公开导出)。不要手动修改生成的指标；报告和图表应来自同一次运行。结果保存了生成时的代码版本，网页或文档后续改动不会改写该记录。

页面源码保留展开后的缩进，便于阅读和审查。若本地装有 Node.js，可在仓库根目录用同一版本的格式化工具整理这三个文件（仅维护时使用，不影响运行）：

```bash
npx --yes prettier@3.6.2 --no-config --single-quote --trailing-comma es5 --print-width 100 --write docs/index.html docs/assets/site.css docs/assets/site.js
```

## 发布与检查

当前 GitHub Pages 使用 `main` 分支的 `/docs`。推送后，在仓库 Actions 中查看 Pages 构建状态。

更新后检查：四个任务、七个模型与指标切换；图表和 JSON 下载；研究文档入口；窄屏布局与键盘焦点。浏览器控制台不应出现脚本错误或资源 404。

研究方法和开发说明统一放在 `guides/`；旧 Notebook 放在 `archive/`，避免混入网站入口。本站展示的是合成流程演示，相关标注应与结果一起保留。

(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const COLORS = ['#32635B', '#B7793D', '#8C514E', '#7D8A75', '#585B69', '#B1A183', '#8DABA3'];
  const metricNames = {
    balanced_accuracy: 'Balanced accuracy',
    macro_f1: 'Macro F1',
    macro_ovr_auc: 'Macro OVR AUC',
    accuracy: 'Accuracy',
  };
  const esc = (value) =>
    String(value).replace(
      /[&<>"']/g,
      (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]
    );
  const pct = (value) => (value * 100).toFixed(1) + '%';
  const point = (x, y) => `${x.toFixed(2)},${y.toFixed(2)}`;
  let report,
    taskId = 'three-class',
    modelId = 'logistic',
    metric = 'balanced_accuracy';
  const svg = (title, body, width, height) =>
    `<svg class="chart-svg" viewBox="0 0 ${width} ${height}" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title>${body}</svg>`;

  function comparison(task) {
    const narrow = window.innerWidth < 650;
    const width = narrow ? 360 : 830,
      left = narrow ? 128 : 185,
      right = narrow ? 314 : 750,
      top = 30,
      row = 36,
      height = task.models.length * row + 65;
    const x = (value) => left + value * (right - left);
    let body = '';
    for (let n = 0; n <= (narrow ? 2 : 5); n++) {
      const value = n / (narrow ? 2 : 5);
      body += `<path class="grid" d="M${x(value)} 12V${height - 33}"/><text class="small" x="${x(value)}" y="${height - 12}" text-anchor="middle">${Math.round(value * 100)}%</text>`;
    }
    task.models.forEach((model, index) => {
      const y = top + index * row,
        stats = model.summary[metric],
        color = COLORS[index % COLORS.length];
      body += `<text x="${left - 16}" y="${y + 4}" text-anchor="end">${esc(model.name)}</text><path d="M${x(Math.max(0, stats.mean - stats.std))} ${y}H${x(Math.min(1, stats.mean + stats.std))}" stroke="${color}" stroke-width="2"/>`;
      model.folds.forEach(
        (f) =>
          (body += `<circle cx="${x(f[metric])}" cy="${y}" r="4" fill="${color}" opacity=".45"><title>Fold ${f.fold}: ${pct(f[metric])}</title></circle>`)
      );
      body += `<path d="M${x(stats.mean)} ${y - 6}l6 6-6 6-6-6Z" fill="${color}"/><text class="small" x="${right + 16}" y="${y + 4}">${pct(stats.mean)}</text>`;
    });
    $('comparison-chart').innerHTML = svg(
      `${metricNames[metric]}：各模型外折均值和标准差。合成演示。`,
      body,
      width,
      height
    );
    $('metric-caption').textContent = metricNames[metric] + ' · 外折均值与标准差，合成数据';
    $('metric-table').innerHTML = task.models
      .map(
        (m) =>
          `<tr><th scope="row">${esc(m.name)}</th><td>${pct(m.summary[metric].mean)}</td><td>${pct(m.summary[metric].std)}</td></tr>`
      )
      .join('');
  }

  function roc(model) {
    const left = 49,
      right = 404,
      top = 18,
      bottom = 266;
    let body = '';
    for (let i = 0; i <= 5; i++) {
      const f = i / 5,
        x = left + f * (right - left),
        y = bottom - f * (bottom - top);
      body += `<path class="grid" d="M${x} ${top}V${bottom}M${left} ${y}H${right}"/><text class="small" x="${x}" y="${bottom + 18}" text-anchor="middle">${f.toFixed(1)}</text><text class="small" x="${left - 10}" y="${y + 3}" text-anchor="end">${f.toFixed(1)}</text>`;
    }
    body += `<path d="M${left} ${bottom}L${right} ${top}" stroke="#A3B4A0" stroke-dasharray="5 5"/>`;
    model.roc.forEach((curve, i) => {
      body += `<polyline fill="none" stroke="${COLORS[i]}" stroke-width="2.4" points="${curve.fpr.map((f, j) => point(left + f * (right - left), bottom - curve.mean_tpr[j] * (bottom - top))).join(' ')}"/><rect x="${left + i * 122}" y="316" width="14" height="3" fill="${COLORS[i]}"/><text class="small" x="${left + 20 + i * 122}" y="321">${esc(curve.class)}</text>`;
    });
    body += `<text class="small" x="226" y="304" text-anchor="middle">False positive rate</text><text class="small" transform="translate(13 150) rotate(-90)" text-anchor="middle">Mean true positive rate</text>`;
    $('roc-chart').innerHTML = svg(`${model.name} 平均逐类 ROC，合成演示`, body, 440, 341);
  }

  function confusion(task, model) {
    const max = Math.max(...model.confusion_matrix.flat(), 1);
    $('confusion-chart').innerHTML =
      `<table><caption>真实标签 ↓ / 预测标签 →</caption><thead><tr><th scope="col">真实 / 预测</th>${task.classes.map((c) => `<th scope="col">${esc(c)}</th>`).join('')}</tr></thead><tbody>${model.confusion_matrix.map((row, i) => `<tr><th scope="row" class="row-label">${esc(task.classes[i])}</th>${row.map((value) => `<td style="background:rgba(50,99,91,${(0.06 + (0.9 * value) / max).toFixed(3)});color:${value / max > 0.6 ? '#fff' : '#234C43'}">${value}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  }

  function render() {
    const task = report.tasks.find((t) => t.id === taskId);
    if (!task.models.some((m) => m.id === modelId)) modelId = task.models[0].id;
    const model = task.models.find((m) => m.id === modelId);
    document
      .querySelectorAll('[data-task]')
      .forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.task === taskId)));
    $('run-meta').textContent =
      `合成样本 ${task.samples} · 数值特征 ${task.features} · ${report.config.outer_folds} 外折 × ${report.config.inner_folds} 内折 · Seed ${report.config.seed} · 缺失比例 ${pct(task.missing_fraction)}`;
    $('model-select').innerHTML = task.models
      .map((m) => `<option value="${esc(m.id)}">${esc(m.name)}</option>`)
      .join('');
    $('model-select').value = modelId;
    comparison(task);
    roc(model);
    confusion(task, model);
    $('feature-chart').innerHTML = model.feature_stability.length
      ? model.feature_stability
          .slice(0, 8)
          .map(
            (f) =>
              `<div class="feature-row"><span>${esc(f.feature.replace('synthetic_feature_', 'Synthetic feature '))}</span><span class="feature-track"><i class="feature-fill" style="width:${f.frequency * 100}%"></i></span><span>${f.selected_folds}/${report.config.outer_folds}</span></div>`
          )
          .join('') + '<p class="chart-note">按入选频率列前 8 项；完整记录见结果 JSON。</p>'
      : '<p class="chart-note">先验基线不选择或使用代谢特征，因此没有特征稳定性排名。</p>';
    $('figure-link').href = `results/figures/${taskId}-comparison.svg`;
    $('fingerprint').textContent = `DATA SHA-256 / ${report.data_sha256.slice(0, 16)}…`;
  }

  document.querySelectorAll('[data-task]').forEach((b) =>
    b.addEventListener('click', () => {
      taskId = b.dataset.task;
      render();
    })
  );
  $('metric-select').addEventListener('change', (e) => {
    metric = e.target.value;
    render();
  });
  $('model-select').addEventListener('change', (e) => {
    modelId = e.target.value;
    render();
  });
  let resizeFrame;
  window.addEventListener('resize', () => {
    cancelAnimationFrame(resizeFrame);
    resizeFrame = requestAnimationFrame(() => {
      if (report) render();
    });
  });
  $('copy-command').addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText($('run-command').textContent);
      $('copy-status').textContent = '已复制。请在安装环境后运行。';
    } catch {
      $('copy-status').textContent = '浏览器未允许复制，请直接选中上方命令。';
    }
  });
  fetch('results/demo-results.json')
    .then((r) => {
      if (!r.ok) throw new Error('load');
      return r.json();
    })
    .then((data) => {
      if (data.data_kind !== 'synthetic' || !Array.isArray(data.tasks) || !data.tasks.length)
        throw new Error('format');
      report = data;
      render();
      $('load-status').textContent = '';
      $('explorer').hidden = false;
    })
    .catch(() => {
      $('load-status').textContent =
        '暂时无法读取演示结果。请刷新重试，或从 GitHub 查看结果文件与独立图表。';
    });
})();

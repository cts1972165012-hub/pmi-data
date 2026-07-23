# 全球制造业PMI · 机械出口市场风向标

> 基于 J.P.Morgan / S&P Global 全球制造业 PMI 官方报告的**每月自动更新**数据看板，为机械出口商家指明哪些市场旺盛、哪些市场收缩。

## 🌐 在线访问

部署在 GitHub Pages，地址形如：
```
https://cts1972165012-hub.github.io/pmi-data/
```
（首次部署需在仓库 Settings → Pages 中开启，详见 `SETUP_GUIDE.md`）

## 📁 项目结构

```
pmi-data/
├── index.html                    # 最终看板（由脚本构建，勿手动编辑）
├── data/
│   ├── data.json                 # ★ 核心数据文件（每月更新这里）
│   ├── latest_report.json        # 最新报告下载元数据（自动生成）
│   └── reports/                  # 每月报告第2页柱状图图片（自动生成）
├── scripts/
│   ├── template.html             # HTML模板（含占位符）
│   ├── build_html.py             # 构建脚本：data.json + template → index.html
│   ├── fetch_report.py           # 下载最新报告PDF并提取柱状图图片
│   └── update_data.py            # 数据录入脚本（交互式/批量）
├── vendor/
│   └── chart.umd.min.js          # Chart.js（内联用，保证离线可用）
├── .github/workflows/
│   └── monthly-update.yml        # 每月5号自动下载报告的GitHub Action
├── SETUP_GUIDE.md                # ★ 完整配置指南
└── README.md
```

## 🔄 每月更新流程

1. **自动**：每月5号，GitHub Action 自动下载最新报告、提取柱状图图片、创建Issue提醒
2. **录入**：运行 `python3 scripts/update_data.py`（或把图片+data.json交给AI agent读取录入）
3. **构建**：脚本自动重新构建 `index.html`
4. **推送**：`git push` 后 GitHub Pages 自动更新网站

## 🛠️ 本地命令

```bash
# 重新构建看板
python3 scripts/build_html.py

# 交互式录入新月份数据
python3 scripts/update_data.py

# 从JSON文件批量导入新月份数据
python3 scripts/update_data.py --from new_month.json

# 手动下载最新报告（通常由Action自动执行）
python3 scripts/fetch_report.py
```

## 📊 数据说明

- 各国PMI数值读取自各期官方报告第2页"国家排行"柱状图，精度约±0.2
- 全球综合PMI（WORLD）与产出PMI取自报告正文，为精确值
- 个别经济体因发布延迟未纳入当月全球计算，构建时按**前后两月均值**插补并以≈标注
- PMI > 50 代表扩张，< 50 代表收缩

## ⚠️ 免责声明

本报告仅供商业决策参考，不构成投资建议。数据以 J.P.Morgan / S&P Global 官方发布为准。

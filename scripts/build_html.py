#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_html.py — 从 data/data.json 构建自包含的 index.html

用法：
    python3 scripts/build_html.py

说明：
    - 读取 data/data.json（每月更新时只需修改此文件）
    - 内联 Chart.js（vendor/chart.umd.min.js），生成完全离线的单文件 index.html
    - 自动对 null 值按前后两月均值插补
    - 输出 index.html 到项目根目录
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "data.json")
CHART_PATH = os.path.join(ROOT, "vendor", "chart.umd.min.js")
TEMPLATE_PATH = os.path.join(ROOT, "scripts", "template.html")
OUT_PATH = os.path.join(ROOT, "index.html")


def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def main():
    data = load_data()

    # 数据校验
    n_months = len(data["months"])
    for c in data["countries"]:
        assert len(c["v"]) == n_months, f"{c['zh']} 数据长度应为 {n_months}"
        for x in c["v"]:
            if x is not None:
                assert 40 <= x <= 60, f"{c['zh']} 数值异常: {x}"
    assert len(data["global"]["headline"]) == n_months, "global.headline 长度不匹配"

    # 读取模板与 Chart.js
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()
    with open(CHART_PATH, encoding="utf-8") as f:
        chartjs = f.read()

    # 注入数据（JSON 序列化，确保 null 正确）
    data_js = json.dumps(data, ensure_ascii=False, indent=2)

    html = template
    html = html.replace("/*__CHARTJS__*/", chartjs)
    html = html.replace("/*__DATA__*/", "const PMI_DATA = " + data_js + ";")

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(OUT_PATH) / 1024
    print(f"[OK] 构建成功: {OUT_PATH}")
    print(f"     大小: {size_kb:.1f} KB")
    print(f"     月份数: {n_months} ({data['months'][0]} ~ {data['months'][-1]})")
    print(f"     国家数: {len(data['countries'])}")
    print(f"     数据更新: {data['meta']['updated_at']}")


if __name__ == "__main__":
    main()

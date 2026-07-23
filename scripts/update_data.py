#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
update_data.py — 向 data/data.json 追加一个新月份的PMI数据

用法：
    python3 scripts/update_data.py                  # 交互式录入
    python3 scripts/update_data.py --from new.json  # 从JSON文件批量导入

交互式模式会逐国提示录入，直接回车表示该月未发布（记为null，构建时自动插补）。
录入完成后自动调用 build_html.py 重新构建 index.html。
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(ROOT, "data", "data.json")


def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[OK] 数据已保存: {DATA_PATH}")


def parse_value(s):
    """解析输入值，空串返回None，非法输入返回'INVALID'"""
    s = s.strip()
    if s == "":
        return None
    try:
        v = float(s)
        if 40 <= v <= 60:
            return v
        return "INVALID"
    except ValueError:
        return "INVALID"


def interactive_entry(data):
    """交互式录入新月份"""
    n = len(data["months"])
    new_month = input(f"当前已有 {n} 个月（{data['months'][0]}~{data['months'][-1]}）。\n"
                      f"请输入新月份标签（如 '7月'）: ").strip()
    if not new_month:
        print("未输入月份，退出。")
        return False

    if new_month in data["months"]:
        print(f"⚠️  月份 {new_month} 已存在！")
        confirm = input("仍要继续追加吗？(y/N): ").strip().lower()
        if confirm != "y":
            return False

    print("\n=== 录入各国PMI（直接回车=该月未发布，将自动插补）===\n")
    for c in data["countries"]:
        while True:
            s = input(f"{c['zh']} ({c['en']}): ")
            v = parse_value(s)
            if v == "INVALID":
                print("  ⚠️  请输入 40~60 之间的数字，或直接回车跳过")
                continue
            c["v"].append(v)
            if v is None:
                print("  → 记为未发布(null)")
            break

    print("\n=== 录入全球指标 ===")
    while True:
        s = input("全球制造业PMI (headline): ")
        v = parse_value(s)
        if v == "INVALID":
            print("  ⚠️  请输入 40~60 之间的数字")
            continue
        data["global"]["headline"].append(v if v is not None else data["global"]["headline"][-1])
        break

    while True:
        s = input("全球产出PMI (output): ")
        v = parse_value(s)
        if v == "INVALID":
            print("  ⚠️  请输入 40~60 之间的数字")
            continue
        data["global"]["output"].append(v if v is not None else data["global"]["output"][-1])
        break

    note = input("本月要点备注（可回车跳过）: ").strip()
    data["global"]["month_notes"].append(note or "—")

    # 添加月份标签
    data["months"].append(new_month)

    # 添加来源
    src_url = input("报告URL（可回车跳过）: ").strip()
    if src_url:
        data["sources"].append({
            "m": f"{new_month}报告",
            "d": f"覆盖 {new_month}数据",
            "url": src_url
        })

    # 更新元数据
    from datetime import date
    data["meta"]["updated_at"] = date.today().isoformat()
    data["meta"]["data_range"] = f"{data['months'][0]}—{data['months'][-1]}"

    return True


def from_file(data, path):
    """从JSON文件批量导入。格式: {"month":"7月","headline":52.0,"output":52.8,
       "note":"...","source_url":"...","countries":{"印度":54.5,"日本":54.8,...}}"""
    with open(path, encoding="utf-8") as f:
        new = json.load(f)

    month = new["month"]
    if month in data["months"]:
        print(f"⚠️  月份 {month} 已存在，退出。")
        return False

    # 国家数据
    country_map = {c["zh"]: c for c in data["countries"]}
    country_map_en = {c["en"]: c for c in data["countries"]}
    for name, val in new.get("countries", {}).items():
        c = country_map.get(name) or country_map_en.get(name)
        if c is None:
            print(f"  ⚠️  未知国家: {name}，跳过")
            continue
        c["v"].append(val)

    # 未提供的国家补null
    for c in data["countries"]:
        if len(c["v"]) < len(data["months"]) + 1:
            c["v"].append(None)

    data["global"]["headline"].append(new["headline"])
    data["global"]["output"].append(new["output"])
    data["global"]["month_notes"].append(new.get("note", "—"))
    data["months"].append(month)

    if new.get("source_url"):
        data["sources"].append({
            "m": f"{month}报告",
            "d": f"覆盖 {month}数据",
            "url": new["source_url"]
        })

    from datetime import date
    data["meta"]["updated_at"] = date.today().isoformat()
    data["meta"]["data_range"] = f"{data['months'][0]}—{data['months'][-1]}"
    return True


def main():
    data = load_data()

    if "--from" in sys.argv:
        idx = sys.argv.index("--from")
        path = sys.argv[idx + 1]
        ok = from_file(data, path)
    else:
        ok = interactive_entry(data)

    if not ok:
        sys.exit(1)

    save_data(data)

    # 自动重新构建
    print("\n=== 重新构建 index.html ===")
    build_script = os.path.join(ROOT, "scripts", "build_html.py")
    subprocess.run([sys.executable, build_script], check=True)

    print("\n✅ 全部完成！接下来：")
    print("   git add data/data.json index.html")
    print("   git commit -m 'data: 更新 " + data["months"][-1] + " PMI数据'")
    print("   git push  # GitHub Pages 将自动更新")


if __name__ == "__main__":
    main()

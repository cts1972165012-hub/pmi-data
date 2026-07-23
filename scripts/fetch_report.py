#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_report.py — 从 pmi.spglobal.com 下载最新一期 J.P.Morgan Global Manufacturing PMI 报告
并提取第2页（国家排行柱状图）为图片。

在 GitHub Actions 中运行，需要 poppler-utils (pdftoppm) 和 requests。
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta

try:
    import requests
except ImportError:
    print("请先安装 requests: pip install requests")
    sys.exit(1)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
REPORTS_DIR = os.path.join(DATA_DIR, "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

# 已知的报告URL列表页面
RELEASES_URL = "https://www.pmi.spglobal.com/Public/Release/PressReleases"


def find_latest_report_url():
    """尝试从 releases 页面找到最新的 Manufacturing PMI 报告链接"""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PMI-Bot/1.0)"}

    # 方法1: 直接尝试已知的URL模式（每月报告URL是固定的hash）
    # 从 data.json 中获取最后一个已知URL，然后尝试访问 releases 页面
    data_path = os.path.join(DATA_DIR, "data.json")
    if os.path.exists(data_path):
        with open(data_path, encoding="utf-8") as f:
            data = json.load(f)
        known_urls = [s["url"] for s in data.get("sources", [])]
    else:
        known_urls = []

    # 方法2: 访问 releases 列表页
    try:
        resp = requests.get(RELEASES_URL, headers=headers, timeout=30)
        resp.raise_for_status()
        # 查找所有 Manufacturing PMI 相关链接
        pattern = r'href="(/Public/Home/PressRelease/[a-f0-9]+)"[^>]*>[^<]*Manufacturing PMI'
        matches = re.findall(pattern, resp.text, re.IGNORECASE)
        if matches:
            # 返回第一个（最新的）
            url = "https://www.pmi.spglobal.com" + matches[0]
            if url not in known_urls:
                return url
            print(f"最新报告已在数据中: {url}")
    except Exception as e:
        print(f"访问 releases 页面失败: {e}")

    # 方法3: 尝试通过搜索API
    try:
        search_url = "https://www.pmi.spglobal.com/Public/Home/PressRelease"
        resp = requests.get(search_url, headers=headers, timeout=30,
                            params={"q": "J.P.Morgan Global Manufacturing PMI"})
        if resp.status_code == 200:
            pattern = r'href="(/Public/Home/PressRelease/[a-f0-9]+)"'
            matches = re.findall(pattern, resp.text)
            for m in matches:
                url = "https://www.pmi.spglobal.com" + m
                if url not in known_urls:
                    return url
    except Exception as e:
        print(f"搜索失败: {e}")

    return None


def download_pdf(url):
    """下载报告PDF"""
    headers = {"User-Agent": "Mozilla/5.0 (compatible; PMI-Bot/1.0)"}
    print(f"下载报告: {url}")
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()

    # 保存到临时文件
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(resp.content)
    tmp.close()
    print(f"PDF 已下载: {tmp.name} ({len(resp.content)} bytes)")
    return tmp.name


def extract_page2_image(pdf_path, output_prefix):
    """用 pdftoppm 提取第2页为JPEG图片"""
    output = os.path.join(REPORTS_DIR, output_prefix)
    cmd = [
        "pdftoppm", "-jpeg", "-r", "250",
        "-f", "2", "-l", "2",
        pdf_path, output
    ]
    subprocess.run(cmd, check=True)
    # pdftoppm 输出文件名: output-2.jpg
    img_path = f"{output}-2.jpg"
    if os.path.exists(img_path):
        print(f"图片已生成: {img_path}")
        return img_path
    # 尝试其他命名
    for f in os.listdir(REPORTS_DIR):
        if f.startswith(output_prefix) and f.endswith(".jpg"):
            return os.path.join(REPORTS_DIR, f)
    raise FileNotFoundError(f"未找到生成的图片: {output}*")


def detect_data_month(pdf_path):
    """从PDF文本中检测数据月份"""
    try:
        result = subprocess.run(
            ["pdftotext", "-l", "1", pdf_path, "-"],
            capture_output=True, text=True, timeout=30
        )
        text = result.stdout
        # 匹配 "January 2026", "February 2026" 等
        match = re.search(
            r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})',
            text
        )
        if match:
            month_map = {
                'January': '1月', 'February': '2月', 'March': '3月',
                'April': '4月', 'May': '5月', 'June': '6月',
                'July': '7月', 'August': '8月', 'September': '9月',
                'October': '10月', 'November': '11月', 'December': '12月'
            }
            return f"{match.group(2)}年{month_map[match.group(1)]}"
    except Exception as e:
        print(f"检测月份失败: {e}")

    # 回退：用当前日期推算（报告通常月初发布上月数据）
    now = datetime.utcnow()
    prev = now.replace(day=1) - timedelta(days=1)
    return f"{prev.year}年{prev.month}月"


def main():
    print("=" * 60)
    print("J.P.Morgan Global Manufacturing PMI — 报告下载器")
    print("=" * 60)

    # 1. 查找最新报告
    url = find_latest_report_url()
    if not url:
        print("\n⚠️  未找到新的报告。可能本月报告尚未发布，或URL模式已变化。")
        print("请手动访问 https://www.pmi.spglobal.com/Public/Release/PressReleases 查找。")
        # 写入状态文件
        with open(os.path.join(DATA_DIR, "latest_report.json"), "w") as f:
            json.dump({"status": "no_new_report", "checked_at": datetime.utcnow().isoformat()}, f)
        return

    # 2. 下载PDF
    pdf_path = download_pdf(url)

    # 3. 检测数据月份
    data_month = detect_data_month(pdf_path)
    print(f"数据月份: {data_month}")

    # 4. 提取第2页图片
    safe_month = data_month.replace("年", "-").replace("月", "")
    img_path = extract_page2_image(pdf_path, f"pmi_{safe_month}")

    # 5. 保存元数据
    meta = {
        "status": "downloaded",
        "data_month": data_month,
        "report_url": url,
        "image_path": os.path.relpath(img_path, ROOT),
        "downloaded_at": datetime.utcnow().isoformat()
    }
    meta_path = os.path.join(DATA_DIR, "latest_report.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 完成！")
    print(f"   数据月份: {data_month}")
    print(f"   报告URL: {url}")
    print(f"   图片路径: {img_path}")
    print(f"   元数据: {meta_path}")

    # 清理临时PDF
    os.unlink(pdf_path)


if __name__ == "__main__":
    main()

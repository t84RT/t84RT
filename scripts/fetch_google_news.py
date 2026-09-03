#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google News 多专题新闻聚合器（增强版）
- 支持多个商业/科技相关专题
- 每个源可独立配置最大条数（默认 30）
- 提取标题、链接、摘要、发布时间
- 保存为带日期的 Markdown 文件到 data/ 目录
"""

import feedparser
import requests
import datetime
import os
import sys
from typing import List, Dict

# ---------- 配置 ----------
DATA_DIR = "googlenew"                     # 存储目录
MAX_PER_SOURCE = 30                   # 每个源最多抓取条数（可调）
TIMEOUT = 15                          # 请求超时
# 自定义请求头，模拟真实浏览器
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# ---------- 新闻源定义（可根据需要增删） ----------
# 商业/科技/金融等专题 RSS 地址
NEWS_SOURCES = {
    "Business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "Technology": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
    "Finance": "https://news.google.com/rss/headlines/section/topic/FINANCE?hl=en-US&gl=US&ceid=US:en",
    "Markets": "https://news.google.com/rss/headlines/section/topic/MARKETS?hl=en-US&gl=US&ceid=US:en",
    # 如果还有其它专题，可追加：
    # "Startups": "https://news.google.com/rss/headlines/section/topic/STARTUPS?hl=en-US&gl=US&ceid=US:en",
    # "Economy": "https://news.google.com/rss/headlines/section/topic/ECONOMY?hl=en-US&gl=US&ceid=US:en",
}

# ---------- 工具函数 ----------
def fetch_feed(url: str, source_name: str, max_items: int) -> List[Dict]:
    """抓取单个 RSS 源，返回新闻条目列表（包含标题、链接、摘要、发布时间）"""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        print(f"⚠️  [{source_name}] 网络请求失败: {e}")
        return []

    feed = feedparser.parse(resp.text)
    if not feed.entries:
        print(f"⚠️  [{source_name}] 解析到 0 条条目（可能返回非 RSS 内容）")
        return []

    entries = []
    for entry in feed.entries[:max_items]:
        # 提取摘要（可能有 HTML 标签，我们保留纯文本）
        summary = entry.get("summary", "").strip()
        # 移除 HTML 标签（简单清理）
        if summary:
            import re
            summary = re.sub(r"<[^>]+>", "", summary)  # 粗略去除标签
        entries.append({
            "title": entry.title,
            "link": entry.link,
            "published": entry.get("published", ""),
            "summary": summary,
        })
    print(f"✅ [{source_name}] 抓取到 {len(entries)} 条新闻")
    return entries

def generate_report(sources_data: Dict[str, List[Dict]], date_str: str) -> str:
    """生成 Markdown 报告内容，包含摘要和发布时间"""
    lines = [f"# 📰 Google News 综合热榜（{date_str}）\n"]
    lines.append(f"**共抓取 {sum(len(v) for v in sources_data.values())} 条新闻**\n")
    for source_name, entries in sources_data.items():
        if not entries:
            lines.append(f"\n## {source_name}\n> 暂无数据\n")
            continue
        lines.append(f"\n## {source_name} （{len(entries)} 条）\n")
        for idx, item in enumerate(entries, 1):
            title = item["title"]
            link = item["link"]
            pub = item["published"]
            summary = item["summary"]
            # 截断过长的摘要（保留前 150 字符）
            if summary and len(summary) > 150:
                summary = summary[:150] + "..."
            lines.append(f"### {idx}. [{title}]({link})")
            if pub:
                lines.append(f"   - 📅 {pub}")
            if summary:
                lines.append(f"   - 📝 {summary}")
            lines.append("")  # 空行分隔
    return "\n".join(lines)

# ---------- 主函数 ----------
def fetch_google_news():
    # 确保目录存在
    os.makedirs(DATA_DIR, exist_ok=True)

    # 生成日期
    today = datetime.date.today().isoformat()  # 格式 "2026-09-03"
    filename = f"google_news_{today}.md"
    filepath = os.path.join(DATA_DIR, filename)

    print("🌐 开始抓取 Google News 多个专题...")
    print(f"📌 每个源最多抓取 {MAX_PER_SOURCE} 条\n")

    all_data = {}
    for name, url in NEWS_SOURCES.items():
        print(f"⏳ 正在抓取 [{name}] ...")
        entries = fetch_feed(url, name, MAX_PER_SOURCE)
        all_data[name] = entries

    # 生成 Markdown
    content = generate_report(all_data, today)

    # 写入文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    total = sum(len(v) for v in all_data.values())
    print(f"\n📊 总计抓取 {total} 条新闻，已保存至 {filepath}")

if __name__ == "__main__":
    fetch_google_news()

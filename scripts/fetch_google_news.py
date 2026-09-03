#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Google News 多专题新闻聚合器
支持多个 RSS 源，合并生成带日期的 Markdown 报告
"""

import feedparser
import requests
import datetime
import os
import sys
from typing import List, Dict

# ---------- 配置 ----------
# 存储目录
DATA_DIR = "data"
# 最多保留每个源的前 N 条新闻
MAX_PER_SOURCE = 10
# 请求超时（秒）
TIMEOUT = 15

# ---------- 新闻源定义 ----------
# 主题分类：商业、科技、健康、娱乐等（可根据需要增删）
NEWS_SOURCES = {
    "Business": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "Technology": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
    # 如果还有其它专题，可追加，例如：
    # "Health": "https://news.google.com/rss/headlines/section/topic/HEALTH?hl=en-US&gl=US&ceid=US:en",
    # "Entertainment": "https://news.google.com/rss/headlines/section/topic/ENTERTAINMENT?hl=en-US&gl=US&ceid=US:en",
}

# ---------- 工具函数 ----------
def fetch_feed(url: str, source_name: str) -> List[Dict]:
    """抓取单个 RSS 源，返回新闻条目列表（dict 含 title, link, published）"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
    except Exception as e:
        print(f"⚠️  [{source_name}] 网络请求失败: {e}")
        return []

    feed = feedparser.parse(resp.text)
    if not feed.entries:
        print(f"⚠️  [{source_name}] 解析到 0 条条目（可能返回非 RSS 内容）")
        return []

    entries = []
    for entry in feed.entries[:MAX_PER_SOURCE]:
        # 提取发布时间（若有）
        published = entry.get("published", "")
        entries.append({
            "title": entry.title,
            "link": entry.link,
            "published": published,
        })
    print(f"✅ [{source_name}] 抓取到 {len(entries)} 条新闻")
    return entries

def generate_report(sources_data: Dict[str, List[Dict]], date_str: str) -> str:
    """生成 Markdown 报告内容"""
    lines = [f"# Google News 综合热榜（{date_str}）\n"]
    for source_name, entries in sources_data.items():
        if not entries:
            lines.append(f"\n## {source_name}\n")
            lines.append("> 暂无数据\n")
            continue
        lines.append(f"\n## {source_name}\n")
        for idx, item in enumerate(entries, 1):
            title = item["title"]
            link = item["link"]
            # 可附加发布时间
            pub = item["published"]
            if pub:
                lines.append(f"{idx}. [{title}]({link})  *({pub})*")
            else:
                lines.append(f"{idx}. [{title}]({link})")
        lines.append("")  # 空行
    return "\n".join(lines)

# ---------- 主函数 ----------
def fetch_google_news():
    # 确保目录存在
    os.makedirs(DATA_DIR, exist_ok=True)

    # 生成日期
    today = datetime.date.today().isoformat()  # 格式 "2026-09-03"
    filename = f"google_news_{today}.md"
    filepath = os.path.join(DATA_DIR, filename)

    print("🌐 开始抓取 Google News 多个专题...\n")

    all_data = {}
    for name, url in NEWS_SOURCES.items():
        print(f"⏳ 正在抓取 [{name}] ...")
        entries = fetch_feed(url, name)
        all_data[name] = entries

    # 生成 Markdown
    content = generate_report(all_data, today)

    # 写入文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    # 统计信息
    total = sum(len(v) for v in all_data.values())
    print(f"\n📊 总计抓取 {total} 条新闻，已保存至 {filepath}")

if __name__ == "__main__":
    fetch_google_news()

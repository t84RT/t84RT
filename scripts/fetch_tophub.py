#!/usr/bin/env python3
"""
Tophub 科技热榜抓取脚本（基于 HTML 结构精准解析）
抓取 https://tophub.today/c/tech 所有来源的热门条目
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os

def fetch_tophub_tech():
    """抓取 Tophub 科技热榜"""
    url = "https://tophub.today/c/tech"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    all_items = []
    seen_titles = set()  # 全局去重

    # 1. 定位所有来源区块
    source_blocks = soup.find_all('div', class_='cc-cd')
    print(f"🔍 发现 {len(source_blocks)} 个来源区块")

    for block in source_blocks:
        # 提取来源名称
        source_elem = block.find('div', class_='cc-cd-lb')
        if not source_elem:
            continue
        source = source_elem.get_text(strip=True)

        # 2. 定位该区块内的所有条目（a 标签且内含 cc-cd-cb-ll）
        entries = block.find_all('a')
        for a in entries:
            item_div = a.find('div', class_='cc-cd-cb-ll')
            if not item_div:
                continue

            # 序号
            span_s = item_div.find('span', class_='s')
            if not span_s:
                continue
            try:
                index = int(span_s.get_text(strip=True))
            except ValueError:
                continue

            # 标题
            span_t = item_div.find('span', class_='t')
            if not span_t:
                continue
            title = span_t.get_text(strip=True)

            # 去重（防止同一标题在不同来源重复出现）
            if title in seen_titles:
                continue
            seen_titles.add(title)

            # 链接（补全相对路径）
            link = a.get('href', '')
            if link and not link.startswith('http'):
                if link.startswith('/'):
                    link = f"https://tophub.today{link}"
                else:
                    link = f"https://tophub.today/{link}"

            # 辅助信息（如作者、评论数）—— 可选
            span_e = item_div.find('span', class_='e')
            extra = span_e.get_text(strip=True) if span_e else ''

            all_items.append({
                'index': index,
                'title': title,
                'source': source,
                'url': link,
                'extra': extra
            })

    # 按序号排序
    all_items.sort(key=lambda x: x['index'])
    print(f"✅ 成功解析 {len(all_items)} 条热榜")
    return all_items


def generate_markdown(items):
    """生成 Markdown 文档"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y-%m-%d")

    md_lines = [
        f"# 📱 Tophub 科技热榜日报",
        f"",
        f"> 更新时间：{now}",
        f"> 数据来源：[Tophub 科技热榜](https://tophub.today/c/tech)",
        f"> 共抓取 {len(items)} 条",
        f"",
        f"---",
        f"",
    ]

    if not items:
        md_lines.append("⚠️ 暂无数据，请检查网络或稍后重试。")
    else:
        # 按来源统计
        source_count = {}
        for item in items:
            src = item['source']
            source_count[src] = source_count.get(src, 0) + 1

        md_lines.append("## 📊 来源分布")
        md_lines.append("")
        md_lines.append("| 来源 | 数量 |")
        md_lines.append("|------|------|")
        for src, count in sorted(source_count.items(), key=lambda x: -x[1]):
            md_lines.append(f"| {src} | {count} |")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

        md_lines.append("## 📰 热榜详情")
        md_lines.append("")

        for item in items:
            md_lines.append(f"### {item['index']}. {item['title']}")
            md_lines.append("")
            md_lines.append(f"- 🏷️ 来源：{item['source']}")
            if item.get('url'):
                md_lines.append(f"- 🔗 [原文链接]({item['url']})")
            if item.get('extra'):
                md_lines.append(f"- 📎 {item['extra']}")
            md_lines.append("")

    md_lines.append("---")
    md_lines.append("")
    md_lines.append("*本报告由 GitHub Actions 自动生成*")

    return "\n".join(md_lines)


def main():
    print("🔄 开始抓取 Tophub 科技热榜...")

    items = fetch_tophub_tech()

    if items is None:
        print("❌ 抓取失败")
        exit(1)

    md_content = generate_markdown(items)

    os.makedirs("docs", exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")

    with open(f"docs/tophub-{date_str}.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    with open("docs/daily.md", "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"📝 已生成: docs/tophub-{date_str}.md")
    print("✅ 完成!")


if __name__ == "__main__":
    main()

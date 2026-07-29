#!/usr/bin/env python3
"""
Tophub 科技热榜每日播报生成器
功能：
  1. 抓取 https://tophub.today/c/tech 所有热榜条目
  2. 生成 docs/daily.md 完整日报
  3. 自动更新 README.md 中的滚动播报区域（需预先放置占位标记）
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import sys
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== 可配置参数 ==========
CONFIG = {
    'url': 'https://tophub.today/c/tech',
    'timeout': 30,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'scroll_item_count': 60,          # 滚动显示条目数
    'scroll_duplicate': 12,           # 无缝循环复制的条目数
    'scroll_height': 420,             # 滚动窗口高度（px）
    'scroll_duration': 70,            # 滚动一圈秒数
    'full_list_count': 120,           # 完整列表显示的条数
    'output_dir': 'docs',
    'daily_filename': 'daily.md',
    'archive_prefix': 'tophub-',
}
# ==================================

def fetch_tophub_tech():
    """抓取 Tophub 科技热榜数据"""
    logger.info(f"开始抓取: {CONFIG['url']}")
    headers = {'User-Agent': CONFIG['user_agent']}

    try:
        response = requests.get(CONFIG['url'], headers=headers, timeout=CONFIG['timeout'])
        response.encoding = 'utf-8'
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"网络请求失败: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')
    all_items = []
    seen_titles = set()

    source_blocks = soup.find_all('div', class_='cc-cd')
    logger.info(f"发现 {len(source_blocks)} 个来源区块")

    for block in source_blocks:
        source_elem = block.find('div', class_='cc-cd-lb')
        if not source_elem:
            continue
        source = source_elem.get_text(strip=True)

        entries = block.find_all('a')
        for a in entries:
            item_div = a.find('div', class_='cc-cd-cb-ll')
            if not item_div:
                continue
            span_s = item_div.find('span', class_='s')
            if not span_s:
                continue
            try:
                index = int(span_s.get_text(strip=True))
            except ValueError:
                continue
            span_t = item_div.find('span', class_='t')
            if not span_t:
                continue
            title = span_t.get_text(strip=True)
            if title in seen_titles:
                continue
            seen_titles.add(title)

            link = a.get('href', '')
            if link and not link.startswith('http'):
                if link.startswith('/'):
                    link = f"https://tophub.today{link}"
                else:
                    link = f"https://tophub.today/{link}"

            span_e = item_div.find('span', class_='e')
            extra = span_e.get_text(strip=True) if span_e else ''

            all_items.append({
                'index': index,
                'title': title,
                'source': source,
                'url': link,
                'extra': extra
            })

    all_items.sort(key=lambda x: x['index'])
    logger.info(f"成功解析 {len(all_items)} 条去重后的热榜")
    return all_items


def generate_scroll_html(items):
    """生成滚动播报的 HTML/CSS 代码"""
    display = items[:CONFIG['scroll_item_count']]
    duplicated = display[:CONFIG['scroll_duplicate']]

    html = f"""
<style>
.rolling-news {{
    height: {CONFIG['scroll_height']}px;
    overflow: hidden;
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    background: #fafafa;
    padding: 8px 0;
    position: relative;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}}
.rolling-news ul {{
    list-style: none;
    margin: 0;
    padding: 0;
    animation: scrollUp {CONFIG['scroll_duration']}s linear infinite;
}}
.rolling-news ul:hover {{
    animation-play-state: paused;
}}
.rolling-news li {{
    padding: 10px 20px;
    border-bottom: 1px solid #f0f0f0;
    font-size: 15px;
    line-height: 1.5;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: #2c3e50;
    display: flex;
    justify-content: space-between;
    align-items: center;
}}
.rolling-news li:last-child {{
    border-bottom: none;
}}
.rolling-news .source-tag {{
    background: #e8f0fe;
    color: #1a73e8;
    font-size: 12px;
    padding: 2px 12px;
    border-radius: 20px;
    white-space: nowrap;
    margin-left: 12px;
    flex-shrink: 0;
}}
@keyframes scrollUp {{
    0% {{ transform: translateY(0); }}
    100% {{ transform: translateY(-50%); }}
}}
@media (prefers-color-scheme: dark) {{
    .rolling-news {{
        background: #1e1e1e;
        border-color: #333;
    }}
    .rolling-news li {{
        color: #e0e0e0;
        border-bottom-color: #2a2a2a;
    }}
    .rolling-news .source-tag {{
        background: #2a3a5a;
        color: #8ab4f8;
    }}
}}
</style>
<div class="rolling-news">
    <ul>
"""

    for item in display:
        html += f"<li><span>🔹 {item['index']}. {item['title']}</span><span class='source-tag'>{item['source']}</span></li>\n"
    for item in duplicated:
        html += f"<li><span>🔹 {item['index']}. {item['title']}</span><span class='source-tag'>{item['source']}</span></li>\n"

    html += """
    </ul>
</div>
"""
    return html


def update_readme_with_scroll(scroll_html):
    """将滚动播报 HTML 嵌入 README.md 的标记区域"""
    readme_path = "README.md"
    if not os.path.exists(readme_path):
        logger.warning(f"{readme_path} 不存在，跳过更新")
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    start_tag = "<!-- TOPHUB_NEWS_START -->"
    end_tag = "<!-- TOPHUB_NEWS_END -->"

    if start_tag not in content or end_tag not in content:
        logger.warning(f"README.md 中未找到 {start_tag} 和 {end_tag}，跳过更新")
        return

    new_section = f"{start_tag}\n\n{scroll_html}\n\n{end_tag}"
    pattern = re.escape(start_tag) + r".*?" + re.escape(end_tag)
    new_content = re.sub(pattern, new_section, content, flags=re.DOTALL)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    logger.info(f"✅ 已更新 README.md 中的滚动播报区域")


def generate_markdown(items):
    """生成完整的 Markdown 文档（用于 docs/）"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    scroll_html = generate_scroll_html(items)

    source_count = {}
    for item in items:
        src = item['source']
        source_count[src] = source_count.get(src, 0) + 1
    sorted_sources = sorted(source_count.items(), key=lambda x: -x[1])

    lines = [
        f"# 📱 Tophub 科技热榜日报",
        "",
        f"> 更新时间：{now}",
        f"> 数据来源：[Tophub 科技热榜]({CONFIG['url']})",
        f"> 共抓取 {len(items)} 条",
        "",
        "---",
        "",
        "## 🔄 滚动播报（自动轮播）",
        "",
        scroll_html,
        "",
        "---",
        "",
        "## 📊 来源分布",
        "",
        "| 来源 | 数量 |",
        "|------|------|",
    ]

    for src, cnt in sorted_sources:
        lines.append(f"| {src} | {cnt} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📰 完整列表")
    lines.append("")

    for item in items[:CONFIG['full_list_count']]:
        lines.append(f"### {item['index']}. {item['title']}")
        lines.append("")
        lines.append(f"- 🏷️ 来源：{item['source']}")
        if item.get('url'):
            lines.append(f"- 🔗 [原文链接]({item['url']})")
        if item.get('extra'):
            lines.append(f"- 📎 {item['extra']}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("*本报告由 GitHub Actions 自动生成*")

    return "\n".join(lines)


def main():
    logger.info("===== Tophub 科技热榜播报生成器启动 =====")

    items = fetch_tophub_tech()
    if items is None:
        logger.error("抓取失败，程序退出")
        sys.exit(1)

    if not items:
        logger.warning("抓取到 0 条数据，仍生成空报告")
    else:
        logger.info(f"成功抓取 {len(items)} 条数据")

    # 1. 生成 Markdown 日报
    md_content = generate_markdown(items)

    os.makedirs(CONFIG['output_dir'], exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    archive_path = os.path.join(CONFIG['output_dir'], f"{CONFIG['archive_prefix']}{date_str}.md")
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info(f"归档文件已生成: {archive_path}")

    daily_path = os.path.join(CONFIG['output_dir'], CONFIG['daily_filename'])
    with open(daily_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    logger.info(f"每日最新文件已更新: {daily_path}")

    # 2. 更新 README.md 中的滚动播报
    scroll_html = generate_scroll_html(items)
    update_readme_with_scroll(scroll_html)

    logger.info("✅ 全部完成！")


if __name__ == "__main__":
    main()

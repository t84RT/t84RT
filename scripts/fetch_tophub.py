#!/usr/bin/env python3
"""
Tophub 科技热榜抓取脚本
抓取 https://tophub.today/c/tech 并生成 Markdown 文档
"""

import requests
from bs4 import BeautifulSoup
import re
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
        print(f"请求失败: {e}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 提取所有文本内容
    text_content = soup.get_text()
    
    # 按行分割并清理
    lines = [line.strip() for line in text_content.split('\n') if line.strip()]
    
    # 解析热榜条目
    # 匹配模式：数字序号 + 标题（可能包含来源信息）
    news_items = []
    
    for line in lines:
        # 匹配以数字开头的行，如 "1 刚刚，Kimi K3开源..."
        match = re.match(r'^(\d+)\s+(.+)$', line)
        if match:
            index = int(match.group(1))
            title = match.group(2).strip()
            
            # 跳过过长的行（可能是合并了多条）
            if len(title) > 200:
                continue
            
            # 尝试提取来源（如 "36氪"、"虎嗅"等）
            source_match = re.search(r'([36氪虎嗅少数派IT之家Readhub抽屉酷安TechWeb煎蛋苹果Google]+)', title)
            source = source_match.group(1) if source_match else "未知来源"
            
            news_items.append({
                'index': index,
                'title': title,
                'source': source,
                'raw': line
            })
    
    return news_items[:50]  # 只取前50条

def generate_markdown(news_items):
    """生成 Markdown 文档"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    md_lines = [
        f"# 📱 Tophub 科技热榜日报",
        f"",
        f"> 更新时间：{now}",
        f"> 数据来源：[Tophub 科技热榜](https://tophub.today/c/tech)",
        f"",
        f"---",
        f"",
    ]
    
    if not news_items:
        md_lines.append("⚠️ 暂无数据，请检查网络或稍后重试。")
    else:
        # 按来源分组统计
        source_count = {}
        for item in news_items:
            src = item['source']
            source_count[src] = source_count.get(src, 0) + 1
        
        md_lines.append("## 📊 概览")
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
        
        for item in news_items:
            md_lines.append(f"### {item['index']}. {item['title']}")
            md_lines.append("")
            md_lines.append(f"- 🏷️ 来源：{item['source']}")
            md_lines.append("")
    
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("*本报告由 GitHub Actions 自动生成*")
    
    return "\n".join(md_lines)

def main():
    """主函数"""
    print("🔄 开始抓取 Tophub 科技热榜...")
    
    news_items = fetch_tophub_tech()
    
    if news_items is None:
        print("❌ 抓取失败")
        exit(1)
    
    print(f"✅ 成功抓取 {len(news_items)} 条数据")
    
    # 生成 Markdown
    md_content = generate_markdown(news_items)
    
    # 确保 docs 目录存在
    os.makedirs("docs", exist_ok=True)
    
    # 写入文件（使用日期命名，同时覆盖最新的 daily.md）
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    # 每日归档
    with open(f"docs/tophub-{date_str}.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    
    # 最新版本（便于查看）
    with open("docs/daily.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"📝 已生成文档: docs/tophub-{date_str}.md")
    print("✅ 完成!")

if __name__ == "__main__":
    main()

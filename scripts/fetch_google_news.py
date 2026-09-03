import feedparser
import requests
import datetime
import os
import sys

RSS_URL = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US%3Aen"

# 配置存储目录（可根据需要改为 "docs" 或其它）
DATA_DIR = "googlenew"

def fetch_google_news():
    # 确保目录存在
    os.makedirs(DATA_DIR, exist_ok=True)

    # 生成带日期的文件名
    today = datetime.date.today().isoformat()  # 格式 "2026-09-03"
    filename = f"google_news_{today}.md"
    filepath = os.path.join(DATA_DIR, filename)

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    print("🌐 正在请求 Google News RSS...")
    try:
        resp = requests.get(RSS_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        print(f"✅ HTTP 状态码: {resp.status_code}")
        print(f"📄 响应内容长度: {len(resp.text)} 字符")
    except Exception as e:
        print(f"❌ 网络请求失败: {e}")
        # 写入错误占位文件
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Google News 科技热榜（{today}）\n\n")
            f.write("⚠️ 网络请求失败，请稍后重试。\n")
        sys.exit(1)

    # 解析 RSS
    feed = feedparser.parse(resp.text)
    print(f"📊 解析到的条目数: {len(feed.entries)}")
    if len(feed.entries) == 0:
        print("⚠️ 没有解析到任何新闻条目，可能是 Google 返回了非 RSS 内容。")
        print("🔍 响应前 200 字符:", resp.text[:200])

    # 写入文件
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"# Google News 科技热榜（{today}）\n\n")
        for i, entry in enumerate(feed.entries[:10], 1):
            title = entry.title
            link = entry.link
            f.write(f"{i}. [{title}]({link})\n")
        if not feed.entries:
            f.write("⚠️ 暂时无法获取数据，请稍后重试。\n")

    print(f"✅ 已生成 {filepath}")

if __name__ == "__main__":
    fetch_google_news()

import feedparser
import requests
import datetime

RSS_URL = "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB?hl=en-US&gl=US&ceid=US%3Aen"

def fetch_google_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        resp = requests.get(RSS_URL, headers=headers, timeout=15)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
    except Exception as e:
        print(f"❌ 抓取失败: {e}")
        # 可以生成一个占位文件，避免中断工作流
        with open("google_news.md", "w", encoding="utf-8") as f:
            f.write(f"# Google News 科技热榜（{datetime.date.today()}）\n\n")
            f.write("⚠️ 暂时无法获取数据，请稍后重试。\n")
        return

    with open("google_news.md", "w", encoding="utf-8") as f:
        f.write(f"# Google News 科技热榜（{datetime.date.today()}）\n\n")
        for i, entry in enumerate(feed.entries[:10], 1):
            title = entry.title
            link = entry.link
            f.write(f"{i}. [{title}]({link})\n")

if __name__ == "__main__":
    fetch_google_news()

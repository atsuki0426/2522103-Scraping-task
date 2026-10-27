import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, urldefrag
from collections import deque
from urllib.robotparser import RobotFileParser
import time
import csv

# 武蔵野大学のトップページ
base_url = "https://www.musashino-u.ac.jp/"
domain = "www.musashino-u.ac.jp"

# URLとタイトルを保存する辞書
site_map = {}

# アクセス済みのURL
visited = set()

# これからアクセスするURL
queue = deque([base_url])
queued = {base_url}

# 全ページを取得
max_pages = float("inf")

# robots.txt を確認
robot = RobotFileParser()
robot.set_url(urljoin(base_url, "/robots.txt"))
robot.read()

# HTTP通信に使用
session = requests.Session()
session.headers.update({
    "User-Agent": "UniversitySitemapStudentBot/1.0"
})

while queue and len(visited) < max_pages:

    # 次にアクセスするURLを取り出す
    url = queue.popleft()
    queued.discard(url)

    # アクセス済みならスキップ
    if url in visited:
        continue

    visited.add(url)

    # robots.txt で許可されていなければスキップ
    if not robot.can_fetch(
        session.headers["User-Agent"], url
    ):
        print("アクセス対象外:", url)
        continue

    try:
        # サーバーへの負荷を軽減
        time.sleep(0.5)

        # Webサイトにアクセス
        response = session.get(url, timeout=15)
        response.raise_for_status()

        # HTML以外は処理しない
        content_type = response.headers.get("Content-Type", "")

        if "text/html" not in content_type.lower():
            continue

        # HTMLを解析
        soup = BeautifulSoup(response.content, "html.parser")

        # titleを取得
        title = soup.title.get_text(strip=True) if soup.title else ""

        # URLをkey、タイトルをvalueとして保存
        site_map[url] = title

        print(f"{len(site_map)}件目: {title}")

        # ページ内のリンクを取得
        for a in soup.find_all("a", href=True):

            # 相対URLを絶対URLに変換
            link = urljoin(url, a["href"])

            # URLの#以降を削除
            link, _ = urldefrag(link)

            # URLを解析
            parsed = urlparse(link)

            # 同じドメインのみ対象
            if parsed.hostname != domain:
                continue

            # httpとhttpsのみ対象
            if parsed.scheme not in ("http", "https"):
                continue

            # 重複したURLを追加しない
            if link not in visited and link not in queued:
                queue.append(link)
                queued.add(link)

    except requests.RequestException as e:
        print("エラー:", url, e)

# 結果を表示
print("\n取得したサイトマップ")

for url, title in site_map.items():
    print(url, ":", title)

print("\n取得ページ数:", len(site_map))

# 辞書型変数をCSVファイルに保存
with open("sitemap.csv", "w", newline="", encoding="utf-8-sig") as f:

    writer = csv.writer(f)

    # 見出し
    writer.writerow(["URL", "title"])

    # 辞書の内容を書き込む
    for url, title in site_map.items():
        writer.writerow([url, title])

print("sitemap.csvに保存しました！")
import streamlit as st
import requests
import re
from urllib.parse import unquote

st.set_page_config(
    page_title="FC27 Salah画像URL調査",
    page_icon="⚽",
    layout="centered"
)

st.title("⚽ FC27 Salah 画像URL調査")

PLAYER_ID = "209331"

URL = (
    "https://www.ea.com/ja/games/ea-sports-fc/"
    "ratings/player-ratings/mohamed-salah/209331"
)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.ea.com/"
}

st.write("Salah（ID: 209331）のページを調査しています。")

try:
    response = requests.get(
        URL,
        headers=headers,
        timeout=20
    )

    st.write("HTTPステータス:", response.status_code)

    if response.status_code != 200:
        st.error("EA公式ページを取得できませんでした。")
        st.stop()

    html = response.text

except Exception as e:
    st.error("ページ取得エラー")
    st.code(str(e))
    st.stop()


st.success("EA公式ページの取得に成功しました！")


# ==========================================
# ID 209331 の周辺を検索
# ==========================================

st.subheader("① ID 209331 の周辺データ")

positions = [
    m.start()
    for m in re.finditer(
        re.escape(PLAYER_ID),
        html
    )
]

st.write(
    f"「209331」がページ内で {len(positions)} 回見つかりました。"
)

if len(positions) == 0:
    st.error("209331がページ内に見つかりませんでした。")
    st.stop()


# ==========================================
# ID周辺のHTMLを調査
# ==========================================

all_urls = []

for position in positions:

    start = max(0, position - 5000)
    end = min(len(html), position + 5000)

    section = html[start:end]

    # 通常のURL
    urls = re.findall(
        r'https?://[^"\'<>\s]+',
        section
    )

    # エスケープされたURL
    escaped_urls = re.findall(
        r'https?:\\/\\/[^"\'<>\s]+',
        section
    )

    urls += escaped_urls

    for url in urls:

        url = url.replace("\\/", "/")
        url = unquote(url)

        # HTMLの末尾につく文字を除去
        url = url.rstrip("\\'\"<>),;")

        if url not in all_urls:
            all_urls.append(url)


# ==========================================
# 画像っぽいURLだけ抽出
# ==========================================

image_urls = []

image_extensions = [
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".avif"
]

image_keywords = [
    "image",
    "images",
    "portrait",
    "player",
    "ratings",
    "pulse",
    "ea.com"
]

for url in all_urls:

    lower_url = url.lower()

    if (
        any(ext in lower_url for ext in image_extensions)
        or any(keyword in lower_url for keyword in image_keywords)
    ):
        if url not in image_urls:
            image_urls.append(url)


st.subheader("② Salah周辺から見つかった画像URL")

if len(image_urls) == 0:

    st.warning(
        "Salah専用と思われる画像URLは見つかりませんでした。"
    )

else:

    st.success(
        f"{len(image_urls)}個の画像URL候補が見つかりました。"
    )

    for i, url in enumerate(image_urls[:30], 1):

        st.write(f"### 候補 {i}")

        st.code(url)


# ==========================================
# 209331周辺のHTMLを確認
# ==========================================

st.subheader("③ ID 209331 周辺のHTML")

for i, position in enumerate(positions[:3], 1):

    start = max(0, position - 1500)
    end = min(len(html), position + 1500)

    section = html[start:end]

    with st.expander(
        f"209331 周辺のHTML {i}"
    ):
        st.code(
            section,
            language="html"
        )


# ==========================================
# 画像URLを実際にテスト
# ==========================================

st.subheader("④ 画像URLの動作確認")

success = False

for i, url in enumerate(image_urls[:30], 1):

    try:

        r = requests.get(
            url,
            headers=headers,
            timeout=10
        )

        content_type = r.headers.get(
            "Content-Type",
            ""
        )

        st.write(
            f"候補 {i}: HTTP {r.status_code} / {content_type}"
        )

        if (
            r.status_code == 200
            and content_type.startswith("image/")
        ):

            st.success(
                "画像として取得できるURLを発見しました！"
            )

            st.code(url)

            st.image(
                r.content,
                width=300,
                caption="取得した画像"
            )

            success = True
            break

    except Exception as e:

        st.write(
            f"候補 {i}: エラー"
        )

        st.code(str(e))


# ==========================================
# 結果
# ==========================================

st.divider()

if success:

    st.success(
        "🎉 Salahの画像URLを発見できました！"
    )

    st.write(
        "このURL形式を使えば、次に16,228人の画像表示へ進めます。"
    )

else:

    st.warning(
        "今回は画像URLを特定できませんでした。"
    )

    st.write(
        "③の「209331 周辺のHTML」に出ている内容から、"
        "Salah専用画像の場所を特定できます。"
    )

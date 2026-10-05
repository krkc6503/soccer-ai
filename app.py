import streamlit as st
import requests
import re
import json
import html as html_lib

st.set_page_config(
    page_title="FC27 Salah 画像調査",
    page_icon="⚽",
    layout="centered"
)

st.title("⚽ FC27 Salah 画像調査")

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

# ==========================================
# EA公式ページ取得
# ==========================================

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

    page = response.text

except Exception as e:
    st.error("ページ取得エラー")
    st.code(str(e))
    st.stop()

st.success("EA公式ページの取得に成功しました！")

# HTMLエンティティを戻す
page = html_lib.unescape(page)

# ==========================================
# 209331の出現位置
# ==========================================

positions = [
    m.start()
    for m in re.finditer(
        re.escape(PLAYER_ID),
        page
    )
]

st.subheader("① 209331の検索結果")

st.write(
    f"「209331」が {len(positions)} 回見つかりました。"
)

if not positions:
    st.error("209331が見つかりませんでした。")
    st.stop()

# ==========================================
# 画像関連キーワード
# ==========================================

keywords = [
    "image",
    "imageUrl",
    "imageURL",
    "imageUrl",
    "avatar",
    "avatarUrl",
    "portrait",
    "playerImage",
    "player_image",
    "card",
    "playerCard",
    "headshot",
    "photo",
    "ratings-images",
    "pulse.ea.com",
    "209331"
]

# ==========================================
# 209331周辺の情報を検索
# ==========================================

st.subheader("② 209331周辺の画像情報")

found_sections = []

for position in positions:

    start = max(0, position - 10000)
    end = min(len(page), position + 10000)

    section = page[start:end]

    # 画像関連キーワードがある部分だけ確認
    for keyword in keywords:

        if keyword.lower() in section.lower():

            # キーワードの位置
            matches = re.finditer(
                re.escape(keyword),
                section,
                flags=re.IGNORECASE
            )

            for match in matches:

                local_start = max(
                    0,
                    match.start() - 500
                )

                local_end = min(
                    len(section),
                    match.end() + 1000
                )

                snippet = section[
                    local_start:local_end
                ]

                if snippet not in found_sections:
                    found_sections.append(snippet)

# ==========================================
# 表示
# ==========================================

if not found_sections:

    st.warning(
        "画像関連データを見つけられませんでした。"
    )

else:

    st.success(
        f"{len(found_sections)}個の関連データを見つけました。"
    )

    for i, snippet in enumerate(
        found_sections[:20],
        1
    ):

        with st.expander(
            f"関連データ {i}"
        ):

            st.code(
                snippet,
                language="text"
            )

# ==========================================
# URL候補を抽出
# ==========================================

st.subheader("③ 画像URL候補")

# HTML内にあるURLを全部取得
all_urls = re.findall(
    r'https?://[^"\'<>\s]+',
    page
)

clean_urls = []

for url in all_urls:

    url = url.replace(
        "\\/",
        "/"
    )

    url = html_lib.unescape(url)

    url = url.rstrip(
        "\\'\"<>),;"
    )

    if url not in clean_urls:
        clean_urls.append(url)

# 画像っぽいURL
image_urls = []

for url in clean_urls:

    lower = url.lower()

    if any(
        x in lower
        for x in [
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".avif",
            "image",
            "portrait",
            "player",
            "ratings-images",
            "pulse.ea.com"
        ]
    ):

        if url not in image_urls:
            image_urls.append(url)

# 209331がURLに入っているものを優先
priority_urls = []

for url in image_urls:

    if PLAYER_ID in url:

        priority_urls.append(url)

for url in image_urls:

    if url not in priority_urls:
        priority_urls.append(url)

st.write(
    f"画像URL候補: {len(priority_urls)}件"
)

if priority_urls:

    for i, url in enumerate(
        priority_urls[:50],
        1
    ):

        st.write(
            f"**候補 {i}**"
        )

        st.code(url)

else:

    st.warning(
        "画像URL候補が見つかりませんでした。"
    )

# ==========================================
# Salah専用と思われるURLをテスト
# ==========================================

st.subheader("④ Salah専用URLのテスト")

salah_urls = [
    url
    for url in priority_urls
    if PLAYER_ID in url
]

if not salah_urls:

    st.info(
        "URLそのものに209331が含まれる画像URLはありませんでした。"
    )

else:

    for i, image_url in enumerate(
        salah_urls[:10],
        1
    ):

        st.write(
            f"### テスト {i}"
        )

        st.code(image_url)

        try:

            r = requests.get(
                image_url,
                headers=headers,
                timeout=10
            )

            content_type = r.headers.get(
                "Content-Type",
                ""
            )

            st.write(
                "HTTP:",
                r.status_code
            )

            st.write(
                "Content-Type:",
                content_type
            )

            if (
                r.status_code == 200
                and content_type.startswith("image/")
            ):

                st.success(
                    "画像として取得できました！"
                )

                st.image(
                    r.content,
                    width=300
                )

        except Exception as e:

            st.warning(
                "取得エラー"
            )

            st.code(str(e))

# ==========================================
# ⑤ ページ内のJSONらしきデータ
# ==========================================

st.subheader("⑤ ページ内JSONデータ")

json_blocks = re.findall(
    r'<script[^>]*>(.*?)</script>',
    page,
    flags=re.DOTALL | re.IGNORECASE
)

json_hits = []

for block in json_blocks:

    if PLAYER_ID in block:

        json_hits.append(block)

st.write(
    f"209331を含むscriptが {len(json_hits)}個あります。"
)

for i, block in enumerate(
    json_hits[:10],
    1
):

    with st.expander(
        f"JSON/script {i}"
    ):

        # 長すぎる場合は周辺だけ表示
        positions2 = [
            m.start()
            for m in re.finditer(
                PLAYER_ID,
                block
            )
        ]

        if positions2:

            for pos in positions2[:5]:

                start = max(
                    0,
                    pos - 2000
                )

                end = min(
                    len(block),
                    pos + 5000
                )

                st.code(
                    block[start:end],
                    language="json"
                )

st.divider()

st.info(
    "この画面の「②」「③」「⑤」に出た内容を確認すれば、"
    "Salah専用画像の場所を特定できます。"
)

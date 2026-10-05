import streamlit as st
import requests
import re
from PIL import Image
from io import BytesIO

# ==============================
# ページ設定
# ==============================

st.set_page_config(
    page_title="EA FC27 画像テスト",
    page_icon="⚽",
    layout="centered"
)

st.title("⚽ EA FC27 画像テスト")

st.write("Mohamed Salah（ID: 209331）のFC27画像を取得します。")

PLAYER_ID = 209331

EA_PAGE_URL = (
    "https://www.ea.com/ja/games/ea-sports-fc/"
    "ratings/player-ratings/mohamed-salah/209331"
)

# ==============================
# EA公式ページを取得
# ==============================

st.subheader("① EA公式ページ")

st.link_button(
    "EA公式のSalah FC27ページを開く",
    EA_PAGE_URL
)

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "*/*;q=0.8"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://www.ea.com/"
}

try:

    response = requests.get(
        EA_PAGE_URL,
        headers=headers,
        timeout=20
    )

    st.write("EA公式ページのHTTPステータス:", response.status_code)

    if response.status_code != 200:

        st.error(
            "EA公式ページをStreamlitサーバーから取得できませんでした。"
        )

        st.write(
            "この場合でも、EA公式ページ自体が存在しないという意味ではありません。"
        )

        st.stop()

    html = response.text

    st.success("EA公式ページの取得に成功しました！")

except Exception as e:

    st.error("EA公式ページの取得中にエラーが発生しました。")

    st.code(str(e))

    st.stop()


# ==============================
# ページ内から画像URLを探す
# ==============================

st.subheader("② ページ内の画像URLを検索")

image_urls = []


# ------------------------------
# og:image
# ------------------------------

patterns = [
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',

    r'<meta[^>]+name=["\']twitter:image["\'][^>]+content=["\']([^"\']+)["\']',
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']twitter:image["\']'
]

for pattern in patterns:

    matches = re.findall(
        pattern,
        html,
        flags=re.IGNORECASE
    )

    for url in matches:

        if url not in image_urls:
            image_urls.append(url)


# ------------------------------
# EA画像URLをHTMLから探す
# ------------------------------

ea_image_patterns = [
    r'https://[^"\']+ratings-images-prod[^"\']+',
    r'https:\\/\\/[^"\']+ratings-images-prod[^"\']+',
]

for pattern in ea_image_patterns:

    matches = re.findall(
        pattern,
        html,
        flags=re.IGNORECASE
    )

    for url in matches:

        url = url.replace("\\/", "/")

        if url not in image_urls:
            image_urls.append(url)


# ==============================
# 結果表示
# ==============================

if len(image_urls) == 0:

    st.warning(
        "EA公式ページから画像URLを見つけられませんでした。"
    )

    st.write(
        "この場合はEA公式ページがJavaScriptで画像を読み込んでいる可能性があります。"
    )

    st.stop()


st.success(
    f"画像URL候補を {len(image_urls)} 件見つけました。"
)


# ==============================
# 画像を順番にテスト
# ==============================

st.subheader("③ 画像表示テスト")

image_found = False

for i, image_url in enumerate(image_urls[:10], 1):

    st.write(f"### テスト {i}")

    st.code(image_url)

    try:

        image_response = requests.get(
            image_url,
            headers=headers,
            timeout=15
        )

        st.write(
            "画像HTTPステータス:",
            image_response.status_code
        )

        content_type = image_response.headers.get(
            "Content-Type",
            ""
        )

        st.write(
            "Content-Type:",
            content_type
        )

        if (
            image_response.status_code == 200
            and image_response.content
        ):

            try:

                image = Image.open(
                    BytesIO(image_response.content)
                )

                st.image(
                    image,
                    width=300,
                    caption="Mohamed Salah - EA SPORTS FC 27"
                )

                st.success(
                    "🎉 FC27画像の表示に成功しました！"
                )

                st.write("使用できた画像URL")

                st.code(image_url)

                image_found = True

                break

            except Exception as image_error:

                st.warning(
                    "HTTP 200ですが画像として読み込めませんでした。"
                )

                st.code(str(image_error))

        else:

            st.warning(
                "この画像URLでは取得できませんでした。"
            )

    except Exception as e:

        st.warning(
            "画像取得中にエラーが発生しました。"
        )

        st.code(str(e))


# ==============================
# 最終結果
# ==============================

st.divider()

if image_found:

    st.success(
        "SalahのFC27画像を取得できました！"
    )

    st.write(
        "この画像URLの仕組みを使って、"
        "次に16,228人の選手画像へ対応できます。"
    )

else:

    st.error(
        "今回は画像を取得できませんでした。"
    )

    st.write(
        "ただし、FC27の選手データが壊れているわけではありません。"
    )

    st.write(
        "EA公式ページではSalahのFC27レーティングが確認できます。"
    )

    st.link_button(
        "EA公式 Salah FC27ページ",
        EA_PAGE_URL
    )

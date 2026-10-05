import streamlit as st
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(
    page_title="FC27 画像テスト",
    page_icon="⚽",
    layout="centered"
)

st.title("⚽ EA FC27 画像テスト")

st.write("Mohamed Salah（ID: 209331）のFC27画像を確認します。")

player_id = 209331

# FC27で考えられる画像URLを順番にテスト
image_urls = [
    f"https://ratings-images-prod.pulse.ea.com/FC27/full/player-portraits/p{player_id}.png?padding=0.7",
    f"https://ratings-images-prod.pulse.ea.com/FC27/full/player-portraits/p{player_id}.png",
    f"https://ratings-images-prod.pulse.ea.com/FC27/components/items/{player_id}_en.webp",
]

success = False

for i, url in enumerate(image_urls, 1):

    st.write(f"### テスト {i}")

    st.code(url)

    try:
        response = requests.get(
            url,
            timeout=10,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        st.write("HTTPステータス:", response.status_code)

        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))

            st.image(
                image,
                width=250,
                caption="Mohamed Salah - FC27"
            )

            st.success("画像の読み込みに成功しました！")

            st.write("使用できたURL:")
            st.code(url)

            success = True
            break

        else:
            st.warning("このURLでは画像を取得できませんでした。")

    except Exception as e:
        st.warning(f"読み込みエラー: {e}")


if not success:
    st.error("FC27の画像URL候補では画像を取得できませんでした。")

    st.info(
        "選手データ自体は正常です。"
        "EA公式にはSalah（ID 209331）のFC27ページが存在します。"
    )

    st.write("EA公式FC27選手ページ")

    st.markdown(
        "https://www.ea.com/ja/games/ea-sports-fc/ratings/"
        "player-ratings/mohamed-salah/209331"
    )

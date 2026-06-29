import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Soccer AI", layout="wide")

st.title("⚽ Soccer AI Ver2.0")

st.info(
    "※ 日本語検索は一部の選手のみ対応しています。\n"
    "検索できない場合は英語で検索してください。"
)

st.markdown(
    "🔍 [選手名が分からない場合はこちら](https://www.google.com/search?q=サッカー選手一覧)"
)

# -------------------------------
# Transfermarktデータ
# -------------------------------

tm = pd.read_csv("players_small.csv")

tm = tm[
    [
        "name",
        "current_club_name",
        "position",
        "date_of_birth",
        "market_value_in_eur",
        "highest_market_value_in_eur",
    ]
].dropna()

tm["date_of_birth"] = pd.to_datetime(
    tm["date_of_birth"],
    errors="coerce"
)

tm = tm.dropna(subset=["date_of_birth"])

tm["Age"] = 2026 - tm["date_of_birth"].dt.year

# -------------------------------
# FC26データ
# -------------------------------

fc = pd.read_csv("FC26_20250921.csv")

fc = fc[
    [
        "short_name",
        "long_name",
        "overall",
        "potential",
        "value_eur",
        "club_name",
        "pace",
        "shooting",
        "passing",
        "dribbling",
        "defending",
        "physic",
        "player_face_url",
    ]
].copy()

# -------------------------------
# 名前を統一
# -------------------------------

tm["merge_name"] = (
    tm["name"]
    .str.lower()
    .str.strip()
)

fc["merge_name"] = (
    fc["short_name"]
    .str.lower()
    .str.strip()
)

# -------------------------------
# データ結合
# -------------------------------

df = tm.merge(
    fc,
    on="merge_name",
    how="left"
)

# -------------------------------
# 日本語辞書
# -------------------------------

player_jp = {

    "Kylian Mbappe":"エムバペ",
    "Erling Haaland":"ハーランド",
    "Jude Bellingham":"ベリンガム",
    "Vinicius Junior":"ヴィニシウス",
    "Bukayo Saka":"サカ",
    "Mohamed Salah":"サラー",
    "Harry Kane":"ケイン",
    "Kevin De Bruyne":"デブライネ",
    "Lionel Messi":"メッシ",
    "Cristiano Ronaldo":"ロナウド",
    "Lamine Yamal":"ヤマル",
    "Pedri":"ペドリ",
    "Rodri":"ロドリ",
    "Cole Palmer":"パーマー",
    "Florian Wirtz":"ヴィルツ",
    "Jamal Musiala":"ムシアラ",
    "Neymar":"ネイマール",
    "Son Heung-min":"ソン",
}

club_jp = {

    "Real Madrid":"レアル・マドリード",
    "FC Barcelona":"バルセロナ",
    "Manchester City":"マンチェスター・シティ",
    "Liverpool FC":"リヴァプール",
    "Arsenal FC":"アーセナル",
    "Chelsea FC":"チェルシー",
    "Paris Saint-Germain":"パリ・サンジェルマン",
    "Bayern Munich":"バイエルン",
}

df["NameJP"] = df["name"].replace(player_jp)
df["NameJP"] = df["NameJP"].fillna(df["name"])

df["ClubJP"] = df["current_club_name"].replace(club_jp)
df["ClubJP"] = df["ClubJP"].fillna(df["current_club_name"])

# -------------------------------
# ポジション数値化
# -------------------------------

position_map = {
    "Goalkeeper": 1,
    "Defender": 2,
    "Midfield": 3,
    "Attack": 4,
}

df["PositionNum"] = (
    df["position"]
    .map(position_map)
    .fillna(3)
)

# -------------------------------
# AI学習
# -------------------------------

X = df[["Age", "PositionNum"]]
y = df["market_value_in_eur"]

model = LinearRegression()
model.fit(X, y)

# -------------------------------
# モード選択
# -------------------------------

mode = st.radio(
    "選択",
    ["実在選手", "自分で入力"]
)

# ===============================
# 実在選手モード
# ===============================

if mode == "実在選手":

    search = st.text_input(
        "選手名（日本語・英語OK）"
    )

    filtered = df[
        df["NameJP"].str.contains(
            search,
            case=False,
            na=False,
        )
        |
        df["name"].str.contains(
            search,
            case=False,
            na=False,
        )
    ]

    if len(filtered) == 0:

        st.warning("選手が見つかりません。")

    else:

        display = (
            filtered["NameJP"]
            + "（"
            + filtered["ClubJP"]
            + "）"
        )

        player = st.selectbox(
            "選手を選択",
            display
        )

        selected = filtered.iloc[
            display.tolist().index(player)
        ]

        # -----------------------
        # 顔写真
        # -----------------------

        if pd.notna(selected["player_face_url"]):

            st.image(
                selected["player_face_url"],
                width=180,
            )

        # -----------------------
        # 基本情報
        # -----------------------

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "Overall",
                int(selected["overall"])
                if pd.notna(selected["overall"])
                else "-"
            )

            st.metric(
                "Potential",
                int(selected["potential"])
                if pd.notna(selected["potential"])
                else "-"
            )

            st.metric(
                "Age",
                int(selected["Age"])
            )

        with col2:

            st.metric(
                "Current Value (€)",
                f"{selected['market_value_in_eur']:,.0f}"
            )

            st.metric(
                "Highest Value (€)",
                f"{selected['highest_market_value_in_eur']:,.0f}"
            )

            st.metric(
                "Club",
                selected["ClubJP"]
            )

        # -----------------------
        # AI予測
        # -----------------------

        pred = model.predict(
            [[
                selected["Age"],
                selected["PositionNum"]
            ]]
        )

        st.subheader("🤖 AI予測市場価値")

        st.success(
            f"{pred[0]:,.0f} €"
        )

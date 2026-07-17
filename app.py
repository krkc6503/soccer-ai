import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from math import pi

# -----------------------------
# ページ設定
# -----------------------------
st.set_page_config(
    page_title="EA FC26 × Transfermarkt",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ EA FC26 × Transfermarkt 選手分析アプリ")
st.write("EA FC26能力値とTransfermarkt市場価値を比較できます。")

# -----------------------------
# データ読み込み
# -----------------------------
@st.cache_data
def load_data():
    ea = pd.read_csv("EAFC26-Men(1).csv")
    tm = pd.read_csv("players_small(1).csv")

    ea.columns = ea.columns.str.strip()
    tm.columns = tm.columns.str.strip()

    return ea, tm

ea, tm = load_data()

# -----------------------------
# クラブ名日本語
# -----------------------------
club_dict = {
    "Real Madrid":"レアル・マドリード",
    "FC Barcelona":"FCバルセロナ",
    "Manchester City":"マンチェスター・シティ",
    "Liverpool":"リヴァプール",
    "Arsenal":"アーセナル",
    "Chelsea":"チェルシー",
    "Manchester United":"マンチェスター・ユナイテッド",
    "Tottenham Hotspur":"トッテナム",
    "Bayern Munich":"バイエルン・ミュンヘン",
    "Borussia Dortmund":"ドルトムント",
    "Paris Saint-Germain":"パリ・サンジェルマン",
    "Inter":"インテル",
    "AC Milan":"ACミラン",
    "Juventus":"ユヴェントス",
    "Napoli":"ナポリ",
    "Atletico Madrid":"アトレティコ・マドリード"
}

# -----------------------------
# 選手名列を探す
# -----------------------------
possible_names = [
    "Name",
    "name",
    "Player",
    "PLAYER",
    "Full Name",
    "player_name"
]

player_column = None

for c in possible_names:
    if c in ea.columns:
        player_column = c
        break

if player_column is None:
    player_column = ea.columns[0]

# -----------------------------
# 検索
# -----------------------------
st.sidebar.header("検索")

player = st.sidebar.text_input("選手名を入力")

if player != "":

    result = ea[
        ea[player_column]
        .astype(str)
        .str.contains(player, case=False, na=False)
    ]

    if result.empty:

        st.error("選手が見つかりません。")

    else:

        row = result.iloc[0]

        st.header(row[player_column])

        col1, col2 = st.columns([1,1])

        with col1:

            st.subheader("EA FC26")

            if "Overall" in ea.columns:
                st.metric("OVR", row["Overall"])

            stats = [
                "PAC",
                "SHO",
                "PAS",
                "DRI",
                "DEF",
                "PHY"
            ]

            for s in stats:
                if s in ea.columns:
                    st.metric(s, row[s])

        with col2:

            tm_result = tm[
                tm["name"]
                .astype(str)
                .str.contains(player, case=False, na=False)
            ]

            if not tm_result.empty:

                info = tm_result.iloc[0]

                st.subheader("Transfermarkt")

                if "current_club_name" in info:

                    club = info["current_club_name"]

                    jp = club_dict.get(club, club)

                    st.write("クラブ：", jp)

                if "position" in info:
                    st.write("ポジション：", info["position"])

                if "market_value_in_eur" in info:

                    value = info["market_value_in_eur"]

                    st.metric(
                        "市場価値 (€)",
                        f"€{value:,.0f}"
                    )

                if "highest_market_value_in_eur" in info:

                    st.metric(
                        "最高市場価値 (€)",
                        f"€{info['highest_market_value_in_eur']:,.0f}"
                    )

                if "date_of_birth" in info:

                    birth = pd.to_datetime(info["date_of_birth"])

                    age = int(
                        (pd.Timestamp.today()-birth).days/365.25
                    )

                    st.write("年齢：", age)

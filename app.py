import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ==========================================
# ページ設定
# ==========================================
st.set_page_config(
    page_title="EA FC26 × Transfermarkt",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ EA FC26 × Transfermarkt 選手分析システム")
st.caption("EA FC26能力値 × Transfermarkt市場価値")

# ==========================================
# データ読み込み
# ==========================================
@st.cache_data
def load_data():

    ea = pd.read_csv("EAFC26-Men(1).csv")
    tm = pd.read_csv("players_small(1).csv")

    ea.columns = ea.columns.str.strip()
    tm.columns = tm.columns.str.strip()

    return ea, tm


ea, tm = load_data()

# ==========================================
# クラブ日本語辞書
# ==========================================
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
    "Atlético Madrid":"アトレティコ・マドリード"
}

# ==========================================
# 検索
# ==========================================
st.sidebar.header("🔍 選手検索")

player = st.sidebar.text_input("選手名")

player_list = sorted(ea["Name"].dropna().astype(str).unique())

selected = st.sidebar.selectbox(
    "一覧から選択",
    [""] + player_list
)

if selected != "":
    player = selected

# ==========================================
# 選手表示
# ==========================================
if player != "":

    result = ea[
        ea["Name"]
        .astype(str)
        .str.contains(player, case=False, na=False)
    ]

    if result.empty:

        st.error("選手が見つかりません。")
        st.stop()

    row = result.iloc[0]

    st.header(f"⭐ {row['Name']}")

    col1, col2 = st.columns([1,1])

    with col1:

        st.subheader("EA FC26")

        st.metric("OVR", row["OVR"])

        stats = ["PAC","SHO","PAS","DRI","DEF","PHY"]

        for s in stats:

            st.metric(s, row[s])

    with col2:

        tm_result = tm[
            tm["name"]
            .astype(str)
            .str.contains(player, case=False, na=False)
        ]

        if not tm_result.empty:

            info = tm_result.iloc[0]

            club = club_dict.get(
                info["current_club_name"],
                info["current_club_name"]
            )

            st.subheader("Transfermarkt")

            st.write("クラブ：", club)

            st.write("ポジション：", info["position"])

            st.metric(
                "市場価値",
                f"€{info['market_value_in_eur']:,.0f}"
            )

            st.metric(
                "最高市場価値",
                f"€{info['highest_market_value_in_eur']:,.0f}"
            )

            birth = pd.to_datetime(info["date_of_birth"])

            age = int(
                (pd.Timestamp.today()-birth).days/365.25
            )

            st.write("年齢：", age)

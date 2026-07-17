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
# ==========================================
# レーダーチャート
# ==========================================
if player != "" and not result.empty:
st.divider()
st.subheader("📊 能力レーダーチャート")

radar_stats = ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]

if all(stat in ea.columns for stat in radar_stats):

    values = []

    for stat in radar_stats:
        values.append(float(row[stat]))
    st.write("row exists:", "row" in locals())
    values += values[:1]

    angles = np.linspace(
        0,
        2 * np.pi,
        len(radar_stats),
        endpoint=False
    ).tolist()

    angles += angles[:1]

    fig = plt.figure(figsize=(6, 6))

    ax = plt.subplot(111, polar=True)

    ax.plot(
        angles,
        values,
        linewidth=2
    )

    ax.fill(
        angles,
        values,
        alpha=0.25
    )

    ax.set_xticks(angles[:-1])

    ax.set_xticklabels(radar_stats)

    ax.set_ylim(0, 100)

    st.pyplot(fig)

# ==========================================
# 能力値グラフ
# ==========================================

st.divider()
st.subheader("📈 能力値グラフ")

graph = pd.DataFrame({
    "能力": radar_stats,
    "数値": [row[s] for s in radar_stats]
})

st.bar_chart(
    graph.set_index("能力")
)

# ==========================================
# 基本情報
# ==========================================

st.divider()
st.subheader("📋 EAFC26 基本情報")

show_cols = [
    "Overall",
    "Potential",
    "Age",
    "Height",
    "Weight",
    "Preferred Foot",
    "Weak Foot",
    "Skill Moves",
    "Position"
]

for c in show_cols:

    if c in ea.columns:

        st.write(f"**{c}** : {row[c]}")
# ==========================================
# 2選手比較
# ==========================================

st.divider()
st.header("👥 2選手比較")

players = sorted(ea[player_column].dropna().astype(str).unique())

col1, col2 = st.columns(2)

with col1:
    player1 = st.selectbox(
        "選手①",
        players,
        key="compare1"
    )

with col2:
    player2 = st.selectbox(
        "選手②",
        players,
        index=1 if len(players) > 1 else 0,
        key="compare2"
    )

if player1 and player2:

    p1 = ea[ea[player_column] == player1].iloc[0]
    p2 = ea[ea[player_column] == player2].iloc[0]

    compare_stats = ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]

    compare_df = pd.DataFrame({
        player1: [p1[s] if s in ea.columns else 0 for s in compare_stats],
        player2: [p2[s] if s in ea.columns else 0 for s in compare_stats]
    }, index=compare_stats)

    st.dataframe(compare_df)

    st.bar_chart(compare_df.T)

# ==========================================
# 市場価値ランキング
# ==========================================

st.divider()
st.header("💶 市場価値ランキング TOP20")

if "market_value_in_eur" in tm.columns:

    ranking = tm.sort_values(
        "market_value_in_eur",
        ascending=False
    ).head(20)

    show_columns = ["name"]

    if "current_club_name" in ranking.columns:
        show_columns.append("current_club_name")

    if "market_value_in_eur" in ranking.columns:
        show_columns.append("market_value_in_eur")

    ranking = ranking[show_columns]

    ranking = ranking.rename(columns={
        "name": "選手名",
        "current_club_name": "クラブ",
        "market_value_in_eur": "市場価値 (€)"
    })

    if "クラブ" in ranking.columns:
        ranking["クラブ"] = ranking["クラブ"].map(
            lambda x: club_dict.get(x, x)
        )

    st.dataframe(
        ranking,
        use_container_width=True
    )

# ==========================================
# CSV閲覧
# ==========================================

with st.expander("EAFC26データを見る"):
    st.dataframe(ea)

with st.expander("Transfermarktデータを見る"):
    st.dataframe(tm)
# ==========================================
# 日本語・英語検索しやすくする
# ==========================================

st.sidebar.divider()
st.sidebar.subheader("🔍 クイック検索")

player_list = sorted(
    ea[player_column].dropna().astype(str).unique()
)

selected_player = st.sidebar.selectbox(
    "一覧から選ぶ",
    [""] + player_list
)

if selected_player != "":
    st.info(f"選択中：{selected_player}")

# ==========================================
# 市場価値TOP10グラフ
# ==========================================

st.divider()
st.header("📊 市場価値 TOP10")

if "market_value_in_eur" in tm.columns:

    top10 = (
        tm.sort_values(
            "market_value_in_eur",
            ascending=False
        )
        .head(10)
        .copy()
    )

    top10["market_value_in_eur"] = (
        top10["market_value_in_eur"] / 1_000_000
    )

    chart = top10.set_index("name")["market_value_in_eur"]

    st.bar_chart(chart)

# ==========================================
# データ件数
# ==========================================

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "EAFC26選手数",
        len(ea)
    )

with col2:
    st.metric(
        "Transfermarkt選手数",
        len(tm)
    )

# ==========================================
# ダウンロード
# ==========================================

st.divider()

st.download_button(
    "📥 EAFC26 CSVダウンロード",
    ea.to_csv(index=False).encode("utf-8-sig"),
    "EAFC26_export.csv",
    "text/csv"
)

st.download_button(
    "📥 Transfermarkt CSVダウンロード",
    tm.to_csv(index=False).encode("utf-8-sig"),
    "Transfermarkt_export.csv",
    "text/csv"
)

# ==========================================
# フッター
# ==========================================

st.divider()

st.caption(
    "EA FC26 × Transfermarkt Player Analysis System"
)

st.caption(
    "Created with Streamlit"
)

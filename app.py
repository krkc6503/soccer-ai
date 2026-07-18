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

st.title("サッカー移籍金予測AI")
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
# ページ切り替え
# ==========================================

page = st.sidebar.radio("🏠 メニュー",
[
    "ホーム",
    "選手分析",
    "ランキング",
    "データ閲覧"
]
)
# ==========================================
# ホーム画面
# ==========================================

if page == "ホーム":

    st.title("⚽ EA FC26 × Transfermarkt")
    st.subheader("選手分析システム")

    st.write("""
このアプリでは、EA FC26とTransfermarktのデータを使って
世界中のサッカー選手を分析できます。
""")

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("EA FC26登録選手数", len(ea))

    with col2:
        st.metric("Transfermarkt登録選手数", len(tm))

    st.divider()

    st.markdown("### 🚀 このアプリでできること")
    st.write("✅ 選手能力分析")
    st.write("✅ レーダーチャート")
    st.write("✅ 市場価値分析")
    st.write("✅ AIスカウトレポート")
    st.write("✅ 選手比較")
    st.write("✅ ランキング表示")

    st.info("👈 左のメニューから『選手分析』を選んで始めてください。")
    

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
if page == "選手分析":

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
# ==========================================
# 選手カード
# ==========================================

    photo_col, info_col = st.columns([1, 2])

    with photo_col:
        st.image(photo_url, width=180)
    with info_col:
        st.header(f"⭐ {row['Name']}")
        st.metric("OVR", row["OVR"])

        if "Position" in row.index:
            st.write(f"**ポジション：** {row['Position']}")

        if "Team" in row.index:
            st.write(f"**クラブ：** {row['Team']}")

        if "Nation" in row.index:
            st.write(f"**国籍：** {row['Nation']}")

    st.divider()

    st.subheader("⚡ 能力値")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("PAC", row["PAC"])
        st.metric("DRI", row["DRI"])

    with c2:
        st.metric("SHO", row["SHO"])
        st.metric("DEF", row["DEF"])

    with c3:
        st.metric("PAS", row["PAS"])
        st.metric("PHY", row["PHY"])


# ==========================================
# 移籍市場シミュレーター
# ==========================================

    st.divider()
    st.subheader("💰 移籍市場シミュレーター")

    market = info["market_value_in_eur"]
    ovr = row["OVR"]

    if ovr >= 90:
        evaluation = "🔥 ワールドクラス"
    elif ovr >= 85:
        evaluation = "⭐ トップ選手"
    elif ovr >= 80:
        evaluation = "👍 優秀な選手"
    else:
        evaluation = "📈 成長期待"

    st.write("評価：", evaluation)

    if age <= 23:
        age_text = "若手で将来性あり"
    elif age <= 29:
        age_text = "全盛期"
    else:
        age_text = "ベテランによる価値低下あり" 

    st.write("年齢評価：", age_text)

    if market / 1_000_000 >= 100:
        price_text = "高額選手"
    else:
        price_text = "手頃な価格帯"

    st.write("市場価値評価：", price_text)
# ==========================================
# レーダーチャート
# ==========================================

if player != "" and 'row' in locals():
    st.divider()

    st.subheader("📊 能力レーダーチャート")
    
    radar_stats = ["PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]
    
    values = [float(row[s]) for s in radar_stats]
    
    values += values[:1]

    angles = np.linspace(

        0,

        2*np.pi,

        len(radar_stats),

        endpoint=False

    ).tolist()

    angles += angles[:1]

    fig = plt.figure(figsize=(6,6))

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

    ax.set_ylim(0,100)

    st.pyplot(fig)

# ==========================================
# 能力値グラフ
# ==========================================

if player != "" and 'row' in locals():
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
# EAFC26 基本情報
# ==========================================

if player != "" and 'row' in locals():
    st.divider()
    st.subheader("📋 EAFC26 基本情報")

    base_info = [
    ("年齢", "Age"),
    ("身長", "Height"),
    ("体重", "Weight"),
    ("利き足", "Preferred foot"),
    ("逆足", "Weak foot"),
    ("スキル", "Skill moves"),
    ("ポジション", "Position"),
    ("国籍", "Nation"),
    ("リーグ", "League"),
    ("チーム", "Team")
    ]

    for title, col in base_info:
        if col in ea.columns:
            st.write(f"**{title}：** {row[col]}")



# ==========================================
# GK能力（GKのみ表示）
# ==========================================

gk_stats = [
    "GK Diving",
    "GK Handling",
    "GK Kicking",
    "GK Positioning",
    "GK Reflexes"
]
if player != "" and 'row' in locals():
    if all(col in ea.columns for col in gk_stats):

        if row["Position"] == "GK":

            st.divider()
            st.subheader("🧤 GK能力")

            gk_df = pd.DataFrame({
                "能力": gk_stats,
                "数値": [row[s] for s in gk_stats]
            })

            st.bar_chart(
                gk_df.set_index("能力")
            )
if page == "選手分析":
# ==========================================
# 2選手比較
# ==========================================

    st.divider()
    st.header("👥 2選手比較")

    players = sorted(
        ea["Name"].dropna().astype(str).unique()
    )

    col1, col2 = st.columns(2)

    with col1:
        player1 = st.selectbox(
            "選手①",
            players,
            key="player1"
        )

    with col2:
        player2 = st.selectbox(
            "選手②",
            players,
            index=1 if len(players) > 1 else 0,
            key="player2"
        )

    if player1 != "" and player2 != "":

        p1 = ea[ea["Name"] == player1].iloc[0]
        p2 = ea[ea["Name"] == player2].iloc[0]

        compare_stats = [
            "PAC",
            "SHO",
            "PAS",
            "DRI",
            "DEF",
            "PHY"
        ]

        compare_df = pd.DataFrame(
            {
                player1: [p1[s] for s in compare_stats],
                player2: [p2[s] for s in compare_stats]
            },
            index=compare_stats
        )

        st.dataframe(compare_df)

        st.bar_chart(compare_df.T)
    
if page == "ランキング":

# ==========================================
# 市場価値ランキング TOP20
# ==========================================
    st.divider()
    st.header("💶 市場価値ランキング TOP20")

    ranking = (
        tm.sort_values(
            "market_value_in_eur",
            ascending=False
        )
        .head(20)
        .copy()
    )

    ranking["current_club_name"] = ranking["current_club_name"].map(
        lambda x: club_dict.get(x, x)
    )

    ranking = ranking.rename(
        columns={
            "name": "選手名",
            "current_club_name": "クラブ",
            "market_value_in_eur": "市場価値 (€)"
        }
    )

    st.dataframe(
        ranking[
        [
            "選手名",
            "クラブ",
            "市場価値 (€)"
        ]
        ],
        use_container_width=True
    )

# ==========================================
# 市場価値 TOP10 グラフ
# ==========================================

    st.divider()
    st.header("📊 市場価値 TOP10")

    top10 = (
        tm.sort_values(
            "market_value_in_eur",
            ascending=False
        )
        .head(10)
        .copy()
    )

    top10["市場価値(M€)"] = (
        top10["market_value_in_eur"] / 1_000_000
    )

    chart = top10.set_index("name")["市場価値(M€)"]

    st.bar_chart(chart)
if page == "データ閲覧":
# ==========================================
# Transfermarkt 基本情報
# ==========================================

    st.divider()
    st.subheader("🌍 Transfermarktデータ")

    st.metric(
        "登録選手数",
        len(tm)
    )

    st.metric(
        "EAFC26登録選手数",
        len(ea)
    )
# ==========================================
# CSV閲覧
# ==========================================

    st.divider()
    st.header("📄 データ閲覧")

    with st.expander("EAFC26 データを見る"):
        st.dataframe(
            ea,
            use_container_width=True
        )

    with st.expander("Transfermarkt データを見る"):
        st.dataframe(
            tm,
            use_container_width=True
        )
if page == "データ閲覧":
# ==========================================
# CSVダウンロード
# ==========================================

    st.divider()
    st.header("📥 CSVダウンロード")

    col1, col2 = st.columns(2)

    with col1:

        st.download_button(
            label="EAFC26 CSV",
            data=ea.to_csv(index=False).encode("utf-8-sig"),
            file_name="EAFC26_export.csv",
            mime="text/csv"
        )

    with col2:

        st.download_button(
            label="Transfermarkt CSV",
            data=tm.to_csv(index=False).encode("utf-8-sig"),
            file_name="Transfermarkt_export.csv",
            mime="text/csv"
        )

# ==========================================
# データ件数
# ==========================================

    st.divider()
    st.header("📊 データ件数")

    c1, c2 = st.columns(2)

    with c1:
        st.metric(
            "EAFC26選手数",
            len(ea)
        )

    with c2:
        st.metric(
            "Transfermarkt選手数",
            len(tm)
        )

# ==========================================
# 列名確認（デバッグ用）
# ==========================================

    with st.expander("🛠 デバッグ情報"):

        st.write("EAFC26 Columns")
        st.write(list(ea.columns))

        st.write("Transfermarkt Columns")
        st.write(list(tm.columns))

# ==========================================
# フッター
# ==========================================

st.divider()

st.caption("⚽ EA FC26 × Transfermarkt Player Analysis System")

st.caption("Created with Streamlit")

st.success("✅ 読み込み完了")

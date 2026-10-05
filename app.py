import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime


# ==========================================
# ページ設定
# ==========================================

st.set_page_config(
    page_title="EA FC27 × Transfermarkt",
    page_icon="⚽",
    layout="wide"
)


# ==========================================
# タイトル
# ==========================================

st.title("サッカー移籍金予測AI")
st.caption("EA FC27能力値 × Transfermarkt市場価値")


# ==========================================
# データ読み込み
# ==========================================

@st.cache_data
def load_data():

    ea = pd.read_csv("EAFC27-Men(1).csv")
    tm = pd.read_csv("players_small(1).csv")

    ea.columns = ea.columns.str.strip()
    tm.columns = tm.columns.str.strip()

    return ea, tm


ea, tm = load_data()


# ==========================================
# ページ切り替え
# ==========================================

page = st.sidebar.radio(
    "🏠 メニュー",
    [
        "ホーム",
        "選手分析",
        "ランキング",
        "データ閲覧"
    ]
)


# ==========================================
# クラブ日本語辞書
# ==========================================

club_dict = {
    "Real Madrid": "レアル・マドリード",
    "FC Barcelona": "FCバルセロナ",
    "Manchester City": "マンチェスター・シティ",
    "Liverpool": "リヴァプール",
    "Arsenal": "アーセナル",
    "Chelsea": "チェルシー",
    "Manchester United": "マンチェスター・ユナイテッド",
    "Tottenham Hotspur": "トッテナム",
    "Bayern Munich": "バイエルン・ミュンヘン",
    "Borussia Dortmund": "ドルトムント",
    "Paris Saint-Germain": "パリ・サンジェルマン",
    "Inter": "インテル",
    "AC Milan": "ACミラン",
    "Juventus": "ユヴェントス",
    "Napoli": "ナポリ",
    "Atlético Madrid": "アトレティコ・マドリード"
}


# ==========================================
# ホーム
# ==========================================

if page == "ホーム":

    st.title("⚽ EA FC27 × Transfermarkt")
    st.subheader("選手分析システム")

    st.write("""
    このアプリでは、EA FC27とTransfermarktのデータを使って
    世界中のサッカー選手を分析できます。
    """)

    st.divider()

    col1, col2 = st.columns(2)

    with col1:
        st.metric("EA FC27登録選手数", len(ea))

    with col2:
        st.metric("Transfermarkt登録選手数", len(tm))

    st.divider()

    st.markdown("### 🚀 このアプリでできること")
    st.write("✅ 選手能力分析")
    st.write("✅ レーダーチャート")
    st.write("✅ 市場価値分析")
    st.write("✅ 選手比較")
    st.write("✅ ランキング表示")

    st.info("👈 左のメニューから「選手分析」を選んで始めてください。")


# ==========================================
# 検索
# ==========================================

st.sidebar.header("🔍 選手検索")

player = st.sidebar.text_input("選手名")

player_list = sorted(
    ea["Name"].dropna().astype(str).unique()
)

selected = st.sidebar.selectbox(
    "一覧から選択",
    [""] + player_list
)

if selected != "":
    player = selected


# ==========================================
# 選手分析
# ==========================================

if page == "選手分析":

    if player == "":
        st.info("👈 左側から選手を検索してください。")
        st.stop()

    result = ea[
        ea["Name"]
        .astype(str)
        .str.contains(player, case=False, na=False)
    ]

    if result.empty:
        st.error("選手が見つかりません。")
        st.stop()

    row = result.iloc[0]

    # ==========================================
    # 選手情報
    # ==========================================

    st.header(f"⭐ {row['Name']}")

    photo_col, info_col = st.columns([1, 2])

    with photo_col:

        # FC27の選手画像URLをIDから作成
        player_id = row.get("ID", "")

        image_url = ""

        if pd.notna(player_id) and str(player_id) != "":
            image_url = (
                f"https://ratings-images-prod.pulse.ea.com/"
                f"FC27/components/items/{int(float(player_id))}_en.webp"
            )

        try:
            if image_url:
                st.image(
                    image_url,
                    width=180
                )
            else:
                st.info("選手画像はありません。")
        except Exception:
            st.info("選手画像を読み込めませんでした。")

    with info_col:

        st.header(f"⭐ {row['Name']}")

        st.metric(
            "OVR",
            row["OVR"]
        )

        if "Position" in row.index:
            st.write(
                f"**ポジション：** {row['Position']}"
            )

        if "Team" in row.index:
            team_name = row["Team"]
            team_jp = club_dict.get(team_name, team_name)

            st.write(
                f"**クラブ：** {team_jp}"
            )

        if "Nation" in row.index:
            st.write(
                f"**国籍：** {row['Nation']}"
            )

        if "League" in row.index:
            st.write(
                f"**リーグ：** {row['League']}"
            )


    # ==========================================
    # 能力値
    # ==========================================

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
    # Transfermarkt
    # ==========================================

    st.divider()
    st.subheader("💰 移籍市場シミュレーター")

    tm_result = tm[
        tm["name"]
        .astype(str)
        .str.contains(
            str(row["Name"]),
            case=False,
            na=False
        )
    ]

    market = 0

    if not tm_result.empty:

        info = tm_result.iloc[0]

        try:
            market = float(
                info["market_value_in_eur"]
            )
        except Exception:
            market = 0


    # ==========================================
    # OVR評価
    # ==========================================

    try:
        ovr = float(row["OVR"])
    except Exception:
        ovr = 0


    if ovr >= 90:
        evaluation = "🔥 ワールドクラス"
    elif ovr >= 85:
        evaluation = "⭐ トップ選手"
    elif ovr >= 80:
        evaluation = "👍 優秀な選手"
    else:
        evaluation = "📈 成長期待"


    st.write("**評価：**", evaluation)


    # ==========================================
    # 年齢
    # ==========================================

    age = None

    # EA CSVにAgeが入っている場合
    if "Age" in ea.columns:

        try:
            value = row["Age"]

            if pd.notna(value) and str(value).strip() != "":
                age = float(value)

        except Exception:
            age = None


    # EA側に年齢がない場合はTransfermarktから取得
    if age is None and not tm_result.empty:

        try:

            birthday = pd.to_datetime(
                tm_result.iloc[0]["date_of_birth"],
                errors="coerce"
            )

            if pd.notna(birthday):

                today = datetime.today()

                age = (
                    today.year
                    - birthday.year
                    - (
                        (today.month, today.day)
                        <
                        (birthday.month, birthday.day)
                    )
                )

        except Exception:
            age = None


    if age is not None:

        if age <= 23:
            age_text = "若手で将来性あり"
        elif age <= 29:
            age_text = "全盛期"
        else:
            age_text = "ベテラン"

        st.write(
            f"**年齢：** {int(age)}歳"
        )

        st.write(
            "**年齢評価：**",
            age_text
        )

    else:
        st.write("**年齢：** データなし")


    # ==========================================
    # 市場価値評価
    # ==========================================

    if market >= 100_000_000:
        price_text = "💎 超高額選手"
    elif market >= 50_000_000:
        price_text = "💰 高額選手"
    elif market > 0:
        price_text = "📊 市場価値あり"
    else:
        price_text = "市場価値データなし"


    st.write(
        "**市場価値評価：**",
        price_text
    )


    if market > 0:

        st.metric(
            "Transfermarkt市場価値",
            f"€{market / 1_000_000:.1f}M"
        )


    # ==========================================
    # レーダーチャート
    # ==========================================

    st.divider()
    st.subheader("📊 能力レーダーチャート")

    radar_stats = [
        "PAC",
        "SHO",
        "PAS",
        "DRI",
        "DEF",
        "PHY"
    ]

    values = []

    for stat in radar_stats:

        try:
            value = float(row[stat])
        except Exception:
            value = 0

        values.append(value)


    values += values[:1]

    angles = np.linspace(
        0,
        2 * np.pi,
        len(radar_stats),
        endpoint=False
    ).tolist()

    angles += angles[:1]


    fig = plt.figure(figsize=(6, 6))

    ax = plt.subplot(
        111,
        polar=True
    )

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

    ax.set_xticks(
        angles[:-1]
    )

    ax.set_xticklabels(
        radar_stats
    )

    ax.set_ylim(
        0,
        100
    )

    st.pyplot(
        fig
    )

    plt.close(fig)


    # ==========================================
    # 能力値グラフ
    # ==========================================

    st.divider()
    st.subheader("📈 能力値グラフ")

    graph = pd.DataFrame({
        "能力": radar_stats,
        "数値": [
            row[s]
            for s in radar_stats
        ]
    })

    st.bar_chart(
        graph.set_index("能力")
    )


    # ==========================================
    # EAFC27基本情報
    # ==========================================

    st.divider()
    st.subheader("📋 EAFC27 基本情報")

    basic_columns = [
        ("ID", "ID"),
        ("ランキング", "Rank"),
        ("年齢", "Age"),
        ("ポジション", "Position"),
        ("国籍", "Nation"),
        ("リーグ", "League"),
        ("チーム", "Team")
    ]

    for title, column in basic_columns:

        if column in ea.columns:

            value = row[column]

            if pd.notna(value) and str(value).strip() != "":
                st.write(
                    f"**{title}：** {value}"
                )


# ==========================================
# 2選手比較
# ==========================================

if page == "選手分析":

    st.divider()
    st.header("👥 2選手比較")

    players = sorted(
        ea["Name"]
        .dropna()
        .astype(str)
        .unique()
    )

    if len(players) >= 2:

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
                index=1,
                key="player2"
            )


        p1 = ea[
            ea["Name"] == player1
        ].iloc[0]

        p2 = ea[
            ea["Name"] == player2
        ].iloc[0]


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
                player1: [
                    p1[s]
                    for s in compare_stats
                ],

                player2: [
                    p2[s]
                    for s in compare_stats
                ]
            },
            index=compare_stats
        )


        st.dataframe(
            compare_df,
            use_container_width=True
        )

        st.bar_chart(
            compare_df.T
        )


# ==========================================
# ランキング
# ==========================================

if page == "ランキング":

    st.header("💶 市場価値ランキング TOP20")

    ranking = (
        tm.sort_values(
            "market_value_in_eur",
            ascending=False
        )
        .head(20)
        .copy()
    )


    ranking["current_club_name"] = (
        ranking["current_club_name"]
        .map(
            lambda x:
            club_dict.get(x, x)
        )
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
    # TOP10グラフ
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
        top10["market_value_in_eur"]
        / 1_000_000
    )


    chart = (
        top10
        .set_index("name")
        ["市場価値(M€)"]
    )


    st.bar_chart(chart)


# ==========================================
# データ閲覧
# ==========================================

if page == "データ閲覧":

    st.header("📄 データ閲覧")

    st.subheader("EA FC27")

    st.write(
        f"登録選手数：{len(ea)}人"
    )

    with st.expander(
        "EA FC27 データを見る"
    ):

        st.dataframe(
            ea,
            use_container_width=True
        )


    st.subheader("Transfermarkt")

    st.write(
        f"登録選手数：{len(tm)}人"
    )

    with st.expander(
        "Transfermarkt データを見る"
    ):

        st.dataframe(
            tm,
            use_container_width=True
        )


    # ==========================================
    # CSVダウンロード
    # ==========================================

    st.divider()
    st.header("📥 CSVダウンロード")

    col1, col2 = st.columns(2)


    with col1:

        st.download_button(
            label="EAFC27 CSV",
            data=ea.to_csv(
                index=False
            ).encode("utf-8-sig"),
            file_name="EAFC27_export.csv",
            mime="text/csv"
        )


    with col2:

        st.download_button(
            label="Transfermarkt CSV",
            data=tm.to_csv(
                index=False
            ).encode("utf-8-sig"),
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
            "EAFC27選手数",
            len(ea)
        )

    with c2:

        st.metric(
            "Transfermarkt選手数",
            len(tm)
        )


    # ==========================================
    # デバッグ
    # ==========================================

    with st.expander(
        "🛠 デバッグ情報"
    ):

        st.write(
            "EAFC27 Columns"
        )

        st.write(
            list(ea.columns)
        )


        st.write(
            "Transfermarkt Columns"
        )

        st.write(
            list(tm.columns)
        )


# ==========================================
# フッター
# ==========================================

st.divider()

st.caption(
    "⚽ EA FC27 × Transfermarkt Player Analysis System"
)

st.caption(
    "Created with Streamlit"
)

st.success(
    "✅ 読み込み完了"
)

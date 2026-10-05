import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go


# =========================================================
# ページ設定
# =========================================================

st.set_page_config(
    page_title="EA FC27 × Transfermarkt",
    page_icon="⚽",
    layout="wide"
)


# =========================================================
# データ読み込み
# =========================================================

@st.cache_data
def load_data():

    # EA FC27
    ea = pd.read_csv(
        "EAFC27-Men(1).csv",
        encoding="utf-8-sig"
    )

    # Transfermarkt
    tm = pd.read_csv(
        "players_small(1).csv",
        encoding="utf-8-sig"
    )

    # 列名の前後の空白を削除
    ea.columns = ea.columns.astype(str).str.strip()
    tm.columns = tm.columns.astype(str).str.strip()

    # 数値列
    ea_numeric = [
        "ID",
        "Rank",
        "OVR",
        "PAC",
        "SHO",
        "PAS",
        "DRI",
        "DEF",
        "PHY",
        "Age"
    ]

    for col in ea_numeric:
        if col in ea.columns:
            ea[col] = pd.to_numeric(
                ea[col],
                errors="coerce"
            )

    # 文字列列
    for col in ea.columns:
        if ea[col].dtype == "object":
            ea[col] = ea[col].fillna("").astype(str).str.strip()

    # Transfermarktの数値列
    tm_numeric = [
        "market_value_in_eur",
        "highest_market_value_in_eur"
    ]

    for col in tm_numeric:
        if col in tm.columns:
            tm[col] = pd.to_numeric(
                tm[col],
                errors="coerce"
            )

    for col in tm.columns:
        if tm[col].dtype == "object":
            tm[col] = tm[col].fillna("").astype(str).str.strip()

    return ea, tm


# =========================================================
# データ読み込みエラー対策
# =========================================================

try:
    ea, tm = load_data()

except FileNotFoundError as e:

    st.error("❌ CSVファイルが見つかりません。")

    st.write("GitHubに次の2つのファイルがあるか確認してください。")

    st.code(
        "EAFC27-Men(1).csv\n"
        "players_small(1).csv"
    )

    st.stop()

except pd.errors.EmptyDataError:

    st.error("❌ CSVファイルの中身が空です。")

    st.stop()

except Exception as e:

    st.error("❌ データ読み込み中にエラーが発生しました。")

    st.code(str(e))

    st.stop()


# =========================================================
# 必須列チェック
# =========================================================

required_ea = [
    "Name",
    "OVR",
    "PAC",
    "SHO",
    "PAS",
    "DRI",
    "DEF",
    "PHY"
]

missing_ea = [
    col for col in required_ea
    if col not in ea.columns
]

if missing_ea:

    st.error("❌ EA FC27 CSVに必要な列がありません。")

    st.write("不足している列：")
    st.write(missing_ea)

    st.write("現在の列：")
    st.write(list(ea.columns))

    st.stop()


# =========================================================
# Transfermarkt列の確認
# =========================================================

has_tm = (
    "name" in tm.columns
    and "market_value_in_eur" in tm.columns
)


# =========================================================
# サイドバー
# =========================================================

st.sidebar.title("⚽ EA FC27")

page = st.sidebar.radio(
    "ページ",
    [
        "ホーム",
        "選手分析",
        "ランキング",
        "データ閲覧"
    ]
)


# =========================================================
# タイトル
# =========================================================

st.title("⚽ EA FC27 × Transfermarkt 選手分析アプリ")

st.caption(
    "EA FC27能力値とTransfermarkt市場価値を比較できます。"
)


# =========================================================
# 共通関数
# =========================================================

def format_money(value):

    if pd.isna(value):
        return "データなし"

    value = float(value)

    if value >= 1_000_000_000:
        return f"€{value / 1_000_000_000:.2f}B"

    if value >= 1_000_000:
        return f"€{value / 1_000_000:.1f}M"

    if value >= 1_000:
        return f"€{value / 1_000:.0f}K"

    return f"€{value:,.0f}"


def find_player(name):

    result = ea[
        ea["Name"].astype(str).str.lower()
        == str(name).lower()
    ]

    if len(result) > 0:
        return result.iloc[0]

    result = ea[
        ea["Name"].astype(str).str.contains(
            str(name),
            case=False,
            na=False
        )
    ]

    if len(result) > 0:
        return result.iloc[0]

    return None


def get_tm_player(player_name):

    if not has_tm:
        return None

    result = tm[
        tm["name"].astype(str).str.lower()
        == str(player_name).lower()
    ]

    if len(result) > 0:
        return result.iloc[0]

    result = tm[
        tm["name"].astype(str).str.contains(
            str(player_name),
            case=False,
            na=False
        )
    ]

    if len(result) > 0:
        return result.iloc[0]

    return None


def make_radar(player):

    stats = [
        "PAC",
        "SHO",
        "PAS",
        "DRI",
        "DEF",
        "PHY"
    ]

    values = []

    for stat in stats:

        value = pd.to_numeric(
            player.get(stat, 0),
            errors="coerce"
        )

        if pd.isna(value):
            value = 0

        values.append(float(value))

    values_closed = values + [values[0]]
    stats_closed = stats + [stats[0]]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values_closed,
            theta=stats_closed,
            fill="toself",
            name=str(player["Name"])
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True,
        height=450
    )

    return fig


def get_rating_level(ovr):

    try:
        ovr = float(ovr)
    except:
        return "評価不明"

    if ovr >= 90:
        return "🌟 ワールドクラス"

    if ovr >= 85:
        return "🔥 トップクラス"

    if ovr >= 80:
        return "⭐ 高能力"

    if ovr >= 75:
        return "💪 優秀"

    if ovr >= 70:
        return "👍 平均以上"

    return "⚽ 発展途上"


def scout_report(player):

    name = player["Name"]

    ovr = float(player.get("OVR", 0) or 0)
    pac = float(player.get("PAC", 0) or 0)
    sho = float(player.get("SHO", 0) or 0)
    pas = float(player.get("PAS", 0) or 0)
    dri = float(player.get("DRI", 0) or 0)
    deff = float(player.get("DEF", 0) or 0)
    phy = float(player.get("PHY", 0) or 0)

    stats = {
        "PAC": pac,
        "SHO": sho,
        "PAS": pas,
        "DRI": dri,
        "DEF": deff,
        "PHY": phy
    }

    best_stat = max(
        stats,
        key=stats.get
    )

    position = str(
        player.get("Position", "")
    )

    team = str(
        player.get("Team", "")
    )

    report = f"""
### 📝 AIスカウトレポート

**{name}** は総合値 **{ovr:.0f}** の選手です。

- ポジション：{position}
- チーム：{team}
- 最大の特徴：**{best_stat} {stats[best_stat]:.0f}**
- 評価：**{get_rating_level(ovr)}**

EA FC27の能力値を見ると、
**{best_stat}** が特に高いことが特徴です。

6つの能力値を総合すると、
この選手は現在の能力を生かしたプレーで
チームに貢献できる選手と考えられます。
"""

    return report


# =========================================================
# HOME
# =========================================================

if page == "ホーム":

    st.header("🏠 ホーム")

    st.write(
        "EA FC27の選手能力値とTransfermarktの市場価値を "
        "組み合わせて分析するアプリです。"
    )

    st.divider()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "EA FC27選手数",
            f"{len(ea):,}人"
        )

    with col2:
        if "OVR" in ea.columns:
            avg_ovr = ea["OVR"].mean()
            st.metric(
                "平均OVR",
                f"{avg_ovr:.1f}"
            )
        else:
            st.metric(
                "平均OVR",
                "-"
            )

    with col3:
        st.metric(
            "最高OVR",
            f"{ea['OVR'].max():.0f}"
        )

    st.divider()

    st.subheader("⭐ FC27 TOP10")

    top10 = (
        ea
        .sort_values("OVR", ascending=False)
        .head(10)
        .copy()
    )

    show_cols = [
        col for col in [
            "Rank",
            "Name",
            "OVR",
            "PAC",
            "SHO",
            "PAS",
            "DRI",
            "DEF",
            "PHY",
            "Team",
            "Position"
        ]
        if col in top10.columns
    ]

    st.dataframe(
        top10[show_cols],
        use_container_width=True,
        hide_index=True
    )


# =========================================================
# 選手分析
# =========================================================

elif page == "選手分析":

    st.header("🔎 選手分析")

    search = st.text_input(
        "選手名を入力",
        placeholder="例：Mohamed Salah"
    )

    if search:

        candidates = ea[
            ea["Name"].astype(str).str.contains(
                search,
                case=False,
                na=False
            )
        ].copy()

        if len(candidates) == 0:

            st.warning(
                "選手が見つかりませんでした。"
            )

        else:

            if len(candidates) > 1:

                selected_name = st.selectbox(
                    "選手を選択してください",
                    candidates["Name"].tolist()
                )

                row = candidates[
                    candidates["Name"] == selected_name
                ].iloc[0]

            else:

                row = candidates.iloc[0]

            st.divider()

            # -------------------------------------------------
            # 選手基本情報
            # -------------------------------------------------

            st.subheader(
                f"⚽ {row['Name']}"
            )

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "OVR",
                    f"{row['OVR']:.0f}"
                )

            with col2:
                st.metric(
                    "PAC",
                    f"{row['PAC']:.0f}"
                )

            with col3:
                st.metric(
                    "SHO",
                    f"{row['SHO']:.0f}"
                )

            with col4:
                st.metric(
                    "PAS",
                    f"{row['PAS']:.0f}"
                )

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "DRI",
                    f"{row['DRI']:.0f}"
                )

            with col2:
                st.metric(
                    "DEF",
                    f"{row['DEF']:.0f}"
                )

            with col3:
                st.metric(
                    "PHY",
                    f"{row['PHY']:.0f}"
                )

            with col4:
                st.metric(
                    "評価",
                    get_rating_level(row["OVR"])
                )

            st.divider()

            # -------------------------------------------------
            # 基本情報
            # -------------------------------------------------

            st.subheader("📋 基本情報")

            info_col1, info_col2 = st.columns(2)

            with info_col1:

                st.write(
                    f"**名前：** {row.get('Name', '-')}"
                )

                st.write(
                    f"**チーム：** {row.get('Team', '-')}"
                )

                st.write(
                    f"**リーグ：** {row.get('League', '-')}"
                )

                st.write(
                    f"**ポジション：** {row.get('Position', '-')}"
                )

            with info_col2:

                st.write(
                    f"**国籍：** {row.get('Nation', '-')}"
                )

                age = row.get("Age", "")

                if pd.notna(age) and str(age) != "":
                    st.write(
                        f"**年齢：** {float(age):.0f}"
                    )

                st.write(
                    f"**Rank：** #{int(row['Rank']) if pd.notna(row['Rank']) else '-'}"
                )

                st.write(
                    f"**ID：** {int(row['ID']) if pd.notna(row['ID']) else '-'}"
                )

            st.divider()

            # -------------------------------------------------
            # レーダーチャート
            # -------------------------------------------------

            st.subheader("📊 能力値レーダーチャート")

            st.plotly_chart(
                make_radar(row),
                use_container_width=True
            )

            # -------------------------------------------------
            # 能力値
            # -------------------------------------------------

            st.subheader("📈 能力値")

            stat_data = pd.DataFrame(
                {
                    "能力": [
                        "PAC",
                        "SHO",
                        "PAS",
                        "DRI",
                        "DEF",
                        "PHY"
                    ],
                    "数値": [
                        row["PAC"],
                        row["SHO"],
                        row["PAS"],
                        row["DRI"],
                        row["DEF"],
                        row["PHY"]
                    ]
                }
            )

            st.bar_chart(
                stat_data.set_index("能力")
            )

            # -------------------------------------------------
            # Transfermarkt
            # -------------------------------------------------

            st.divider()

            st.subheader(
                "💰 Transfermarkt市場価値"
            )

            tm_row = get_tm_player(
                row["Name"]
            )

            if tm_row is not None:

                market_value = tm_row.get(
                    "market_value_in_eur",
                    np.nan
                )

                highest_value = tm_row.get(
                    "highest_market_value_in_eur",
                    np.nan
                )

                col1, col2 = st.columns(2)

                with col1:

                    st.metric(
                        "現在の市場価値",
                        format_money(market_value)
                    )

                with col2:

                    st.metric(
                        "最高市場価値",
                        format_money(highest_value)
                    )

            else:

                st.info(
                    "Transfermarktに一致する選手データがありません。"
                )

            # -------------------------------------------------
            # AIスカウト
            # -------------------------------------------------

            st.divider()

            st.subheader(
                "🤖 AIスカウト"
            )

            st.markdown(
                scout_report(row)
            )

            # -------------------------------------------------
            # 画像なしの理由
            # -------------------------------------------------

            st.divider()

            st.caption(
                "※ EA FC27の画像URLは使用していません。"
                "そのため、画像URLの403エラーやcard/Image列による"
                "エラーは発生しません。"
            )


# =========================================================
# ランキング
# =========================================================

elif page == "ランキング":

    st.header("🏆 ランキング")

    ranking_type = st.selectbox(
        "ランキングを選択",
        [
            "OVR",
            "PAC",
            "SHO",
            "PAS",
            "DRI",
            "DEF",
            "PHY"
        ]
    )

    top_n = st.slider(
        "表示人数",
        min_value=5,
        max_value=50,
        value=10
    )

    ranking = (
        ea
        .sort_values(
            ranking_type,
            ascending=False
        )
        .head(top_n)
        .copy()
    )

    # 順位を追加
    ranking.insert(
        0,
        "順位",
        range(1, len(ranking) + 1)
    )

    # 重複した列があれば削除
    ranking = ranking.loc[
        :,
        ~ranking.columns.duplicated()
    ]

    # 表示する列
    cols = [
        "順位",
        "Name",
        "OVR",
        "PAC",
        "SHO",
        "PAS",
        "DRI",
        "DEF",
        "PHY",
        "Team",
        "Position",
        "Nation"
    ]

    # 存在する列だけ表示
    cols = [
        col
        for col in cols
        if col in ranking.columns
    ]

    # 念のため重複を削除
    cols = list(dict.fromkeys(cols))

    # ランキング表
    st.dataframe(
        ranking[cols],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    st.subheader(
        f"📊 {ranking_type} TOP10"
    )

    chart_data = ranking.head(10).copy()

    st.bar_chart(
        chart_data.set_index("Name")[ranking_type]
    )


# =========================================================
# データ閲覧
# =========================================================

elif page == "データ閲覧":

    st.header("📊 データ閲覧")

    st.write(
        f"現在 **{len(ea):,}人** のFC27選手データがあります。"
    )

    st.divider()

    # フィルター

    col1, col2, col3 = st.columns(3)

    with col1:

        teams = sorted(
            [
                str(x)
                for x in ea["Team"].dropna().unique()
                if str(x).strip() != ""
            ]
        )

        selected_team = st.selectbox(
            "チーム",
            ["すべて"] + teams
        )

    with col2:

        positions = sorted(
            [
                str(x)
                for x in ea["Position"].dropna().unique()
                if str(x).strip() != ""
            ]
        )

        selected_position = st.selectbox(
            "ポジション",
            ["すべて"] + positions
        )

    with col3:

        min_ovr = st.slider(
            "最低OVR",
            0,
            100,
            70
        )

    filtered = ea.copy()

    if selected_team != "すべて":

        filtered = filtered[
            filtered["Team"] == selected_team
        ]

    if selected_position != "すべて":

        filtered = filtered[
            filtered["Position"] == selected_position
        ]

    filtered = filtered[
        filtered["OVR"] >= min_ovr
    ]

    st.write(
        f"該当選手：**{len(filtered):,}人**"
    )

    display_cols = [
        col
        for col in [
            "ID",
            "Rank",
            "Name",
            "OVR",
            "PAC",
            "SHO",
            "PAS",
            "DRI",
            "DEF",
            "PHY",
            "Age",
            "Nation",
            "League",
            "Team",
            "Position"
        ]
        if col in filtered.columns
    ]

    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        hide_index=True
    )

    # CSVダウンロード

    csv_data = filtered[
        display_cols
    ].to_csv(
        index=False,
        encoding="utf-8-sig"
    )

    st.download_button(
        label="📥 表示中のデータをCSVでダウンロード",
        data=csv_data,
        file_name="FC27_filtered_players.csv",
        mime="text/csv"
    )


# =========================================================
# データ閲覧
# =========================================================

elif page == "データ閲覧":

    st.header("📊 データ閲覧")

    st.write(
        f"現在 **{len(ea):,}人** のFC27選手データがあります。"
    )

    st.divider()

    # -------------------------------------------------
    # フィルター
    # -------------------------------------------------

    col1, col2, col3 = st.columns(3)

    with col1:

        teams = sorted(
            [
                str(x)
                for x in ea["Team"].dropna().unique()
                if str(x).strip() != ""
            ]
        )

        selected_team = st.selectbox(
            "チーム",
            ["すべて"] + teams
        )

    with col2:

        positions = sorted(
            [
                str(x)
                for x in ea["Position"].dropna().unique()
                if str(x).strip() != ""
            ]
        )

        selected_position = st.selectbox(
            "ポジション",
            ["すべて"] + positions
        )

    with col3:

        min_ovr = st.slider(
            "最低OVR",
            0,
            100,
            70
        )

    filtered = ea.copy()

    if selected_team != "すべて":

        filtered = filtered[
            filtered["Team"] == selected_team
        ]

    if selected_position != "すべて":

        filtered = filtered[
            filtered["Position"] == selected_position
        ]

    filtered = filtered[
        filtered["OVR"] >= min_ovr
    ]

    st.write(
        f"該当選手：**{len(filtered):,}人**"
    )

    display_cols = [
        col for col in [
            "ID",
            "Rank",
            "Name",
            "OVR",
            "PAC",
            "SHO",
            "PAS",
            "DRI",
            "DEF",
            "PHY",
            "Age",
            "Nation",
            "League",
            "Team",
            "Position"
        ]
        if col in filtered.columns
    ]

    st.dataframe(
        filtered[display_cols],
        use_container_width=True,
        hide_index=True
    )

    # -------------------------------------------------
    # CSVダウンロード
    # -------------------------------------------------

    csv_data = filtered[display_cols].to_csv(
        index=False,
        encoding="utf-8-sig"
    )

    st.download_button(
        label="📥 表示中のデータをCSVでダウンロード",
        data=csv_data,
        file_name="FC27_filtered_players.csv",
        mime="text/csv"
    )


# =========================================================
# フッター
# =========================================================

st.divider()

st.caption(
    "EA FC27 × Transfermarkt | Player Analysis System"
)

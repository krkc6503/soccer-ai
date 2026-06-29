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

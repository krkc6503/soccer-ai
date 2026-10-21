
import os
import time
import re
import unicodedata

import requests
import pandas as pd


# =====================================
# 基本設定
# =====================================

API_URL = "https://pub-api.fcradar.gg/v1/games/fc27/players"
API_KEY = os.environ.get("FCRADAR_API_KEY")
OUTPUT_FILE = "EAFC27-Men(1).csv"

if not API_KEY:
    raise RuntimeError(
        "FCRADAR_API_KEY が設定されていません。"
    )

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}


# =====================================
# 除外するリーグ名・チーム名の単語
# =====================================

EXCLUDED_WORDS = [
    # 女子リーグ・女子チーム
    "women",
    "woman",
    "female",
    "girls",
    "girl",
    "feminine",
    "femenina",
    "frauen",
    "wsl",
    "nwsl",
    "damen",
    "arkema",

    # レジェンド・特殊カード関連
    "classic",
    "icon",
    "icons",
    "hero",
    "heroes",
    "legend",
    "legends",
    "custom",
]


# =====================================
# 共通関数
# =====================================

def get_nested(data, *keys):
    """入れ子になった辞書から値を安全に取得する。"""
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def normalize_text(value):
    """文字列を比較しやすい形式に整える。"""
    if value is None:
        return ""

    value = unicodedata.normalize("NFKC", str(value))
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)

    return " ".join(value.split())


# =====================================
# 除外判定
# =====================================

def should_exclude_player(player):
    league = get_nested(player, "league", "name") or ""
    club = get_nested(player, "club", "name") or ""

    league = str(league).strip()
    club = str(club).strip()

    # リーグとクラブが両方空欄なら除外
    if not league and not club:
        return True

    # テスト用チームを除外
    if club.lower().startswith("marketing team"):
        return True

    # リーグ名とクラブ名を検査
    text_to_check = normalize_text(
        f"{league} {club}"
    )

    words_in_name = set(text_to_check.split())

    for word in EXCLUDED_WORDS:
        normalized_word = normalize_text(word)

        # 複数単語のキーワードはフレーズで判定
        if " " in normalized_word:
            if normalized_word in text_to_check:
                return True

        # 単語単位で判定
        elif normalized_word in words_in_name:
            return True

    # 「Liga F」など、女子リーグで使われる名称
    if re.search(r"\bliga f\b", text_to_check):
        return True

    return False


# =====================================
# APIから全選手を取得
# =====================================

def fetch_all_players():
    session = requests.Session()
    session.headers.update(HEADERS)

    all_players = []
    page = 1

    while True:
        result = None

        # 最大5回まで再試行
        for attempt in range(5):
            try:
                response = session.get(
                    API_URL,
                    params={"page": page},
                    timeout=60,
                )

                response.raise_for_status()
                result = response.json()
                break

            except (
                requests.RequestException,
                ValueError,
            ) as error:
                print(
                    f"ページ {page} の取得失敗 "
                    f"({attempt + 1}/5): {error}"
                )

                if attempt < 4:
                    time.sleep(3 * (attempt + 1))
                else:
                    raise RuntimeError(
                        f"ページ {page} の取得に失敗しました。"
                    ) from error

        if not isinstance(result, dict):
            raise RuntimeError(
                f"ページ {page} のAPI応答が不正です。"
            )

        players = result.get("data", [])

        if not isinstance(players, list):
            raise RuntimeError(
                f"ページ {page} の選手データが不正です。"
            )

        all_players.extend(players)

        meta = result.get("meta") or {}
        last_page = int(meta.get("lastPage", page))

        print(
            f"ページ {page}/{last_page}: "
            f"{len(players)}人取得"
        )

        if page >= last_page:
            break

        page += 1
        time.sleep(0.5)

    return all_players


# =====================================
# メイン処理
# =====================================

def main():
    print("FC27選手データの取得を開始します。")

    all_players = fetch_all_players()

    print(
        "APIから取得した総件数:",
        len(all_players),
    )

    rows = []
    excluded_count = 0

    for player in all_players:

        # 女子リーグ・レジェンド関連・テスト用チーム等を除外
        if should_exclude_player(player):
            excluded_count += 1
            continue

        attributes = player.get("attributes") or {}

        league = (
            get_nested(player, "league", "name") or ""
        )

        club = (
            get_nested(player, "club", "name") or ""
        )

        rows.append({
            "ID": player.get("id"),
            "Rank": None,
            "Name": (
                player.get("common_name")
                or player.get("name")
            ),
            "GENDER": "Men's Football",
            "OVR": player.get("overall_rating"),
            "PAC": attributes.get("pace"),
            "SHO": attributes.get("shooting"),
            "PAS": attributes.get("passing"),
            "DRI": attributes.get("dribbling"),
            "DEF": attributes.get("defending"),
            "PHY": attributes.get("physical"),
            "Age": player.get("age"),
            "Nation": get_nested(
                player, "nation", "name"
            ),
            "League": league,
            "Team": club,
            "Position": player.get("position"),
        })

    columns = [
        "ID",
        "Rank",
        "Name",
        "GENDER",
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
        "Position",
    ]

    df = pd.DataFrame(rows, columns=columns)

    # OVRを数値として扱う
    df["OVR"] = pd.to_numeric(
        df["OVR"],
        errors="coerce",
    )

    # OVRが高い順に順位を設定
    # 同じOVRなら同順位にする
    valid_ovr = df["OVR"].notna()

    df.loc[valid_ovr, "Rank"] = (
        df.loc[valid_ovr, "OVR"]
        .rank(
            method="min",
            ascending=False,
        )
    )

    df["Rank"] = df["Rank"].astype("Int64")

    # OVRが高い順に並べる
    df = df.sort_values(
        by="OVR",
        ascending=False,
        na_position="last",
    ).reset_index(drop=True)

    # CSVを書き出す
    df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig",
    )

    print("--------------------------------")
    print("CSVを作成しました:", OUTPUT_FILE)
    print("API取得人数:", len(all_players))
    print("除外した選手数:", excluded_count)
    print("CSVの行数:", len(df))
    print("OVRが空欄の選手数:", int(df["OVR"].isna().sum()))
    print("Rankが空欄の選手数:", int(df["Rank"].isna().sum()))
    print("--------------------------------")

    print("選手データの先頭5人:")
    print(
        df.head(5).to_string(index=False)
    )


if __name__ == "__main__":
    main()

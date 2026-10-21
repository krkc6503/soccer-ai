
import os
import time
import re
import unicodedata
import requests
import pandas as pd

API_URL = "https://pub-api.fcradar.gg/v1/games/fc27/players"
API_KEY = os.environ.get("FCRADAR_API_KEY")

if not API_KEY:
    raise RuntimeError("FCRADAR_API_KEY が設定されていません")

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}

# 女子選手・レジェンド用と思われるリーグ名やクラブ名
EXCLUDED_WORDS = [
    "women",
    "woman",
    "female",
    "girls",
    "girl",
    "feminine",
    "classic",
    "icon",
    "icons",
    "hero",
    "heroes",
    "legend",
    "legends",
    "fut heroes",
    "fut icon",
    "fut icons",
    "custom",
]


def get_nested(data, *keys):
    """辞書の中から安全に入れ子の値を取得する。"""
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def normalize_text(value):
    """比較用に文字列を整える。"""
    if value is None:
        return ""
    value = unicodedata.normalize("NFKC", str(value)).lower()
    value = re.sub(r"[^a-z0-9]+", " ", value)
    return " ".join(value.split())


def should_exclude_player(player):
    """女子選手・レジェンド等の可能性が高い選手を除外する。"""
    league = get_nested(player, "league", "name") or ""
    club = get_nested(player, "club", "name") or ""

    # リーグとクラブが両方空欄の選手を除外
    if not str(league).strip() and not str(club).strip():
        return True

    text_to_check = normalize_text(f"{league} {club}")
    words_in_name = set(text_to_check.split())

    # リーグ名・クラブ名に除外語が含まれる場合
    for word in EXCLUDED_WORDS:
        normalized_word = normalize_text(word)

        if " " in normalized_word:
            if normalized_word in text_to_check:
                return True
        elif normalized_word in words_in_name:
            return True

    return False


def fetch_all_players():
    """APIから全ページを取得する。"""
    session = requests.Session()
    session.headers.update(HEADERS)

    all_players = []
    page = 1

    while True:
        result = None

        # 通信に失敗したら最大5回まで再試行
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

            except Exception as error:
                print(
                    f"ページ {page} の取得失敗 "
                    f"({attempt + 1}/5): {error}"
                )

                if attempt < 4:
                    time.sleep(3 * (attempt + 1))
                else:
                    raise

        players = result.get("data", [])
        all_players.extend(players)

        meta = result.get("meta", {})
        last_page = int(meta.get("lastPage", page))

        print(f"ページ {page}/{last_page}: {len(players)}人取得")

        if page >= last_page:
            break

        page += 1
        time.sleep(0.5)

    return all_players


def main():
    all_players = fetch_all_players()
    print("APIから取得した総件数:", len(all_players))

    rows = []
    excluded_count = 0

    for player in all_players:
        # 女子選手・レジェンド等を除外
        if should_exclude_player(player):
            excluded_count += 1
            continue

        attributes = player.get("attributes") or {}
        league = get_nested(player, "league", "name") or ""
        club = get_nested(player, "club", "name") or ""
        # テスト用チームを除外
        if club.strip().lower().startswith("marketing team"):
            excluded_count += 1
            continue

        rows.append({
            "ID": player.get("id"),
            "Rank": player.get("rank"),
            "Name": player.get("common_name") or player.get("name"),
            "GENDER": "Men's Football",
            "OVR": player.get("overall_rating"),
            "PAC": attributes.get("pace"),
            "SHO": attributes.get("shooting"),
            "PAS": attributes.get("passing"),
            "DRI": attributes.get("dribbling"),
            "DEF": attributes.get("defending"),
            "PHY": attributes.get("physical"),
            "Age": player.get("age"),
            "Nation": get_nested(player, "nation", "name"),
            "League": league,
            "Team": club,
            "Position": player.get("position"),
        })

    df = pd.DataFrame(rows)

    output_file = "EAFC27-Men(1).csv"
    df.to_csv(output_file, index=False, encoding="utf-8-sig")

    print("除外した選手数:", excluded_count)
    print("CSVを作成しました:", output_file)
    print("CSVの行数:", len(df))
    print("列名:", list(df.columns))
    print(df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()

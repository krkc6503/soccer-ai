
import os
import time
import requests
import pandas as pd

API_URL = "https://pub-api.fcradar.gg/v1/games/fc27/players"
API_KEY = os.environ.get("FCRADAR_API_KEY")

if not API_KEY:
    raise RuntimeError("FCRADAR_API_KEY が設定されていません")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
}

session = requests.Session()
session.headers.update(headers)

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

        except Exception as e:
            print(
                f"ページ {page} の取得失敗 "
                f"({attempt + 1}/5): {e}"
            )

            if attempt < 4:
                time.sleep(3 * (attempt + 1))
            else:
                raise

    players = result.get("data", [])
    all_players.extend(players)
    if page == 1:
    print("選手データの項目一覧:")
    print(list(players[0].keys()) if players else "データなし")

    meta = result.get("meta", {})
    last_page = int(meta.get("lastPage", page))

    print(f"ページ {page}/{last_page}: {len(players)}人取得")

    if page >= last_page:
        break

    page += 1
    time.sleep(0.5)

print("取得した総件数:", len(all_players))



def get_nested(data, *keys):
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data

import json

for p in all_players:
    name = str(p.get("name", ""))
    common_name = str(p.get("common_name", ""))

    if any(x in (name + common_name).lower()
           for x in ["mia hamm", "ronaldo"]):
        print("選手データ確認:")
        print(json.dumps(p, ensure_ascii=False, indent=2))
rows = []


for p in all_players:
    attributes = p.get("attributes") or {}

    league = get_nested(p, "league", "name") or ""
    club = get_nested(p, "club", "name") or ""

    # 女子リーグ・レジェンド用リーグ・クラブを除外
    excluded_words = [
        "women",
        "woman",
        "female",
        "classic",
        "icons",
        "heroes",
        "custom",
    ]

    text_to_check = (league + " " + club).lower()

    if any(word in text_to_check for word in excluded_words):
        continue

    rows.append({
        "ID": p.get("id"),
        "Name": p.get("common_name") or p.get("name"),
        "GENDER": "Men's Football",
        "OVR": p.get("overall_rating"),
        "PAC": attributes.get("pace"),
        "SHO": attributes.get("shooting"),
        "PAS": attributes.get("passing"),
        "DRI": attributes.get("dribbling"),
        "DEF": attributes.get("defending"),
        "PHY": attributes.get("physical"),
        "Age": p.get("age"),
        "Nation": get_nested(p, "nation", "name"),
        "League": league,
        "Team": club,
        "Position": p.get("position"),
    })


df = pd.DataFrame(rows)

output_file = "EAFC27-Men(1).csv"
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print("CSVを作成しました:", output_file)
print("CSVの行数:", len(df))
print("列名:", list(df.columns))
print(df.head(5).to_string(index=False))

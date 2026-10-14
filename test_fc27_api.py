
import os
import requests
import json

api_key = os.environ.get("FCRADAR_API_KEY")
if not api_key:
    raise RuntimeError("FCRADAR_API_KEY がありません")

response = requests.get(
    "https://pub-api.fcradar.gg/v1/games/fc27/players",
    headers={"Authorization": f"Bearer {api_key}"},
    params={"limit": 5},
    timeout=30,
)
print("ステータスコード:", response.status_code)
response.raise_for_status()

result = response.json()
print("JSONの最上位のキー:", list(result.keys()))

players = result.get("data", [])
print("取得できた選手数:", len(players))

for player in players[:3]:
    print(json.dumps({
        "id": player.get("id"),
        "name": player.get("name"),
        "overall_rating": player.get("overall_rating"),
        "club": player.get("club"),
        "league": player.get("league"),
    }, ensure_ascii=False))

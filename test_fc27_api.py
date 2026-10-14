
import os
import requests
import json

api_key = os.environ.get("FCRADAR_API_KEY")
if not api_key:
    raise RuntimeError("FCRADAR_API_KEY がありません")

response = requests.get(
    "https://pub-api.fcradar.gg/v1/games/fc27/players",
    headers={"Authorization": f"Bearer {api_key}"},
    params={"limit": 3},
    timeout=30,
)

print("ステータスコード:", response.status_code)
response.raise_for_status()

result = response.json()

print("メタ情報:")
print(json.dumps(result.get("meta"), ensure_ascii=False, indent=2))

print("リンク情報:")
print(json.dumps(result.get("links"), ensure_ascii=False, indent=2))

print("選手データの項目:")
players = result.get("data", [])
if players:
    print(json.dumps(players[0], ensure_ascii=False, indent=2))

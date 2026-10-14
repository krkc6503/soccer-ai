
import os
import requests

api_key = os.environ.get("FCRADAR_API_KEY")

if not api_key:
    raise RuntimeError("FCRADAR_API_KEY が設定されていません")

url = "https://pub-api.fcradar.gg/v1/games/fc27/players"

response = requests.get(
    url,
    headers={"Authorization": f"Bearer {api_key}"},
    params={"limit": 5},
    timeout=30,
)

print("ステータスコード:", response.status_code)
print(response.text[:2000])
response.raise_for_status()

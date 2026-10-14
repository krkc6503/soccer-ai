import requests

player_id = 209331

cdn_token = "YOUR_CDN_TOKEN"

url = (
    f"https://pub-api.fcradar.gg/cdn/"
    f"{cdn_token}/FC27/heads/{player_id}.png"
)

response = requests.get(url, timeout=20)

print("画像URL:", url.replace(cdn_token, "[HIDDEN]"))
print("ステータス:", response.status_code)
print("Content-Type:", response.headers.get("Content-Type"))
print("画像サイズ:", len(response.content))

if response.status_code == 200 and "image" in response.headers.get("Content-Type", ""):
    with open("salah_test.png", "wb") as f:
        f.write(response.content)
    print("画像取得成功！")
else:
    print("画像取得失敗")
    print(response.text[:300])

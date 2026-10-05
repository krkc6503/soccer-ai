import requests

player_id = 209331

urls = [
    f"https://ratings-images-prod.pulse.ea.com/FC27/full/player-portraits/p{player_id}.png",
    f"https://ratings-images-prod.pulse.ea.com/FC27/components/items/{player_id}_en.webp",
]

for i, url in enumerate(urls, 1):
    print("試しています:", url)

    r = requests.get(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
        timeout=20
    )

    print("ステータス:", r.status_code)
    print("サイズ:", len(r.content))

    if r.status_code == 200:
        with open(f"salah_test_{i}.png", "wb") as f:
            f.write(r.content)

        print("成功しました！")

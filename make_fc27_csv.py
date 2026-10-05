import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://www.ea.com/games/ea-sports-fc/ratings"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)

print("ステータスコード:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

# ページ内のtableを探す
tables = soup.find_all("table")

print("見つかったtable数:", len(tables))

if len(tables) == 0:
    print("選手データのtableが見つかりませんでした。")
    print("ページのHTMLを確認します。")
    print(response.text[:5000])
else:
    for i, table in enumerate(tables):
        try:
            df = pd.read_html(str(table))[0]

            print("table", i, "の行数:", len(df))
            print(df.head())

            # FC27の選手データらしい表を探す
            required_columns = ["OVR", "PAC", "SHO", "PAS", "DRI", "DEF", "PHY"]

            if all(col in df.columns for col in required_columns):
                df.to_csv(
                    "EAFC27-Men(1).csv",
                    index=False,
                    encoding="utf-8-sig"
                )

                print("FC27のCSVを作成しました！")
                print("行数:", len(df))
                break

        except Exception as e:
            print("table", i, "読み込み失敗:", e)

import requests
from bs4 import BeautifulSoup
import pandas as pd

url = "https://www.ea.com/games/ea-sports-fc/ratings"

response = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0"}
)

print("ステータスコード:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

# ページ内のテキストを確認
text = soup.get_text(" ", strip=True)

print(text[:5000])

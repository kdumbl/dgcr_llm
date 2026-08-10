import requests
from bs4 import BeautifulSoup

url_thread = "https://www.dgcoursereview.com/threads/turning-the-key-as-part-of-elbow-unbending-vs-with-the-wrist.182494/"
url_forum = "https://www.dgcoursereview.com/forums/technique-strategy.52/"

headers = {
    "User-Agent": "Mozilla/5.0 (compatible; ResearchBot/1.0)"
}

response = requests.get(url_thread, headers=headers, timeout=20)
response.raise_for_status()

soup = BeautifulSoup(response.text, "lxml")

print(soup.title.get_text(strip=True))

with open("thread_long.html", "w", encoding="utf-8") as f:
    f.write(response.text)
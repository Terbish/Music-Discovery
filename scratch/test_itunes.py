import requests
import json

def test_itunes(artist, title):
    url = "https://itunes.apple.com/search"
    params = {
        "term": f"{artist} {title}",
        "entity": "song",
        "limit": 1
    }
    resp = requests.get(url, params=params)
    if resp.status_code == 200:
        data = resp.json()
        if data["resultCount"] > 0:
            result = data["results"][0]
            print(f"Found: {result.get('artistName')} - {result.get('trackName')}")
            print(f"Genre: {result.get('primaryGenreName')}")
            return result.get('primaryGenreName')
    print("Not found")
    return None

print("Testing Japanese track (Romanji):")
test_itunes("YOASOBI", "Yoru ni Kakeru")

print("\nTesting Japanese track (Kanji):")
test_itunes("YOASOBI", "夜に駆ける")

print("\nTesting Chinese track:")
test_itunes("Jay Chou", "晴天")

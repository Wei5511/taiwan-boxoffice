import requests

try:
    r = requests.get("http://127.0.0.1:8000/movies", params={"country": "其他", "limit": 1})
    data = r.json()
    print("API RESPONSE:")
    import json
    print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error testing API: {e}")

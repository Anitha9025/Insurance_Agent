import urllib.request
import json

def test_claims():
    url = "http://127.0.0.1:8000/api/v1/claims"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            print(f"SUCCESS! Retrieved {len(data)} claims from backend.")
            for c in data[:3]:
                print(f" - {c['claim_number']}: {c['title']} (${c['claim_amount']})")
    except urllib.error.HTTPError as err:
        print(f"HTTP Error {err.code}: {err.read().decode()}")

if __name__ == "__main__":
    test_claims()

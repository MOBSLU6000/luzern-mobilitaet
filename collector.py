import json
import os
import urllib.request
from datetime import datetime, timezone

PARKING_API = "https://pls.ch/api/v1/parkings/lucerne"
NEXTBIKE_API = "https://api.nextbike.net/maps/nextbike-live.json?city=252"
DATA_FILE = "data.json"

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def main():
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Fetch Parking
    parking_raw = fetch_json(PARKING_API)
    parking_list = []
    if parking_raw and isinstance(parking_raw, list):
        for item in parking_raw:
            parking_list.append({
                "id": str(item.get("id", item.get("title"))),
                "title": item.get("title", item.get("name", "Parkhaus")),
                "free": int(item.get("free", 0)),
                "total": int(item.get("total", 100))
            })

    # Fetch Nextbike
    nextbike_raw = fetch_json(NEXTBIKE_API)
    nextbike_list = []
    if nextbike_raw and isinstance(nextbike_raw, dict):
        countries = nextbike_raw.get("countries", [])
        if countries:
            cities = countries[0].get("cities", [])
            if cities:
                places = cities[0].get("places", [])
                for p in places:
                    nextbike_list.append({
                        "id": str(p.get("uid")),
                        "name": p.get("name"),
                        "lat": p.get("lat"),
                        "lng": p.get("lng"),
                        "bikes": int(p.get("bikes", 0)),
                        "free_racks": int(p.get("free_racks", 0))
                    })

    # Create Entry
    entry = {
        "timestamp": timestamp,
        "parking": parking_list,
        "nextbike": nextbike_list
    }

    # Append to History
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []

    history.append(entry)
    # Keep last 3000 snapshots (~3 weeks of 10-min intervals)
    history = history[-3000:]

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print(f"Data successfully updated at {timestamp}")

if __name__ == "__main__":
    main()

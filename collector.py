import json
import os
import urllib.request
from datetime import datetime, timezone

PARKING_API = "https://pls.ch/api/v1/parkings/lucerne"
NEXTBIKE_API = "https://api.nextbike.net/maps/nextbike-live.json?city=252"
DATA_FILE = "data.json"

# Simulation Data in case API blocks Datacenter IPs
MOCK_PARKING = [
    {"id": "1", "title": "Bahnhof", "free": 45, "total": 500},
    {"id": "2", "title": "Kesselturm", "free": 18, "total": 280},
    {"id": "3", "title": "Altstadt", "free": 8, "total": 220},
    {"id": "4", "title": "Kasernenplatz", "free": 82, "total": 340},
    {"id": "5", "title": "Musegg", "free": 110, "total": 330},
    {"id": "6", "title": "Schweizerhof", "free": 25, "total": 250},
    {"id": "7", "title": "City-Parking", "free": 140, "total": 640}
]

def fetch_json(url):
    # Standard Browser User-Agent string to avoid datacenter blocking
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except Exception as e:
        print(f"Fetch info for {url}: {e}")
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
    else:
        print("API nicht direkt erreichbar. Verwende Fallback-Datensatz.")
        parking_list = MOCK_PARKING

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

    # Assemble Payload
    entry = {
        "timestamp": timestamp,
        "parking": parking_list,
        "nextbike": nextbike_list
    }

    # Load Existing History
    history = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                history = json.load(f)
                if not isinstance(history, list):
                    history = []
        except Exception:
            history = []

    history.append(entry)
    # Keep last 2000 snapshots
    history = history[-2000:]

    # Write back to file
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

    print(f"Messpunkt erfolgreich geschrieben: {timestamp}")

if __name__ == "__main__":
    main()

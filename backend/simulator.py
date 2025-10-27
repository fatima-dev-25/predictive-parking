# backend/simulator.py
import requests, time, random, os
from dotenv import load_dotenv
load_dotenv()

BASE = os.getenv('BACKEND_BASE', 'http://127.0.0.1:5000')

def get_lots():
    r = requests.get(f'{BASE}/api/parking_lots')
    return r.json()

def simulate():
    while True:
        lots = get_lots()
        
        for l in lots:
            total = l['total_slots']
            # create rush-hour like behavior: random occupancy around 50-95%
            hour = time.localtime().tm_hour
            if 8 <= hour <= 11 or 17 <= hour <= 20:
                base = 0.8
            else:
                base = 0.5
            occupied = min(total, max(0, int(total * (base + (random.random()-0.5)*0.2))))
            # push update
            requests.post(f'{BASE}/api/parking_lots/{l["id"]}/update-occupancy', json={'occupied': occupied})
            print(f"Updated lot {l['id']} occupied={occupied}")
            time.sleep(0.5)
        time.sleep(10)

if __name__ == '__main__':
    simulate()

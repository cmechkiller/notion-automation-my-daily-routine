import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DAILY_ROUTINE_DB_ID = os.getenv("DAILY_ROUTINE_DB_ID")

API_BASE = "https://api.notion.com/v1"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def safe_get(url):
    r = requests.get(url, headers=HEADERS)
    if not r.ok:
        print(f"❌ GET {url} failed: {r.status_code} {r.text}")
        return None
    return r.json()

def fetch_supporting_dbs(daily_routine_db_id):
    url = f"{API_BASE}/databases/{daily_routine_db_id}"
    res = safe_get(url)
    if not res:
        return {}

    supporting_dbs = {}
    for name, prop in res["properties"].items():
        if prop["type"] == "relation":
            supporting_dbs[name] = prop["relation"]["database_id"]

    print("🔗 Supporting DBs found:", supporting_dbs)
    return supporting_dbs

def inspect_db(db_id, name):
    url = f"{API_BASE}/databases/{db_id}"
    res = safe_get(url)
    if not res:
        return
    print(f"\n📂 {name} ({db_id}) properties:")
    for prop_name, prop in res["properties"].items():
        print(f"  - {prop_name}: {prop['type']}")

if __name__ == "__main__":
    if not DAILY_ROUTINE_DB_ID:
        print("❌ DAILY_ROUTINE_DB_ID not set in .env")
        exit(1)

    supporting_dbs = fetch_supporting_dbs(DAILY_ROUTINE_DB_ID)
    for name, db_id in supporting_dbs.items():
        inspect_db(db_id, name)

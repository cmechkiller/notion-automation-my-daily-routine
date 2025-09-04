import os
import requests
from dotenv import load_dotenv

# --- Load env ---
load_dotenv()
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
MONTHLY_SUMMARY_DB_ID = os.getenv("MONTHLY_SUMMARY_DB_ID")
DAILY_ROUTINE_DB_ID = os.getenv("DAILY_ROUTINE_DB_ID")

API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}

# --- Helpers ---
def safe_get(url):
    r = requests.get(url, headers=HEADERS)
    if not r.ok:
        print(f"❌ GET {url} failed: {r.status_code} {r.text}")
        return None
    return r.json()

def safe_patch(url, payload):
    r = requests.patch(url, headers=HEADERS, json=payload)
    if not r.ok:
        print(f"❌ PATCH {url} failed: {r.status_code} {r.text}")
        return None
    return r.json()

# --- Fetch supporting DBs ---
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

# --- Inspect DB properties ---
def inspect_db(db_id, label=""):
    url = f"{API_BASE}/databases/{db_id}"
    res = safe_get(url)
    if not res:
        return {}
    props = {name: prop["type"] for name, prop in res["properties"].items()}
    print(f"\n📂 {label} ({db_id}) properties:")
    for n, t in props.items():
        print(f"  - {n}: {t}")
    return res["properties"]

# --- Update Monthly Summary with emoji-friendly rollups ---
def update_monthly_summary(summary_db_id, supporting_dbs):
    payload = {"properties": {}}

    # Books
    if "Books" in supporting_dbs:
        props = inspect_db(supporting_dbs["Books"], "Books")
        if "Completed" in props:
            payload["properties"]["📚 Books Completed %"] = {
                "rollup": {
                    "relation_property_name": "Books",
                    "rollup_property_name": "Completed",
                    "function": "percent_checked",
                }
            }
            payload["properties"]["📚 Books In Progress %"] = {
                "rollup": {
                    "relation_property_name": "Books",
                    "rollup_property_name": "Completed",
                    "function": "percent_unchecked",
                }
            }

    # Podcasts
    if "Podcasts" in supporting_dbs:
        props = inspect_db(supporting_dbs["Podcasts"], "Podcasts")
        if "Listened" in props:
            payload["properties"]["🎧 Podcasts Completed %"] = {
                "rollup": {
                    "relation_property_name": "Podcasts",
                    "rollup_property_name": "Listened",
                    "function": "percent_checked",
                }
            }
            payload["properties"]["🎧 Podcasts In Progress %"] = {
                "rollup": {
                    "relation_property_name": "Podcasts",
                    "rollup_property_name": "Listened",
                    "function": "percent_unchecked",
                }
            }

    # Recipes
    if "Recipes" in supporting_dbs:
        props = inspect_db(supporting_dbs["Recipes"], "Recipes")
        if "Tried" in props:
            payload["properties"]["🍳 Recipes Tried %"] = {
                "rollup": {
                    "relation_property_name": "Recipes",
                    "rollup_property_name": "Tried",
                    "function": "percent_checked",
                }
            }

    # Exercise
    if "Exercise" in supporting_dbs:
        props = inspect_db(supporting_dbs["Exercise"], "Exercise")
        if "Calories Burned" in props:
            payload["properties"]["🏋️ Exercise Calories"] = {
                "rollup": {
                    "relation_property_name": "Exercise",
                    "rollup_property_name": "Calories Burned",
                    "function": "sum",
                }
            }

    # Monthly Budget
    if "Monthly Budget" in supporting_dbs:
        props = inspect_db(supporting_dbs["Monthly Budget"], "Monthly Budget")
        if "Spent" in props:
            payload["properties"]["💰 Budget Spent"] = {
                "rollup": {
                    "relation_property_name": "Monthly Budget",
                    "rollup_property_name": "Spent",
                    "function": "sum",
                }
            }

    if not payload["properties"]:
        print("⚠️ No rollups to update.")
        return

    url = f"{API_BASE}/databases/{summary_db_id}"
    res = safe_patch(url, payload)
    if res:
        print(f"✅ Updated Monthly Summary DB {summary_db_id} with rollups")

# --- Main ---
def main():
    if not MONTHLY_SUMMARY_DB_ID or not DAILY_ROUTINE_DB_ID:
        print("❌ Missing env vars: MONTHLY_SUMMARY_DB_ID or DAILY_ROUTINE_DB_ID")
        return

    supporting_dbs = fetch_supporting_dbs(DAILY_ROUTINE_DB_ID)
    if not supporting_dbs:
        print("❌ Could not fetch supporting DBs")
        return

    update_monthly_summary(MONTHLY_SUMMARY_DB_ID, supporting_dbs)

if __name__ == "__main__":
    main()

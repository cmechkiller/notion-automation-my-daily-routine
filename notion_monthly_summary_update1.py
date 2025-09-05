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

# --- Update Monthly Summary safely ---
def update_monthly_summary(summary_db_id, supporting_dbs):
    # Fetch existing properties so we don't duplicate
    url = f"{API_BASE}/databases/{summary_db_id}"
    res = safe_get(url)
    if not res:
        return
    existing_props = res["properties"].keys()

    payload = {"properties": {}}

    # Books
    if "Books" in supporting_dbs:
        props = inspect_db(supporting_dbs["Books"], "Books")
        if "Completed" in props:
            if "📚 Books Completed %" not in existing_props:
                payload["properties"]["📚 Books Completed %"] = {
                    "rollup": {
                        "relation_property_name": "Books",
                        "rollup_property_name": "Completed",
                        "function": "percent_checked",
                    }
                }
            if "📚 Books In Progress %" not in existing_props:
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
            if "🎧 Podcasts Completed %" not in existing_props:
                payload["properties"]["🎧 Podcasts Completed %"] = {
                    "rollup": {
                        "relation_property_name": "Podcasts",
                        "rollup_property_name": "Listened",
                        "function": "percent_checked",
                    }
                }
            if "🎧 Podcasts In Progress %" not in existing_props:
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
            if "🍳 Recipes Tried %" not in existing_props:
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
            if "🏋️ Exercise Calories" not in existing_props:
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
            if "💰 Budget Spent" not in existing_props:
                payload["properties"]["💰 Budget Spent"] = {
                    "rollup": {
                        "relation_property_name": "Monthly Budget",
                        "rollup_property_name": "Spent",
                        "function": "sum",
                    }
                }

    if not payload["properties"]:
        print("⚠️ No new rollups to add. Already up-to-date ✅")
        return

    res = safe_patch(url, payload)
    if res:
        print(f"✅ Updated Monthly Summary DB {summary_db_id} with new rollups (no duplicates)")


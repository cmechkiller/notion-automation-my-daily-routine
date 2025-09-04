import os
import requests
from datetime import datetime
from dotenv import load_dotenv

# Load .env file if available
load_dotenv()

# -------------------------------
# Config
# -------------------------------
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")

API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}


# -------------------------------
# Helpers
# -------------------------------
def safe_post(url, json_payload):
    try:
        r = requests.post(url, headers=HEADERS, json=json_payload)
        if not r.ok:
            print(f"❌ POST {url} failed: {r.status_code} {r.text}")
            return {}
        return r.json()
    except Exception as e:
        print(f"❌ Exception on POST {url}: {e}")
        return {}


# -------------------------------
# DB Creation
# -------------------------------
def create_supporting_db(NOTION_PAGE_ID, name, props):
    payload = {
        "parent": {"page_id": NOTION_PAGE_ID},
        "title": [{"type": "text", "text": {"content": name}}],
        "properties": {
            "Name": {"title": {}},
            **props
        }
    }
    res = safe_post(f"{API_BASE}/databases", payload)
    if "id" in res:
        print(f"✅ Created DB: {name} -> {res['id']}")
        return res["id"]
    else:
        print(f"❌ Failed to create DB: {name}")
        return None


def create_all_supporting(NOTION_PAGE_ID):
    books_id = create_supporting_db(NOTION_PAGE_ID, "Books", {
        "Author": {"rich_text": {}},
        "Completed": {"checkbox": {}},
    })
    podcasts_id = create_supporting_db(NOTION_PAGE_ID, "Podcasts", {
        "Host": {"rich_text": {}},
        "Listened": {"checkbox": {}},
    })
    recipes_id = create_supporting_db(NOTION_PAGE_ID, "Recipes", {
        "Ingredients": {"rich_text": {}},
        "Tried": {"checkbox": {}},
    })
    exercise_id = create_supporting_db(NOTION_PAGE_ID, "Exercise", {
        "Duration (min)": {"number": {"format": "number"}},
        "Calories Burned": {"number": {"format": "number"}},
    })
    budget_id = create_supporting_db(NOTION_PAGE_ID, "Monthly Budget", {
        "Budget": {"number": {"format": "number"}},
        "Spent": {"number": {"format": "number"}},
    })

    return {
        "Books": books_id,
        "Podcasts": podcasts_id,
        "Recipes": recipes_id,
        "Exercise": exercise_id,
        "Monthly Budget": budget_id,
    }


def create_daily_db(parent_page_id, supporting_dbs):
    payload = {
        "parent": {"page_id": parent_page_id},
        "title": [{"type": "text", "text": {"content": "Daily Routine"}}],
        "properties": {
            "Name": {"title": {}},
            "Date": {"date": {}},
            "Mood": {"select": {"options": [
                {"name": "Happy", "color": "green"},
                {"name": "Neutral", "color": "blue"},
                {"name": "Sad", "color": "red"},
            ]}},
            "Notes": {"rich_text": {}},
            "Books": {
                "relation": {
                    "database_id": supporting_dbs["Books"],
                    "type": "dual_property",
                    "dual_property": {}
                }
            },
            "Podcasts": {
                "relation": {
                    "database_id": supporting_dbs["Podcasts"],
                    "type": "dual_property",
                    "dual_property": {}
                }
            },
            "Recipes": {
                "relation": {
                    "database_id": supporting_dbs["Recipes"],
                    "type": "dual_property",
                    "dual_property": {}
                }
            },
            "Exercise": {
                "relation": {
                    "database_id": supporting_dbs["Exercise"],
                    "type": "dual_property",
                    "dual_property": {}
                }
            },
            "Monthly Budget": {
                "relation": {
                    "database_id": supporting_dbs["Monthly Budget"],
                    "type": "dual_property",
                    "dual_property": {}
                }
            },
            "Expense": {"number": {"format": "number"}},
        }
    }
    res = safe_post(f"{API_BASE}/databases", payload)
    if "id" in res:
        print(f"✅ Created DB: Daily Routine -> {res['id']}")
        return res["id"]
    else:
        print(f"❌ Failed to create Daily Routine DB.")
        return None



# -------------------------------
# Daily Entry Creation
# -------------------------------
def create_daily_entry_if_missing(daily_db, supporting_dbs):
    today = datetime.today().strftime("%Y-%m-%d")
    month_str = datetime.today().strftime("%B %Y")  # e.g., "September 2025"

    # Step A: Ensure Monthly Budget row exists
    monthly_budget_id = supporting_dbs.get("Monthly Budget")
    monthly_budget_page_id = None
    if monthly_budget_id:
        query = {
            "database_id": monthly_budget_id,
            "filter": {
                "property": "Name",
                "title": {"equals": month_str}
            }
        }
        res = requests.post(f"{API_BASE}/databases/{monthly_budget_id}/query", headers=HEADERS, json=query)
        data = res.json()

        if "results" in data and len(data["results"]) > 0:
            monthly_budget_page_id = data["results"][0]["id"]
        else:
            payload = {
                "parent": {"database_id": monthly_budget_id},
                "properties": {
                    "Name": {"title": [{"text": {"content": month_str}}]},
                    "Budget": {"number": 0},
                    "Spent": {"number": 0},
                }
            }
            res_new = safe_post(f"{API_BASE}/pages", payload)
            if "id" in res_new:
                monthly_budget_page_id = res_new["id"]
                print(f"✅ Created Monthly Budget row for {month_str}")

    # Step B: Create today’s Daily Routine entry
    page_data = {
        "parent": {"database_id": daily_db},
        "properties": {
            "Name": {"title": [{"text": {"content": f"Daily Routine - {today}"}}]},
            "Date": {"date": {"start": today}},
            "Mood": {"select": {"name": "Neutral"}},
            "Notes": {"rich_text": [{"text": {"content": ""}}]},
            "Expense": {"number": 0},
        }
    }

    if monthly_budget_page_id:
        page_data["properties"]["Monthly Budget"] = {
            "relation": [{"id": monthly_budget_page_id}]
        }

    res = safe_post(f"{API_BASE}/pages", page_data)
    if "id" in res:
        print(f"✅ Created today's Daily Routine entry: {res['id']}")
    else:
        print(f"❌ Create page failed: {res}")


# -------------------------------
# Main
# -------------------------------
def main():
    print("🔧 Starting Notion Daily Routine setup...")

    dbs = create_all_supporting(NOTION_PAGE_ID)
    daily_db = create_daily_db(NOTION_PAGE_ID, dbs)

    if daily_db:
        create_daily_entry_if_missing(daily_db, dbs)

    print("🎉 Done. Check your Notion workspace for new databases and today's entry.")


if __name__ == "__main__":
    if not NOTION_API_KEY or not NOTION_PAGE_ID:
        print("❌ Environment variables missing. Please set NOTION_API_KEY and NOTION_PAGE_ID.")
    else:
        main()

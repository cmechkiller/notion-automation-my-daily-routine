import os
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_PAGE_ID = os.getenv("NOTION_PAGE_ID")
API_BASE = "https://api.notion.com/v1"

HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

def safe_post(url, payload):
    res = requests.post(url, headers=HEADERS, json=payload)
    if not res.ok:
        print(f"❌ POST {url} failed: {res.status_code} {res.text}")
        return None
    return res.json()

def create_base_summary_db(notion_page_id, supporting_dbs):
    relation_properties = {}
    for name, db_id in supporting_dbs.items():
        relation_properties[name] = {
            "relation": {
                "database_id": db_id,
                "type": "single_property",   # 👈 REQUIRED
                "single_property": {}        # 👈 REQUIRED (empty object is fine)
            }
        }

    payload = {
        "parent": {"type": "page_id", "page_id": notion_page_id},
        "title": [{"type": "text", "text": {"content": "Monthly Summary"}}],
        "properties": {
            "Name": {"title": {}},   # required
            "Month": {"date": {}},
            "Category": {"select": {}},
            **relation_properties,
        },
    }

    res = safe_post(f"{API_BASE}/databases", payload)
    if not res:
        return None

    summary_db_id = res["id"]
    print(f"✅ Created Monthly Summary DB: {summary_db_id}")
    return summary_db_id


if __name__ == "__main__":
    supporting_dbs = {
        "Recipes": "2634009d-7e27-8159-90fe-d88ed57042ba",
        "Exercise": "2634009d-7e27-814d-bce1-fa83e492e752",
        "Books": "2634009d-7e27-8194-9928-e10dca0a4311",
        "Monthly Budget": "2634009d-7e27-810d-93ef-cef6629c8ef2",
        "Podcasts": "2634009d-7e27-81b9-8aca-d9677c93b57d"
    }

    db_id = create_base_summary_db(NOTION_PAGE_ID, supporting_dbs)
    if db_id:
        print("🎉 Base DB created successfully. Next step: update script for rollups.")

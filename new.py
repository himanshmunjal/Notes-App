from pymongo import MongoClient

# === CONNECT TO YOUR DATABASE ===
# (replace with your Atlas connection string)
conn = MongoClient("mongodb+srv://<your_db_username>:<your_db_paaword>@cluster0.rgxv77e.mongodb.net/")
db = conn["notes"]
collection = db["notes"]

# === FETCH EXISTING NOTES ===
docs = list(collection.find({}))

if not docs:
    print("⚠️ No documents found! Your collection is empty.")
else:
    print(f"✅ Found {len(docs)} existing notes. Normalizing fields...")

# === NORMALIZE EACH DOCUMENT ===
for i, doc in enumerate(docs, start=1):
    update_fields = {}

    # Serial number (auto-increment)
    update_fields["serial"] = i

    # Title
    if "title" not in doc or not doc["title"]:
        update_fields["title"] = f"Untitled Note {i}"

    # Note content
    if "note" not in doc or not doc["note"]:
        update_fields["note"] = "No description provided."

    # Importance
    if "important" not in doc:
        update_fields["important"] = False

    # Category
    if "category" not in doc or not doc["category"]:
        update_fields["category"] = "Uncategorized"

    # Tags
    if "tags" not in doc or not isinstance(doc["tags"], list):
        update_fields["tags"] = []

    # Apply update
    if update_fields:
        collection.update_one({"_id": doc["_id"]}, {"$set": update_fields})

print("✅ All documents normalized successfully!")

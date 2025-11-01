from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pymongo import MongoClient
from bson import ObjectId
from dotenv import load_dotenv
import certifi, os

# Load environment variables from .env file
load_dotenv()

# MongoDB connection using Atlas (secure TLS)
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("❌ MONGO_URI not found in environment variables!")

client = MongoClient(MONGO_URI, tls=True, tlsCAFile=certifi.where())
db = client["notes"]
collection = db["notes"]

# Create indexes for faster lookup
collection.create_index("serial", unique=True)
collection.create_index("title")
collection.create_index("category")

# FastAPI setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Helper function to generate next serial number
def get_next_serial():
    last_note = collection.find_one(sort=[("serial", -1)])
    return (last_note["serial"] + 1) if last_note else 1

# ---------- ROUTES ----------

@app.get("/", response_class=HTMLResponse)
async def read_notes(request: Request):
    docs = collection.find({}).sort([("important", -1), ("serial", 1)])
    newDocs = [
        {
            "id": str(doc["_id"]),
            "serial": doc.get("serial"),
            "title": doc.get("title"),
            "note": doc.get("note"),
            "important": doc.get("important", False),
            "category": doc.get("category", "Uncategorized"),
            "tags": doc.get("tags", [])
        }
        for doc in docs
    ]
    return templates.TemplateResponse("index.html", {"request": request, "newDocs": newDocs})

@app.post("/", response_class=HTMLResponse)
async def add_note(
    title: str = Form(...),
    note: str = Form(...),
    category: str = Form("Uncategorized"),
    tags: str = Form(""),
    important: bool = Form(False)
):
    try:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]
        new_note = {
            "serial": get_next_serial(),
            "title": title,
            "note": note,
            "important": important,
            "category": category,
            "tags": tags_list
        }
        collection.insert_one(new_note)
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database insertion error: {str(e)}")

@app.post("/delete/{note_id}", response_class=HTMLResponse)
async def delete_note(note_id: str):
    try:
        collection.delete_one({"_id": ObjectId(note_id)})
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete error: {str(e)}")

@app.get("/edit/{note_id}", response_class=HTMLResponse)
async def edit_note_page(request: Request, note_id: str):
    note = collection.find_one({"_id": ObjectId(note_id)})
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return templates.TemplateResponse("edit.html", {"request": request, "note": note, "note_id": note_id})

@app.post("/update/{note_id}", response_class=HTMLResponse)
async def update_note(
    note_id: str,
    title: str = Form(...),
    note: str = Form(...),
    category: str = Form("Uncategorized"),
    tags: str = Form(""),
    important: bool = Form(False)
):
    try:
        tags_list = [t.strip() for t in tags.split(",") if t.strip()]
        collection.update_one(
            {"_id": ObjectId(note_id)},
            {"$set": {
                "title": title,
                "note": note,
                "important": important,
                "category": category,
                "tags": tags_list
            }}
        )
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update error: {str(e)}")

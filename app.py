# app.py
import os
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, Request  # <--- שינוי: הוספנו Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles 
from pydantic import BaseModel
from groq import Groq
import logic
from dotenv import load_dotenv
from posthog import Posthog
from fastapi import FastAPI, BackgroundTasks, Request, HTTPException

current_dir = Path(__file__).parent
env_path = current_dir / ".env"

load_dotenv(dotenv_path=env_path)

# Uses GROQ_API_KEY_1 to match your rotation setup configuration
client = Groq(api_key=os.getenv("GROQ_API_KEY_1"))

# אתחול פוסטהוג - ודא שאתה מוסיף את ה-POSTHOG_API_KEY לקובץ ה-.env שלך
posthog = Posthog(project_api_key=os.getenv("POSTHOG_API_KEY"), host='https://eu.posthog.com')

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory=current_dir / "cocktail_images"), name="images")

@app.get("/")
async def serve_index():
    return FileResponse(current_dir / "index.html")

@app.get("/script.js")
async def serve_script():
    return FileResponse(current_dir / "script.js")

@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse(current_dir / "manifest.json")

bm25_data = logic.load_bm25_index()

# מודל הבקשה המעודכן המפריד בין משקה הבסיס לשאר המרכיבים
class ChatRequest(BaseModel):
    base_spirits: list = []
    other_ingredients: list = []
    flavor: str = "All"
    history: list = []
    session_id: str = "anonymous_session"

# פונקציית רקע לשליחת אירועי חיפוש מוצלחים
def track_search_event(session_id: str, message: str, history_len: int, client_ip: str, match_type: str):
    try:
        posthog.capture(
            distinct_id=session_id,
            event="cocktail_search",
            properties={
                "$ip": client_ip,  # מעביר את ה-IP האמיתי לפוסטהוג לצורך הפקת מיקום גאוגרפי
                "search_term": message,
                "chat_history_length": history_len,
                "match_type": match_type  # שומר את סוג ההתאמה (מדויק, spell-checker וכו')
            }
        )
    except Exception as e:
        print(f"⚠️ Error logging to PostHog: {e}")

# פונקציית רקע לשליחת אירועים שבהם לא נמצא מתכון
def track_failed_search_event(session_id: str, message: str, client_ip: str):
    try:
        posthog.capture(
            distinct_id=session_id,
            event="cocktail_search_failed",
            properties={
                "$ip": client_ip,
                "missing_recipe_term": message
            }
        )
    except Exception as e:
        print(f"⚠️ Error logging failed search to PostHog: {e}")

@app.post("/chat")
async def chat_endpoint(request_data: ChatRequest, request: Request, background_tasks: BackgroundTasks):
    client_ip = request.client.host 

    # העברת המשתנים המופרדים ללוגיקה
    context, match_type = logic.retrieve_candidates(
        bm25_data, 
        request_data.base_spirits,
        request_data.other_ingredients,
        request_data.flavor, 
        top_k=4
    )

    exact_message = f"Base: {request_data.base_spirits}, Other: {request_data.other_ingredients}, Flavor: {request_data.flavor}"

    if context is None:
        background_tasks.add_task(track_failed_search_event, request_data.session_id, exact_message, client_ip)
        # זורקים שגיאת 404 כדי שהדפדפן יפעיל את הטיפול בשגיאות ויציג הודעה נקייה למשתמש
        raise HTTPException(status_code=404, detail="No matching recipes found.")
    background_tasks.add_task(
        track_search_event, 
        request_data.session_id, 
        exact_message, 
        len(request_data.history), 
        client_ip,
        match_type
    )

    return StreamingResponse(
        logic.stream_llm_response(client, exact_message, context, request_data.history, match_type),
        media_type="text/plain"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from groq import Groq
import logic
from dotenv import load_dotenv

# 1. מציאת הנתיב המדויק של התיקייה שבה נמצא הקובץ app.py
current_dir = Path(__file__).parent
env_path = current_dir / ".env"

# 2. טעינת קובץ ה-.env מהנתיב שחישבנו
load_dotenv(dotenv_path=env_path)

# 3. טעינת המפתח מתוך משתני הסביבה (במקום מ-Streamlit)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

app = FastAPI()

# הגדרת CORS כדי שה-JavaScript יוכל לגשת לשרת
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- הגשת קבצים סטטיים ---
@app.get("/")
async def serve_index():
    return FileResponse(current_dir / "index.html")

@app.get("/script.js")
async def serve_script():
    return FileResponse(current_dir / "script.js")

# טעינת נתוני ה-BM25 פעם אחת עם עליית השרת
bm25_data = logic.load_bm25_index()

class ChatRequest(BaseModel):
    message: str
    history: list = []

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    # שימוש ישיר בקלט ללא תיקון כתיב — הצ'יפים שולחים ערכים מדויקים באנגלית
    exact_message = request.message.lower()

    # חיפוש קוקטיילים רלוונטיים — מחזיר (context, match_type)
    context, match_type = logic.retrieve_candidates(bm25_data, exact_message, top_k=4)

    if context is None:
        return {"error": "No matching recipes found."}

    # החזרת תשובה בסטרימינג
    return StreamingResponse(
        logic.stream_llm_response(client, request.message, context, request.history, match_type),
        media_type="text/plain"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
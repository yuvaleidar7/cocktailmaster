import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles 
from pydantic import BaseModel
from groq import Groq
import logic
from dotenv import load_dotenv

current_dir = Path(__file__).parent
env_path = current_dir / ".env"

load_dotenv(dotenv_path=env_path)

# Uses GROQ_API_KEY_1 to match your rotation setup configuration
client = Groq(api_key=os.getenv("GROQ_API_KEY_1"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/images", StaticFiles(directory=current_dir), name="images")

@app.get("/")
async def serve_index():
    return FileResponse(current_dir / "index.html")

@app.get("/script.js")
async def serve_script():
    return FileResponse(current_dir / "script.js")

bm25_data = logic.load_bm25_index()

class ChatRequest(BaseModel):
    message: str
    history: list = []

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    exact_message = request.message.lower()

    context, match_type = logic.retrieve_candidates(bm25_data, exact_message, top_k=4)

    if context is None:
        return {"error": "No matching recipes found."}

    return StreamingResponse(
        logic.stream_llm_response(client, request.message, context, request.history, match_type),
        media_type="text/plain"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
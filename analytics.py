# analytics.py
from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional

# יצירת הראוטר במקום אפליקציה שלמה
router = APIRouter()

class TrackingEvent(BaseModel):
    event_name: str
    user_id: Optional[str] = None
    properties: Dict[str, Any] = {}

def process_and_store_event(event: TrackingEvent, ip_address: str, user_agent: str):
    # כאן בעתיד תוכל להוסיף שמירה למסד נתונים מקומי או לוגר קבצים משלך
    print(f"Processing event: {event.event_name} from IP: {ip_address}")
    print(f"Properties: {event.properties}")
    pass

@router.post("/track")
async def track_user_action(event: TrackingEvent, request: Request, background_tasks: BackgroundTasks):
    client_ip = request.client.host
    user_agent = request.headers.get("user-agent", "")
    
    background_tasks.add_task(process_and_store_event, event, client_ip, user_agent)
    return {"status": "logged"}
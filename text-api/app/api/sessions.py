from fastapi import APIRouter, HTTPException
from ..models import SessionResponse, SessionCreate
from ..utils import JSONStorage
import uuid

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
storage = JSONStorage()

@router.post("/create", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    session_id = str(uuid.uuid4())
    session_data = storage.create_session(session_id, target_cefr=request.target_cefr)
    return SessionResponse(**session_data)

@router.get("/{session_id}/status")
async def get_session_status(session_id: str):
    if not storage.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = storage.get_history(session_id)
    current = storage.get_current(session_id)
    session_info = storage.get_session_info(session_id)
    
    return {
        "session_id": session_id,
        "exists": True,
        "created_at": history.created_at if history else None,
        "target_cefr": session_info.get("target_cefr") if session_info else None,
        "has_current_text": current is not None and current.text is not None,
        "has_feedback": current is not None and current.feedback is not None,
        "message_count": len(history.messages) if history else 0,
        "attempt_number": current.attempt_number if current else 1
    }

@router.get("/{session_id}/attempt-number")
async def get_attempt_number(session_id: str):
    if not storage.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    current = storage.get_current(session_id)
    
    return {
        "session_id": session_id,
        "attempt_number": current.attempt_number if current else 1
    }

@router.get("/{session_id}/best-attempt")
async def get_best_attempt(session_id: str):
    if not storage.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    current = storage.get_current(session_id)
    session_info = storage.get_session_info(session_id)
    
    if not current or not current.best_attempt:
        return {
            "session_id": session_id,
            "has_best_attempt": False,
            "target_cefr": session_info.get("target_cefr") if session_info else None,
            "best_attempt": None
        }
    
    return {
        "session_id": session_id,
        "has_best_attempt": True,
        "target_cefr": session_info.get("target_cefr") if session_info else None,
        "best_attempt": current.best_attempt.model_dump() if current.best_attempt else None
    }
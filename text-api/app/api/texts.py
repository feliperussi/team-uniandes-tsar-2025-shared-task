from fastapi import APIRouter, HTTPException
from ..models import TextCreate, TextUpdate, Text, CurrentState
from ..utils import JSONStorage
import uuid

router = APIRouter(prefix="/api/v1/texts", tags=["texts"])
storage = JSONStorage()

@router.post("/create")
async def create_or_update_text(text_data: TextCreate):
    session_id = text_data.session_id
    
    if not session_id:
        session_id = str(uuid.uuid4())
        storage.create_session(session_id)
    elif not storage.session_exists(session_id):
        storage.create_session(session_id)
    
    current = storage.get_current(session_id)
    version = 1
    
    if current and current.text:
        version = current.text.version + 1
    
    text = Text(
        cefr_level=text_data.cefr_level,
        text_id=text_data.text_id,
        text_translated=text_data.text_translated,
        version=version
    )
    
    storage.save_text(session_id, text)
    
    return {
        "session_id": session_id,
        "text": text.model_dump(),
        "message": f"Text saved successfully (version {version})"
    }

@router.get("/{session_id}/current")
async def get_current_text(session_id: str):
    if not storage.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    current = storage.get_current(session_id)
    
    if not current or not current.text:
        raise HTTPException(status_code=404, detail="No text found for this session")
    
    return current.model_dump()

@router.put("/{session_id}/update")
async def update_text(session_id: str, update_data: TextUpdate):
    if not storage.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    current = storage.get_current(session_id)
    
    if not current or not current.text:
        raise HTTPException(status_code=404, detail="No text found to update")
    
    text = Text(
        id=str(uuid.uuid4()),
        cefr_level=current.text.cefr_level,
        text_id=current.text.text_id,
        text_translated=update_data.text_translated,
        version=current.text.version + 1
    )
    
    storage.save_text(session_id, text)
    
    return {
        "session_id": session_id,
        "text": text.model_dump(),
        "message": f"Text updated successfully (version {text.version})"
    }

@router.get("/{session_id}/versions")
async def get_text_versions(session_id: str):
    if not storage.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = storage.get_history(session_id)
    
    if not history:
        return {"versions": []}
    
    versions = []
    for msg in history.messages:
        if msg.metadata and msg.metadata.get("action") == "text_update":
            versions.append({
                "version": msg.metadata.get("version"),
                "timestamp": msg.timestamp,
                "cefr_level": msg.metadata.get("cefr_level"),
                "text_id": msg.metadata.get("text_id")
            })
    
    return {"session_id": session_id, "versions": versions}
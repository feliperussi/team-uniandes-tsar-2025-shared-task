from fastapi import APIRouter, HTTPException
from ..utils import JSONStorage

router = APIRouter(prefix="/api/v1/history", tags=["history"])
storage = JSONStorage()

@router.get("/{session_id}")
async def get_history(session_id: str):
    if not storage.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = storage.get_history(session_id)
    
    if not history:
        raise HTTPException(status_code=404, detail="No history found for this session")
    
    return history.model_dump()

@router.get("/{session_id}/llm-format")
async def get_history_llm_format(session_id: str):
    if not storage.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = storage.get_history(session_id)
    
    if not history:
        raise HTTPException(status_code=404, detail="No history found for this session")
    
    conversation = []
    for msg in history.messages:
        conversation.append({
            "role": msg.role,
            "content": msg.content
        })
    
    return {
        "session_id": session_id,
        "conversation": conversation,
        "total_messages": len(conversation)
    }

@router.get("/{session_id}/messages")
async def get_messages_only(session_id: str):
    if not storage.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = storage.get_history(session_id)
    
    if not history:
        return {"messages": []}
    
    messages = []
    for msg in history.messages:
        messages.append({
            "timestamp": msg.timestamp,
            "role": msg.role,
            "content": msg.content
        })
    
    return {
        "session_id": session_id,
        "messages": messages
    }
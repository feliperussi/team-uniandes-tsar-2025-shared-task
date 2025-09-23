from fastapi import APIRouter, HTTPException
from ..models import FeedbackCreate, Feedback, MetricsEvaluation
from ..utils import JSONStorage

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])
storage = JSONStorage()

@router.post("/create")
async def create_feedback(feedback_data: FeedbackCreate):
    if not storage.session_exists(feedback_data.session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    current = storage.get_current(feedback_data.session_id)
    
    if not current or not current.text:
        raise HTTPException(status_code=400, detail="No text found to evaluate")
    
    # Create metrics object if any metric fields are provided
    metrics = None
    if feedback_data.cefr_compliance or feedback_data.bertscore or feedback_data.meaningbert:
        if feedback_data.cefr_compliance and feedback_data.bertscore is not None and feedback_data.meaningbert is not None:
            metrics = MetricsEvaluation(
                cefr_compliance=feedback_data.cefr_compliance,
                bertscore=feedback_data.bertscore,
                meaningbert=feedback_data.meaningbert
            )
    
    feedback = Feedback(
        approval=feedback_data.approval,
        grade=feedback_data.grade,
        feedback=feedback_data.feedback,
        metrics=metrics
    )
    
    storage.save_feedback(feedback_data.session_id, feedback)
    
    return {
        "session_id": feedback_data.session_id,
        "feedback": feedback.model_dump(),
        "text_version": current.text.version,
        "message": f"Feedback saved successfully ({feedback.approval} - Grade: {feedback.grade}/10)"
    }

@router.get("/{session_id}/current")
async def get_current_feedback(session_id: str):
    if not storage.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    current = storage.get_current(session_id)
    
    if not current or not current.feedback:
        raise HTTPException(status_code=404, detail="No feedback found for current text")
    
    return {
        "session_id": session_id,
        "feedback": current.feedback.model_dump(),
        "text_version": current.text.version if current.text else None
    }

@router.get("/{session_id}/all")
async def get_all_feedback(session_id: str):
    if not storage.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")
    
    history = storage.get_history(session_id)
    
    if not history:
        return {"feedbacks": []}
    
    feedbacks = []
    for msg in history.messages:
        if msg.metadata and msg.metadata.get("action") == "feedback":
            feedbacks.append({
                "feedback_id": msg.metadata.get("feedback_id"),
                "timestamp": msg.timestamp,
                "grade": msg.metadata.get("grade"),
                "approval": msg.metadata.get("approval"),
                "feedback_text": msg.metadata.get("feedback_text")
            })
    
    return {"session_id": session_id, "feedbacks": feedbacks}
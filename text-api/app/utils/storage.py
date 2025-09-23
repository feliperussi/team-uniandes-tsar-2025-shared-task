import json
import os
from pathlib import Path
from typing import Optional
from datetime import datetime
from ..models import CurrentState, History, LLMMessage, Text, Feedback

class JSONStorage:
    def __init__(self, base_path: str = "data/sessions"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_session_path(self, session_id: str) -> Path:
        session_path = self.base_path / session_id
        session_path.mkdir(parents=True, exist_ok=True)
        return session_path
    
    def _get_current_file(self, session_id: str) -> Path:
        return self._get_session_path(session_id) / "current.json"
    
    def _get_history_file(self, session_id: str) -> Path:
        return self._get_session_path(session_id) / "history.json"
    
    def session_exists(self, session_id: str) -> bool:
        return self._get_session_path(session_id).exists()
    
    def create_session(self, session_id: str, target_cefr: str) -> dict:
        session_path = self._get_session_path(session_id)
        
        history = History(
            session_id=session_id,
            created_at=datetime.now(),
            messages=[]
        )
        
        self._save_history(session_id, history)
        
        # Save session info including target CEFR
        session_info = {
            "session_id": session_id,
            "target_cefr": target_cefr,
            "created_at": history.created_at.isoformat()
        }
        session_info_file = session_path / "session_info.json"
        with open(session_info_file, 'w', encoding='utf-8') as f:
            json.dump(session_info, f, indent=2)
        
        # Don't create current.json initially, only when text is added
        
        return {"session_id": session_id, "created_at": history.created_at, "target_cefr": target_cefr}
    
    def get_current(self, session_id: str) -> Optional[CurrentState]:
        current_file = self._get_current_file(session_id)
        if not current_file.exists():
            return None
        
        with open(current_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        if data.get('text') is None:
            return None
            
        return CurrentState(**data)
    
    def save_text(self, session_id: str, text: Text) -> None:
        # Get existing current state to preserve attempt number and best attempt
        existing_current = self.get_current(session_id)
        attempt_number = 1
        best_attempt = None
        
        if existing_current:
            # Increment attempt number when saving new text
            attempt_number = existing_current.attempt_number + 1
            best_attempt = existing_current.best_attempt
        
        current = CurrentState(
            text=text, 
            feedback=None,
            attempt_number=attempt_number,
            best_attempt=best_attempt
        )
        self._save_current(session_id, current)
        
        self._add_to_history(
            session_id,
            LLMMessage(
                role="user",
                content=f"Text created/updated with CEFR level {text.cefr_level}",
                metadata={
                    "action": "text_update",
                    "text_id": text.text_id,
                    "version": text.version,
                    "cefr_level": text.cefr_level
                }
            )
        )
        
        self._add_to_history(
            session_id,
            LLMMessage(
                role="assistant",
                content=f"Text saved: {text.text_translated}",
                metadata={
                    "text_id": text.id,
                    "version": text.version
                }
            )
        )
    
    def save_feedback(self, session_id: str, feedback: Feedback) -> None:
        current = self.get_current(session_id)
        if not current or not current.text:
            raise ValueError("No text found for this session")
        
        current.feedback = feedback
        
        # Update best attempt if metrics are provided
        if feedback.metrics:
            session_info = self.get_session_info(session_id)
            target_cefr = session_info.get("target_cefr") if session_info else None
            
            if target_cefr:
                # Check if this should be the new best attempt
                should_update_best = False
                
                if current.best_attempt is None:
                    # No best attempt yet
                    should_update_best = True
                else:
                    # Compare with existing best attempt
                    # Priority 1: Match target CEFR with better meaningbert
                    if feedback.metrics.cefr_compliance.upper() == target_cefr.upper():
                        if current.best_attempt.metrics_cefr_compliance.upper() != target_cefr.upper():
                            # New one matches target, old one doesn't
                            should_update_best = True
                        elif current.best_attempt.metrics_meaningbert is not None:
                            # Both match target, compare meaningbert
                            if feedback.metrics.meaningbert > current.best_attempt.metrics_meaningbert:
                                should_update_best = True
                        else:
                            # New one has metrics, old one doesn't
                            should_update_best = True
                    elif current.best_attempt.metrics_cefr_compliance.upper() != target_cefr.upper():
                        # Neither matches target, compare meaningbert
                        if current.best_attempt.metrics_meaningbert is not None:
                            if feedback.metrics.meaningbert > current.best_attempt.metrics_meaningbert:
                                should_update_best = True
                        else:
                            should_update_best = True
                
                if should_update_best:
                    # Create a copy of the current text with metrics for best attempt
                    from copy import deepcopy
                    best_text = deepcopy(current.text)
                    best_text.metrics_meaningbert = feedback.metrics.meaningbert
                    best_text.metrics_cefr_compliance = feedback.metrics.cefr_compliance
                    current.best_attempt = best_text
        
        self._save_current(session_id, current)
        
        metadata = {
            "action": "feedback",
            "feedback_id": feedback.id,
            "grade": feedback.grade,
            "approval": feedback.approval,
            "feedback_text": feedback.feedback
        }
        
        if feedback.metrics:
            metadata["metrics"] = {
                "cefr_compliance": feedback.metrics.cefr_compliance,
                "bertscore": feedback.metrics.bertscore,
                "meaningbert": feedback.metrics.meaningbert
            }
        
        self._add_to_history(
            session_id,
            LLMMessage(
                role="system",
                content=f"Feedback received: Grade {feedback.grade}/10 - {feedback.approval}",
                metadata=metadata
            )
        )
    
    def get_history(self, session_id: str) -> Optional[History]:
        history_file = self._get_history_file(session_id)
        if not history_file.exists():
            return None
        
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return History(**data)
    
    def _save_current(self, session_id: str, current: CurrentState) -> None:
        current_file = self._get_current_file(session_id)
        
        data = {
            "text": current.text.model_dump() if current.text else None,
            "feedback": current.feedback.model_dump() if current.feedback else None,
            "attempt_number": current.attempt_number,
            "best_attempt": current.best_attempt.model_dump() if current.best_attempt else None
        }
        
        with open(current_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    def get_session_info(self, session_id: str) -> Optional[dict]:
        session_info_file = self._get_session_path(session_id) / "session_info.json"
        if not session_info_file.exists():
            return None
        
        with open(session_info_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _save_history(self, session_id: str, history: History) -> None:
        history_file = self._get_history_file(session_id)
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history.model_dump(), f, indent=2, default=str)
    
    def _add_to_history(self, session_id: str, message: LLMMessage) -> None:
        history = self.get_history(session_id)
        if not history:
            history = History(
                session_id=session_id,
                created_at=datetime.now(),
                messages=[]
            )
        
        history.messages.append(message)
        self._save_history(session_id, history)
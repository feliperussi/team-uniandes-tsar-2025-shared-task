from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import numpy as np
from transformers import pipeline
import evaluate
import asyncio
import logging
import os
import warnings

# Suppress specific warnings
warnings.filterwarnings("ignore", category=FutureWarning)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize models and metrics (lazy loading)
cefr_models = None
meaning_bert = None
bertscore = None

def initialize_models():
    """Initialize models on first use"""
    global cefr_models, meaning_bert, bertscore
    
    if cefr_models is None:
        logger.info("Loading CEFR models...")
        try:
            cefr_models = [
                pipeline(task="text-classification", model="AbdullahBarayan/ModernBERT-base-doc_en-Cefr", device=-1),
                pipeline(task="text-classification", model="AbdullahBarayan/ModernBERT-base-doc_sent_en-Cefr", device=-1),
                pipeline(task="text-classification", model="AbdullahBarayan/ModernBERT-base-reference_AllLang2-Cefr2", device=-1)
            ]
            logger.info("CEFR models loaded")
        except Exception as e:
            logger.error(f"Error loading CEFR models: {e}")
            raise
    
    if meaning_bert is None:
        logger.info("Loading MeaningBERT...")
        try:
            meaning_bert = evaluate.load("davebulaval/meaningbert")
            logger.info("MeaningBERT loaded")
        except Exception as e:
            logger.error(f"Error loading MeaningBERT: {e}")
            raise
    
    if bertscore is None:
        logger.info("Loading BERTScore...")
        try:
            bertscore = evaluate.load("bertscore")
            logger.info("BERTScore loaded")
        except Exception as e:
            logger.error(f"Error loading BERTScore: {e}")
            raise

def get_cefr_label(text: str) -> str:
    """Get CEFR label for a single text"""
    if cefr_models is None:
        initialize_models()
    
    top_preds = (model(text)[0] for model in cefr_models)
    best = max(top_preds, key=lambda d: d["score"])
    return best["label"]

def get_bertscore(simplified: str, original: str) -> float:
    """Calculate BERTScore between simplified and original text"""
    if bertscore is None:
        initialize_models()
    
    try:
        result = bertscore.compute(
            references=[original], 
            predictions=[simplified], 
            lang="en",
            device="mps",
            batch_size=1,
            verbose=False
        )
        return round(float(np.mean(result["f1"])), 4)
    except Exception as e:
        logger.error(f"Error calculating BERTScore: {e}")
        # Return a default value if BERTScore fails
        return 0.0

def get_meaningbert_score(simplified: str, original: str) -> float:
    """Calculate MeaningBERT score between simplified and original text"""
    if meaning_bert is None:
        initialize_models()
    
    try:
        score = meaning_bert.compute(
            predictions=[simplified], 
            references=[original]
        )
        return round(score["scores"][0] / 100, 4)
    except Exception as e:
        logger.error(f"Error calculating MeaningBERT: {e}")
        # Return a default value if MeaningBERT fails
        return 0.0

class TextMetricsRequest(BaseModel):
    simplified_text: str
    original_text: str

class TextMetricsResponse(BaseModel):
    cefr_compliance: str
    bertscore: float
    meaningbert: float

@router.post("/evaluate", response_model=TextMetricsResponse)
async def evaluate_text_metrics(request: TextMetricsRequest) -> TextMetricsResponse:
    """
    Evaluate text simplification metrics.
    
    Calculates three metrics:
    1. CEFR Compliance - The predicted CEFR level of the simplified text
    2. BERTScore - Semantic similarity between simplified and original text
    3. MeaningBERT - Meaning preservation score between simplified and original text
    """
    try:
        # Initialize models if not already loaded
        initialize_models()
        
        # Calculate metrics sequentially to avoid threading issues with tqdm
        cefr_result = get_cefr_label(request.simplified_text)
        bert_result = get_bertscore(request.simplified_text, request.original_text)
        meaning_result = get_meaningbert_score(request.simplified_text, request.original_text)
        
        return TextMetricsResponse(
            cefr_compliance=cefr_result,
            bertscore=bert_result,
            meaningbert=meaning_result
        )
        
    except Exception as e:
        logger.error(f"Error evaluating metrics: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error evaluating metrics: {str(e)}")

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Check if the metrics endpoint is healthy and models are loaded"""
    models_loaded = {
        "cefr_models": cefr_models is not None,
        "meaning_bert": meaning_bert is not None,
        "bertscore": bertscore is not None
    }
    
    return {
        "status": "healthy",
        "models_loaded": models_loaded,
        "all_models_ready": all(models_loaded.values())
    }
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import json
from pathlib import Path
import random
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Cache for trial data
trial_data_cache = None

def load_trial_data():
    """Load and cache the trial data"""
    global trial_data_cache
    
    if trial_data_cache is None:
        trial_data_path = Path(__file__).parent.parent.parent.parent / "tsar2025_trialdata.jsonl"
        
        if not trial_data_path.exists():
            raise FileNotFoundError(f"Trial data file not found at {trial_data_path}")
        
        logger.info(f"Loading trial data from {trial_data_path}")
        trial_data_cache = []
        
        with open(trial_data_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    trial_data_cache.append(json.loads(line))
        
        logger.info(f"Loaded {len(trial_data_cache)} examples from trial data")
    
    return trial_data_cache

class ExampleData(BaseModel):
    dataset_id: str
    text_id: str
    original: str
    target_cefr: str
    reference: str

class SimpleExampleData(BaseModel):
    original: str
    reference: str

@router.get("/get-examples", response_class=PlainTextResponse)
async def get_examples(
    count: int = Query(..., ge=1, le=20, description="Number of examples to return (1-20)"),
    text_id: Optional[str] = Query("", description="Text ID to exclude from results"),
    target_cefr: str = Query(..., description="Target CEFR level (a2 or b1)")
) -> str:
    """
    Get examples from the trial data based on criteria.
    
    Parameters:
    - count: Number of examples to return (1-20)
    - text_id: Optional text ID to exclude from results
    - target_cefr: Target CEFR level to filter by (a2 or b1)
    
    Returns examples in natural language format with numbered examples, original text and translation.
    """
    try:
        # Validate target_cefr
        target_cefr = target_cefr.lower()
        if target_cefr not in ['a2', 'b1']:
            raise HTTPException(status_code=400, detail="target_cefr must be 'a2' or 'b1'")
        
        # Load trial data
        trial_data = load_trial_data()
        
        # Filter by target_cefr
        filtered_examples = [
            example for example in trial_data 
            if example.get('target_cefr', '').lower() == target_cefr
        ]
        
        # Exclude text_id if provided
        if text_id and text_id.strip():
            filtered_examples = [
                example for example in filtered_examples 
                if example.get('text_id', '') != text_id
            ]
        
        # Limit to requested count
        total_available = len(filtered_examples)
        
        # If we have more examples than requested, randomly sample
        if total_available > count:
            selected_examples = random.sample(filtered_examples, count)
        else:
            selected_examples = filtered_examples
        
        # Convert to natural language format
        response_text = ""
        for i, example in enumerate(selected_examples, 1):
            response_text += f"Example {i}:\n"
            response_text += f"original: {example['original']}\n"
            response_text += f"translation: {example['reference']}\n"
            if i < len(selected_examples):  # Add blank line between examples except after the last one
                response_text += "\n"
        
        return response_text
        
    except FileNotFoundError as e:
        logger.error(f"Trial data file not found: {e}")
        raise HTTPException(status_code=500, detail="Trial data file not found")
    except Exception as e:
        logger.error(f"Error getting examples: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting examples: {str(e)}")

@router.get("/get-example-by-id/{text_id}", response_model=ExampleData)
async def get_example_by_id(text_id: str) -> ExampleData:
    """
    Get a specific example by its text_id.
    
    Parameters:
    - text_id: The text ID to retrieve (e.g., "01-a2", "01-b1")
    
    Returns the example matching the text_id.
    """
    try:
        # Load trial data
        trial_data = load_trial_data()
        
        # Find the example with matching text_id
        for example in trial_data:
            if example.get('text_id', '') == text_id:
                return ExampleData(
                    dataset_id=example['dataset_id'],
                    text_id=example['text_id'],
                    original=example['original'],
                    target_cefr=example['target_cefr'],
                    reference=example['reference']
                )
        
        # If not found
        raise HTTPException(status_code=404, detail=f"Example with text_id '{text_id}' not found")
        
    except FileNotFoundError as e:
        logger.error(f"Trial data file not found: {e}")
        raise HTTPException(status_code=500, detail="Trial data file not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting example by ID: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting example: {str(e)}")

@router.get("/stats")
async def get_stats() -> Dict:
    """
    Get statistics about the available trial data.
    
    Returns counts by CEFR level and total examples.
    """
    try:
        # Load trial data
        trial_data = load_trial_data()
        
        # Count by CEFR level
        stats = {
            'total': len(trial_data),
            'by_cefr': {}
        }
        
        for example in trial_data:
            cefr = example.get('target_cefr', 'unknown').lower()
            stats['by_cefr'][cefr] = stats['by_cefr'].get(cefr, 0) + 1
        
        # Get unique text IDs (without CEFR suffix)
        unique_texts = set()
        for example in trial_data:
            text_id = example.get('text_id', '')
            if '-' in text_id:
                base_id = text_id.rsplit('-', 1)[0]
                unique_texts.add(base_id)
        
        stats['unique_texts'] = len(unique_texts)
        
        return stats
        
    except FileNotFoundError as e:
        logger.error(f"Trial data file not found: {e}")
        raise HTTPException(status_code=500, detail="Trial data file not found")
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")
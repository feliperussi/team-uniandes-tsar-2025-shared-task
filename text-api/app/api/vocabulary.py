from fastapi import APIRouter, HTTPException
from ..models import TextTagRequest, TextTagResponse, TaggedWord
from ..utils.vocabulary_processor import VocabularyProcessor
from typing import Dict

router = APIRouter(prefix="/api/v1/vocabulary", tags=["vocabulary"])

# Initialize vocabulary processor once
vocab_processor = VocabularyProcessor()

@router.post("/tag", response_model=TextTagResponse)
async def tag_text(request: TextTagRequest):
    """
    Tag words in text according to CEFR vocabulary levels
    
    This endpoint:
    - Receives a text
    - Identifies words from the CEFR vocabulary
    - Returns tagged words grouped by levels
    
    Handles special cases:
    - Words with slashes (a/an, step over/in/on/out of)
    - Words with parentheses (stick (piece of wood), forward(s))
    - Multiple forms (doctor / Dr, OK / okay)
    """
    try:
        # Tag the text
        tagged_words_raw = vocab_processor.tag_text(request.text)
        
        # Group words by level
        tagged_by_level = {
            "A1": [],
            "A2": [],
            "B1": [],
            "B2": [],
            "C1": []
        }
        
        # Populate the groups
        for tw in tagged_words_raw:
            level = tw["level"]
            word_entry = f"{tw['word']} -> {tw['tagged_as']}" if tw['word'] != tw['tagged_as'].lower() else tw['word']
            
            if level in tagged_by_level:
                # Avoid duplicates within each level
                if word_entry not in tagged_by_level[level]:
                    tagged_by_level[level].append(word_entry)
        
        # Calculate statistics
        level_counts = {}
        total_words = 0
        for level, words in tagged_by_level.items():
            if words:  # Only count non-empty levels
                level_counts[level] = len(words)
                total_words += len(words)
        
        stats = {
            "total_tagged": total_words,
            "by_level": level_counts
        }
        
        return TextTagResponse(
            text=request.text,
            tagged_words=tagged_by_level,
            stats=stats
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

@router.get("/stats")
async def get_vocabulary_stats():
    """
    Get statistics about the loaded vocabulary
    """
    stats = vocab_processor.get_vocabulary_stats()
    return {
        "vocabulary_stats": stats,
        "levels": list(stats.keys())[:-1],  # Exclude 'total'
        "total_words": stats.get("total", 0)
    }

@router.post("/check-word")
async def check_word(word: str) -> Dict:
    """
    Check if a specific word exists in the vocabulary and at what level(s)
    """
    word_lower = word.lower().strip()
    
    found_in = []
    for level, words in vocab_processor.vocabulary.items():
        for vocab_word in words:
            # Check direct match
            if vocab_word.lower() == word_lower:
                found_in.append({"level": level, "form": vocab_word})
                continue
            
            # Check if it's a variation
            if '/' in vocab_word:
                variations = vocab_processor._expand_slash_variations(vocab_word)
                if word_lower in [v.lower() for v in variations]:
                    found_in.append({"level": level, "form": vocab_word})
            
            # Check if it's the main word in parenthetical expression
            if '(' in vocab_word:
                main_word = vocab_processor._extract_main_word(vocab_word)
                if main_word.lower() == word_lower:
                    found_in.append({"level": level, "form": vocab_word})
    
    return {
        "word": word,
        "found": len(found_in) > 0,
        "occurrences": found_in
    }

@router.get("/level/{level}")
async def get_words_by_level(level: str):
    """
    Get all words for a specific CEFR level
    """
    level = level.upper()
    if level not in vocab_processor.vocabulary:
        raise HTTPException(status_code=404, detail=f"Level {level} not found. Available levels: {list(vocab_processor.vocabulary.keys())}")
    
    words = vocab_processor.vocabulary[level]
    return {
        "level": level,
        "word_count": len(words),
        "words": words[:100],  # Return first 100 words
        "message": f"Showing first 100 words of {len(words)} total words for level {level}"
    }
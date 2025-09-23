import json
import re
from typing import Dict, List, Tuple, Set
from pathlib import Path

class VocabularyProcessor:
    def __init__(self, vocab_path: str = "../vocabulary.json"):
        self.vocab_path = Path(vocab_path)
        self.vocabulary = self._load_vocabulary()
        self.processed_vocab = self._process_vocabulary()
        
    def _load_vocabulary(self) -> Dict[str, List[str]]:
        """Load vocabulary from JSON file"""
        if not self.vocab_path.exists():
            # Try alternative path
            alt_path = Path(__file__).parent.parent.parent.parent / "vocabulary.json"
            if alt_path.exists():
                self.vocab_path = alt_path
            else:
                return {"A1": [], "A2": [], "B1": [], "B2": [], "C1": []}
        
        with open(self.vocab_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _process_vocabulary(self) -> Dict[str, Dict[str, str]]:
        """
        Process vocabulary to handle special cases
        Returns: Dict[normalized_word, Dict[original_form, level]]
        """
        processed = {}
        
        for level, words in self.vocabulary.items():
            for word in words:
                # Handle different cases
                if '/' in word and '(' not in word:
                    # Cases like "a/an", "step over/in/on/out of"
                    variations = self._expand_slash_variations(word)
                    for variant in variations:
                        normalized = variant.lower().strip()
                        if normalized not in processed:
                            processed[normalized] = {}
                        processed[normalized][word] = level
                        
                elif '(' in word and ')' in word:
                    # Cases like "stick (piece of wood)", "forward(s)"
                    main_word = self._extract_main_word(word)
                    if main_word:
                        normalized = main_word.lower().strip()
                        if normalized not in processed:
                            processed[normalized] = {}
                        processed[normalized][word] = level
                        
                        # Handle cases like "forward(s)" -> forward, forwards
                        if word.endswith('(s)'):
                            base = word.replace('(s)', '')
                            plural = base + 's'
                            for variant in [base, plural]:
                                normalized = variant.lower().strip()
                                if normalized not in processed:
                                    processed[normalized] = {}
                                processed[normalized][word] = level
                else:
                    # Normal words
                    normalized = word.lower().strip()
                    if normalized not in processed:
                        processed[normalized] = {}
                    processed[normalized][word] = level
        
        return processed
    
    def _expand_slash_variations(self, word: str) -> List[str]:
        """
        Expand slash variations
        Examples:
        - "a/an" -> ["a", "an"]
        - "step over/in/on/out of" -> ["step over", "step in", "step on", "step out of"]
        - "doctor / Dr" -> ["doctor", "Dr"]
        """
        # Handle spaces around slashes
        word = re.sub(r'\s*/\s*', '/', word)
        
        # Special case: multi-word with slashes
        if ' ' in word and '/' in word:
            # Cases like "step over/in/on/out of"
            parts = word.split()
            if '/' in parts[-1] or (len(parts) > 1 and '/' in parts[-2]):
                # Find the part with slashes
                base_parts = []
                variable_part = None
                suffix_parts = []
                
                for i, part in enumerate(parts):
                    if '/' in part:
                        base_parts = parts[:i]
                        variable_part = part
                        suffix_parts = parts[i+1:] if i+1 < len(parts) else []
                        break
                
                if variable_part:
                    variations = []
                    options = variable_part.split('/')
                    for option in options:
                        variant = ' '.join(base_parts + [option] + suffix_parts)
                        variations.append(variant.strip())
                    return variations
        
        # Simple slash cases like "a/an", "OK/okay"
        return [v.strip() for v in word.split('/')]
    
    def _extract_main_word(self, word: str) -> str:
        """
        Extract main word from parenthetical expressions
        Examples:
        - "stick (piece of wood)" -> "stick"
        - "mine (belongs to me)" -> "mine"
        - "forward(s)" -> "forward"
        """
        # Find the first opening parenthesis
        paren_index = word.find('(')
        if paren_index > 0:
            main_word = word[:paren_index].strip()
            return main_word
        return word
    
    def tag_text(self, text: str) -> List[Dict[str, str]]:
        """
        Tag words in text with their CEFR levels
        Returns: List of tagged words with format:
        [{"word": "original_word", "tagged_as": "vocabulary_entry", "level": "A1"}]
        """
        # Tokenize text (simple approach, can be improved)
        words = re.findall(r'\b[\w\']+\b', text.lower())
        
        tagged = []
        seen = set()  # To avoid duplicates
        
        for word in words:
            normalized = word.lower().strip()
            
            if normalized in self.processed_vocab:
                entries = self.processed_vocab[normalized]
                for original_form, level in entries.items():
                    tag_key = f"{word}_{original_form}_{level}"
                    if tag_key not in seen:
                        seen.add(tag_key)
                        tagged.append({
                            "word": word,
                            "tagged_as": original_form,
                            "level": level,
                            "position": text.lower().find(word)
                        })
        
        # Sort by position in text
        tagged.sort(key=lambda x: x["position"])
        
        # Remove position from output
        for item in tagged:
            del item["position"]
        
        return tagged
    
    def get_vocabulary_stats(self) -> Dict[str, int]:
        """Get statistics about the vocabulary"""
        stats = {}
        for level, words in self.vocabulary.items():
            stats[level] = len(words)
        stats["total"] = sum(stats.values())
        return stats
# Text Management API

API for managing AI-generated texts with version control, feedback system, and text simplification metrics evaluation.

## Features

- **Session Management**: Each agent gets a unique `session_id` with target CEFR level
- **Text Versioning**: Complete history of modifications with attempt tracking
- **Feedback System**: Evaluation with approval (PASS/FAIL), grading (1-10), and metrics
- **LLM History**: Conversational format for continuity
- **JSON Storage**: No database required, local file storage
- **Text Metrics**: Evaluate text simplification quality with CEFR compliance, BERTScore, and MeaningBERT
- **CEFR Vocabulary Tagging**: Automatic vocabulary level detection
- **Best Attempt Tracking**: Automatically tracks the best attempt based on CEFR compliance and MeaningBERT scores
- **Attempt Counter**: Tracks the number of attempts per session

## Installation

### Option 1: With UV (Recommended)

```bash
# Install UV if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### Option 2: With traditional pip

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Run the API

```bash
# Development with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

The API will be available at: http://localhost:8001

## Interactive Documentation

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

## Data Structure

### Files per Session

Each session creates a folder in `data/sessions/{session_id}/` with:

1. **session_info.json**: Session metadata including target CEFR level
2. **current.json**: Current state of text, feedback, attempt number, and best attempt
3. **history.json**: Complete history in LLM format

## Main Endpoints

### Text Simplification Metrics (NEW)

#### Evaluate text simplification quality

```bash
POST /api/v1/metrics/evaluate

# Example with NASA asteroid text
curl -X POST http://localhost:8001/api/v1/metrics/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "simplified_text": "Asteroids are small rocks in space. NASA is collecting information about middle-sized asteroids (bigger than 140 metres wide). They think there are 25,000 asteroids like this. NASA has collected information about 8,000 of them, but not about the other 17,000. In 2013, in Russia, above the city of Chelyabinsk, an asteroid exploded and hurt 1,200 people. That asteroid was only 19 metres wide, so bigger asteroids will be very dangerous if they hit the Earth.",
    "original_text": "Now NASA is working towards logging some of the smaller asteroids, those measuring 140 metres wide or more. Of the 25,000 estimated asteroids of this size, so far about 8,000 have been logged, leaving 17,000 unaccounted for. Considering that a 19-metre asteroid that exploded above the city of Chelyabinsk in Russia in 2013 injured 1,200 people, these middle-sized asteroids would be a serious danger if they enter Earth'\''s orbit."
  }'
```

Response:

```json
{
  "cefr_compliance": "A2",
  "bertscore": 0.9189,
  "meaningbert": 0.8121
}
```

**Metrics explained:**

- **cefr_compliance**: Predicted CEFR level of the simplified text (A1, A2, B1, B2, C1, C2)
- **bertscore**: Semantic similarity between simplified and original (0-1, higher is better)
- **meaningbert**: Meaning preservation score (0-1, higher means better preservation)

#### Check metrics health status

```bash
GET /api/v1/metrics/health

curl http://localhost:8001/api/v1/metrics/health
```

### Trial Data Examples (NEW)

#### Get examples from trial data

```bash
GET /api/v1/examples/get-examples?count=5&target_cefr=a2&text_id=01-a2

# Get 5 examples of level a2, excluding text_id "01-a2"
curl "http://localhost:8001/api/v1/examples/get-examples?count=5&target_cefr=a2&text_id=01-a2"

# Get all 20 examples of level b1
curl "http://localhost:8001/api/v1/examples/get-examples?count=20&target_cefr=b1&text_id="

# Get 10 random examples of level a2
curl "http://localhost:8001/api/v1/examples/get-examples?count=10&target_cefr=a2&text_id="
```

Response:

```json
{
  "examples": [
    {
      "text_id": "07-a2",
      "original": "The Life of Pi tells the extraordinary story...",
      "target_cefr": "a2",
      "reference": "'The Life of Pi' is a very surprising story..."
    }
  ],
  "total_available": 19,
  "returned_count": 5
}
```

#### Get specific example by ID

```bash
GET /api/v1/examples/get-example-by-id/{text_id}

curl http://localhost:8001/api/v1/examples/get-example-by-id/01-a2
```

#### Get trial data statistics

```bash
GET /api/v1/examples/stats

curl http://localhost:8001/api/v1/examples/stats
```

Response:

```json
{
  "total": 40,
  "by_cefr": { "a2": 20, "b1": 20 },
  "unique_texts": 20
}
```

### Vocabulary Tagging

#### Tag text with CEFR levels

```bash
POST /api/v1/vocabulary/tag

curl -X POST http://localhost:8001/api/v1/vocabulary/tag \
  -H "Content-Type: application/json" \
  -d '{
    "text": "I have a cat and a dog. Yesterday I went to the bank to get money."
  }'
```

Response:

```json
{
  "text": "I have a cat and a dog. Yesterday I went to the bank to get money.",
  "tagged_words": {
    "A1": [
      "have",
      "cat",
      "dog",
      "yesterday",
      "went -> go",
      "bank -> bank (money)",
      "money"
    ],
    "A2": [],
    "B1": [],
    "B2": [],
    "C1": []
  },
  "stats": {
    "total_tagged": 7,
    "by_level": { "A1": 7 }
  }
}
```

#### Check specific word

```bash
POST /api/v1/vocabulary/check-word?word=stick

curl -X POST "http://localhost:8001/api/v1/vocabulary/check-word?word=stick"
```

#### Get vocabulary statistics

```bash
GET /api/v1/vocabulary/stats

curl http://localhost:8001/api/v1/vocabulary/stats
```

#### Get words by level

```bash
GET /api/v1/vocabulary/level/A1

curl http://localhost:8001/api/v1/vocabulary/level/A1
```

### Special Cases for Vocabulary

The tagging endpoint automatically handles:

- **Words with slash**: "a/an" → detects "a" or "an"
- **Multiple expressions**: "step over/in/on/out of" → detects "step over", "step in", etc.
- **Words with parentheses**: "stick (piece of wood)" → detects "stick" and tags as "stick (piece of wood)"
- **Alternative forms**: "forward(s)" → detects "forward" or "forwards"
- **Spaces in slashes**: "doctor / Dr" → detects "doctor" or "Dr"

### Sessions

#### Create new session with target CEFR level

```bash
POST /api/v1/sessions/create

curl -X POST http://localhost:8001/api/v1/sessions/create \
  -H "Content-Type: application/json" \
  -d '{
    "target_cefr": "A2"
  }'
```

Response:

```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "created_at": "2024-01-20T10:00:00",
  "target_cefr": "A2"
}
```

#### Get session status

```bash
GET /api/v1/sessions/{session_id}/status

curl http://localhost:8001/api/v1/sessions/123e4567-e89b-12d3-a456-426614174000/status
```

Response:

```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "exists": true,
  "created_at": "2024-01-20T10:00:00",
  "target_cefr": "A2",
  "has_current_text": true,
  "has_feedback": true,
  "message_count": 4,
  "attempt_number": 2
}
```

#### Get current attempt number

```bash
GET /api/v1/sessions/{session_id}/attempt-number

curl http://localhost:8001/api/v1/sessions/123e4567-e89b-12d3-a456-426614174000/attempt-number
```

Response:

```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "attempt_number": 2
}
```

#### Get best attempt

```bash
GET /api/v1/sessions/{session_id}/best-attempt

curl http://localhost:8001/api/v1/sessions/123e4567-e89b-12d3-a456-426614174000/best-attempt
```

Response:

```json
{
  "session_id": "123e4567-e89b-12d3-a456-426614174000",
  "has_best_attempt": true,
  "target_cefr": "A2",
  "best_attempt": {
    "id": "abc123",
    "cefr_level": "A2",
    "text_id": "text_001",
    "text_translated": "This is the best attempt that matches the target CEFR...",
    "metrics_meaningbert": 0.85,
    "metrics_cefr_compliance": "A2"
  }
}
```

### Texts

#### Create/Update text

```bash
POST /api/v1/texts/create

curl -X POST http://localhost:8001/api/v1/texts/create \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "cefr_level": "A1",
    "text_id": "text_001",
    "text_translated": "This is my translated text..."
  }'
```

#### Get current text

```bash
GET /api/v1/texts/{session_id}/current

curl http://localhost:8001/api/v1/texts/123e4567-e89b-12d3-a456-426614174000/current
```

### Feedback

#### Add feedback with optional metrics

```bash
POST /api/v1/feedback/create

# Basic feedback
curl -X POST http://localhost:8001/api/v1/feedback/create \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "approval": "PASS",
    "grade": 8,
    "feedback": "Good work, only some minor errors..."
  }'

# Feedback with metrics (triggers best attempt evaluation)
curl -X POST http://localhost:8001/api/v1/feedback/create \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "123e4567-e89b-12d3-a456-426614174000",
    "approval": "PASS",
    "grade": 8,
    "feedback": "Good work, only some minor errors...",
    "cefr_compliance": "A2",
    "bertscore": 0.92,
    "meaningbert": 0.85
  }'
```

**Note**: When metrics are provided, the system automatically evaluates if this attempt should be marked as the best attempt based on:

1. Priority to attempts matching the target CEFR level
2. Higher MeaningBERT score when CEFR levels are equal

### History

#### Get history in LLM format

```bash
GET /api/v1/history/{session_id}/llm-format

curl http://localhost:8001/api/v1/history/123e4567-e89b-12d3-a456-426614174000/llm-format
```

## Typical Workflow

1. **Start session with target CEFR level**

   ```python
   # Create session with target CEFR level
   session_data = {"target_cefr": "A2"}
   response = requests.post("http://localhost:8001/api/v1/sessions/create", json=session_data)
   session_id = response.json()["session_id"]
   target_cefr = response.json()["target_cefr"]
   ```

2. **Create/Edit text**

   ```python
   data = {
       "session_id": session_id,
       "cefr_level": "A1",
       "text_id": "text_001",
       "text_translated": "My text in English..."
   }
   requests.post("http://localhost:8001/api/v1/texts/create", json=data)
   ```

3. **Receive feedback with metrics**

   ```python
   # First evaluate the text metrics
   metrics_data = {
       "simplified_text": "Your simplified text...",
       "original_text": "The original complex text..."
   }
   metrics_response = requests.post("http://localhost:8001/api/v1/metrics/evaluate", json=metrics_data)
   metrics = metrics_response.json()

   # Then add feedback with metrics
   feedback = {
       "session_id": session_id,
       "approval": "PASS",
       "grade": 7,
       "feedback": "Evaluator comments...",
       "cefr_compliance": metrics["cefr_compliance"],
       "bertscore": metrics["bertscore"],
       "meaningbert": metrics["meaningbert"]
   }
   requests.post("http://localhost:8001/api/v1/feedback/create", json=feedback)
   ```

4. **Evaluate text metrics**

   ```python
   metrics_data = {
       "simplified_text": "Your simplified text...",
       "original_text": "The original complex text..."
   }
   response = requests.post("http://localhost:8001/api/v1/metrics/evaluate", json=metrics_data)
   metrics = response.json()
   print(f"CEFR Level: {metrics['cefr_compliance']}")
   print(f"BERTScore: {metrics['bertscore']}")
   print(f"MeaningBERT: {metrics['meaningbert']}")
   ```

5. **Continue iterating**

   - When creating a new text, the attempt counter increments
   - Previous feedback is automatically removed when text is edited
   - History maintains complete record
   - Best attempt is automatically tracked based on CEFR compliance and MeaningBERT scores

6. **Check progress**

   ```python
   # Get current attempt number
   response = requests.get(f"http://localhost:8001/api/v1/sessions/{session_id}/attempt-number")
   attempt_number = response.json()["attempt_number"]

   # Get best attempt
   response = requests.get(f"http://localhost:8001/api/v1/sessions/{session_id}/best-attempt")
   best_attempt = response.json()
   if best_attempt["has_best_attempt"]:
       print(f"Best attempt CEFR: {best_attempt['best_attempt']['metrics_cefr_compliance']}")
       print(f"Best attempt MeaningBERT: {best_attempt['best_attempt']['metrics_meaningbert']}")
   ```

## Complete Example with Python

```python
import requests

BASE_URL = "http://localhost:8001"

# 1. Create session with target CEFR level
session_data = {"target_cefr": "A2"}
session_resp = requests.post(f"{BASE_URL}/api/v1/sessions/create", json=session_data)
session_id = session_resp.json()["session_id"]
target_cefr = session_resp.json()["target_cefr"]
print(f"Session ID: {session_id}, Target CEFR: {target_cefr}")

# 2. Create initial text
text_data = {
    "session_id": session_id,
    "cefr_level": "A1",
    "text_id": "text_001",
    "text_translated": "Hello, my name is John. I am 20 years old."
}
requests.post(f"{BASE_URL}/api/v1/texts/create", json=text_data)

# 3. Evaluate text and add feedback with metrics
original = "Complex original text..."
simplified = "Hello, my name is John. I am 20 years old."

metrics_data = {
    "simplified_text": simplified,
    "original_text": original
}
metrics_resp = requests.post(f"{BASE_URL}/api/v1/metrics/evaluate", json=metrics_data)
metrics = metrics_resp.json()

feedback_data = {
    "session_id": session_id,
    "approval": "FAIL",
    "grade": 5,
    "feedback": "Needs more complexity for A1 level",
    "cefr_compliance": metrics["cefr_compliance"],
    "bertscore": metrics["bertscore"],
    "meaningbert": metrics["meaningbert"]
}
requests.post(f"{BASE_URL}/api/v1/feedback/create", json=feedback_data)

# 4. Update text based on feedback
update_data = {
    "text_translated": "Hello, my name is John and I live in Madrid. I am 20 years old and I study engineering."
}
requests.put(f"{BASE_URL}/api/v1/texts/{session_id}/update", json=update_data)

# 5. Check attempt number
attempt_resp = requests.get(f"{BASE_URL}/api/v1/sessions/{session_id}/attempt-number")
print(f"Current attempt: {attempt_resp.json()['attempt_number']}")

# 6. Create another text (increments attempt)
text_data["text_translated"] = "Hello, my name is John and I live in Madrid. I am 20 years old and I study engineering."
requests.post(f"{BASE_URL}/api/v1/texts/create", json=text_data)

# 7. Add feedback with better metrics
metrics_data["simplified_text"] = text_data["text_translated"]
metrics_resp = requests.post(f"{BASE_URL}/api/v1/metrics/evaluate", json=metrics_data)
new_metrics = metrics_resp.json()

feedback_data["approval"] = "PASS"
feedback_data["grade"] = 8
feedback_data["cefr_compliance"] = new_metrics["cefr_compliance"]
feedback_data["bertscore"] = new_metrics["bertscore"]
feedback_data["meaningbert"] = new_metrics["meaningbert"]
requests.post(f"{BASE_URL}/api/v1/feedback/create", json=feedback_data)

# 8. Check best attempt
best_resp = requests.get(f"{BASE_URL}/api/v1/sessions/{session_id}/best-attempt")
best_data = best_resp.json()
if best_data["has_best_attempt"]:
    print(f"Best attempt found!")
    print(f"  CEFR: {best_data['best_attempt']['metrics_cefr_compliance']}")
    print(f"  MeaningBERT: {best_data['best_attempt']['metrics_meaningbert']}")

# 9. View history
history = requests.get(f"{BASE_URL}/api/v1/history/{session_id}/llm-format")
print(history.json())
```

## Project Structure

```
text-api/
├── app/
│   ├── main.py              # Main FastAPI application
│   ├── models.py            # Pydantic models
│   ├── api/
│   │   ├── sessions.py      # Session endpoints
│   │   ├── texts.py         # Text endpoints
│   │   ├── feedback.py      # Feedback endpoints
│   │   ├── history.py       # History endpoints
│   │   ├── vocabulary.py    # Vocabulary tagging endpoints
│   │   ├── metrics.py       # Text metrics evaluation endpoints
│   │   └── examples.py      # Trial data examples endpoints
│   └── utils/
│       ├── storage.py       # JSON file handling
│       └── vocabulary_processor.py  # CEFR vocabulary processing
├── data/
│   └── sessions/           # Session data (created automatically)
├── requirements.txt
└── README.md
```

## Important Notes

- Data is saved in `data/sessions/`
- Each text edit removes previous feedback
- Creating a new text increments the attempt counter
- Best attempt is automatically tracked when feedback includes metrics
- History maintains complete record of all operations
- No database required, all local JSON storage
- Metrics models are loaded on first use (may take a moment)
- Best attempt selection prioritizes:
  1. Attempts matching the target CEFR level
  2. Higher MeaningBERT scores when CEFR levels are equal

## Development

For development with hot-reload:

```bash
uvicorn app.main:app --reload
```

## License

MIT

---

_Disclaimer: This documentation was AI-generated and reviewed by the team._

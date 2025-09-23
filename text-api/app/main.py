from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import sessions_router, texts_router, feedback_router, history_router, vocabulary_router, metrics_router, examples_router

app = FastAPI(
    title="Text Management API",
    description="API for managing AI-generated texts with version control, feedback, and CEFR vocabulary tagging",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sessions_router)
app.include_router(texts_router)
app.include_router(feedback_router)
app.include_router(history_router)
app.include_router(vocabulary_router)
app.include_router(metrics_router, prefix="/api/v1/metrics", tags=["metrics"])
app.include_router(examples_router, prefix="/api/v1/examples", tags=["examples"])

@app.get("/")
async def root():
    return {
        "message": "Text Management API",
        "version": "1.1.0",
        "docs": "/docs",
        "endpoints": {
            "sessions": "/api/v1/sessions",
            "texts": "/api/v1/texts",
            "feedback": "/api/v1/feedback",
            "history": "/api/v1/history",
            "vocabulary": "/api/v1/vocabulary",
            "metrics": "/api/v1/metrics",
            "examples": "/api/v1/examples"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
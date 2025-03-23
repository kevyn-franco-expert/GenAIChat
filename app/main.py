from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.api.routes.cv_routes import router as cv_router
from app.api.routes.query_routes import router as query_router
from app.core.config import settings
from app.infrastructure.vector_db import init_vector_db

# Load environment variables
load_dotenv()

# Initialize the app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description=settings.PROJECT_DESCRIPTION,
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(cv_router, tags=["CVs"])
app.include_router(query_router, tags=["Queries"])

# Initialize vector DB on startup
@app.on_event("startup")
async def startup_event():
    # Initialize the vector database
    init_vector_db()

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
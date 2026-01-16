"""
Ugat-Lemmatizer FastAPI Application
Main entry point for the API server.
"""

import sys
from pathlib import Path

# Add backend to path for imports
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import router

# =========================
# App Configuration
# =========================

app = FastAPI(
    title="Ugat-Lemmatizer API",
    description="""
    **Ugat-Lemmatizer** is a morphological analyzer and lemmatizer 
    for Philippine regional languages.
    
    ### Supported Languages
    - **Ilocano** (Northern Luzon)
    - **Cebuano** (Visayas)
    - **Hiligaynon** (Western Visayas)
    
    ### Features
    - POS Tagging (CRF-based and Affix-based approaches)
    - Lemmatization (Root word extraction)
    - Morphological analysis
    
    ### Approaches
    1. **CRF-based**: Uses trained Conditional Random Field models
    2. **Affix-based**: Uses rule-based affix pattern matching
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# =========================
# CORS Middleware
# =========================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# Include Routes
# =========================

app.include_router(router, prefix="/api/v1", tags=["Lemmatizer"])


# =========================
# Root Endpoint
# =========================

@app.get("/")
def root():
    """Root endpoint with API information."""
    return {
        "name": "Ugat-Lemmatizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "dialects": "/api/v1/dialects",
            "tag": "/api/v1/tag",
            "lemmatize": "/api/v1/lemmatize",
            "health": "/api/v1/health"
        }
    }


# =========================
# Run Server
# =========================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import assessment, schemes, financial, ai

app = FastAPI(
    title="GramSahayak AI API",
    description="Rural Entrepreneurship & Business Feasibility Advisory Platform API",
    version="1.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root status
@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "GramSahayak AI Platform Backend",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "GramSahayak API"}

# Include routers without prefix
app.include_router(assessment.router)
app.include_router(schemes.router)
app.include_router(financial.router)
app.include_router(ai.router)

# Also include with /api prefix to support both direct and proxied calls
api_app = FastAPI()
api_app.include_router(assessment.router)
api_app.include_router(schemes.router)
api_app.include_router(financial.router)
api_app.include_router(ai.router)
app.mount("/api", api_app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

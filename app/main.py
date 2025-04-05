from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import auth, patient
from app.db.database import init_db, close_db_connection
from app.db.models import Patient, Clinician, Session, GameResult  # Import all models

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        yield
    finally:
        await close_db_connection()

app = FastAPI(
    title="ADHD Therapy Platform API",
    lifespan=lifespan,
)

app.include_router(auth.router)

# Root endpoint
@app.get("/", tags=["Root"])
def read_root():
    return {
        "message": "Welcome to ADHD Therapy Platform API",
        "documentation": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "timestamp": datetime.utcnow()}
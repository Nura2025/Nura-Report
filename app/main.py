from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import analytics, auth, patient ,session ,mini_games, game_results
from app.db.database import init_db, close_db_connection
from app.db.models import Patient, Clinician, Session, GameResult  
from fastapi.middleware.cors import CORSMiddleware


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
app.include_router(session.router)
app.include_router(mini_games.router)
app.include_router(game_results.router)
app.include_router(analytics.router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
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
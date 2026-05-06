"""
FastAPI application entrypoint.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database.engine import init_db, close_db
from api.routers import search
# from api.routers import assets, lineage, trust, governance

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown
    await close_db()

app = FastAPI(
    title="DataContextOS API",
    description="An AI-Native Metadata Intelligence Platform",
    version="0.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

app.include_router(search.router, prefix="/api")
# app.include_router(assets.router, prefix="/api")
# app.include_router(lineage.router, prefix="/api")
# app.include_router(trust.router, prefix="/api")
# app.include_router(governance.router, prefix="/api")

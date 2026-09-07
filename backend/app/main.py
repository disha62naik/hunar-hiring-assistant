from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_db_and_tables
from app.routers import screenings, reachout, webhook, calls

app = FastAPI(title="Hunar Hiring Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(screenings.router)
app.include_router(reachout.router)
app.include_router(webhook.router)
app.include_router(calls.router)


@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
def health():
    return {"status": "ok"}

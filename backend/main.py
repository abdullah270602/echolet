from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import logging

from app.routes.livekit import router as livekit_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


app = FastAPI(title="Echolet")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(livekit_router, prefix="/livekit", tags=["livekit"])


@app.get("/")
def read_root():
    return {"Echolet": "Online"}


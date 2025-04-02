from dotenv import load_dotenv
load_dotenv()

import os
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from motor.motor_asyncio import AsyncIOMotorClient
from config.database import MONGO_URI

from routes.analysis_route import router as analysis_route
from routes.users_route import router as users_route
from routes.db_route import router as db_route
from utils.utils import read_file

@asynccontextmanager
async def lifespan(app: FastAPI):
    client = AsyncIOMotorClient(MONGO_URI)
    yield  # App is running here
    client.close()  # Cleanup when shutting down

app = FastAPI(lifespan=lifespan)
origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
print(origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_route, prefix="/users")
app.include_router(analysis_route)
app.include_router(db_route)

@app.get("/", response_class=HTMLResponse)
async def get():
    return read_file("./pages/websocket_test.html")

@app.get("/health-check")
def health_check():
    return "Ok"

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

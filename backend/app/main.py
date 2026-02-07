from fastapi import FastAPI
from pydantic import BaseModel
from app.github_client import fetch_profile_data
from app.readme_builder import build_readme

app = FastAPI()

class GenerateRequest(BaseModel):
    username: str
    config: dict = {}

@app.get("/api/profile/{username}")
async def profile(username: str):
    return await fetch_profile_data(username)

@app.post("/api/generate")
async def generate(req: GenerateRequest):
    profile_data = await fetch_profile_data(req.username)
    result = build_readme(profile_data, req.config)
    return result

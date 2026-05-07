from importlib.metadata import version
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .core import analyse_repo
from .models import GitAnalysisResult

app = FastAPI(title="git-analyser", version=version("git-analyser"))


class AnalyseRequest(BaseModel):
    repo: str  # local path or remote URL


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyse", response_model=GitAnalysisResult)
def analyse(req: AnalyseRequest):
    result = analyse_repo(req.repo)
    if result.error:
        raise HTTPException(status_code=400, detail=result.error)
    return result

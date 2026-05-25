from fastapi import FastAPI, HTTPException
from lens_contract import add_contract_routes, add_cors
from pydantic import BaseModel

from .core import analyse_repo
from .manifest import MANIFEST
from .models import GitAnalysisResult

app = FastAPI(title="git-analyser", version=MANIFEST["version"])

# GET /health and GET /manifest (the family contract, via lens-contract).
add_contract_routes(app, MANIFEST)
# CORS — env-driven: GIT_ANALYSER_MODE=desktop (Electron) or GIT_ANALYSER_ALLOWED_ORIGINS.
add_cors(app, env_prefix="GIT_ANALYSER")


class AnalyseRequest(BaseModel):
    repo: str  # local path or remote URL


@app.post("/analyse", response_model=GitAnalysisResult)
def analyse(req: AnalyseRequest):
    result = analyse_repo(req.repo)
    if result.error:
        raise HTTPException(status_code=400, detail=result.error)
    return result

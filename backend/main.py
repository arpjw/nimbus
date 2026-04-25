from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from api.routes.tasks import router as tasks_router
from api.routes.repos import ws_router, repo_router
from github_app.webhooks import router as github_router

app = FastAPI(title="Nimbus API", version="0.1.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


app.include_router(tasks_router)
app.include_router(ws_router)
app.include_router(repo_router)
app.include_router(github_router)

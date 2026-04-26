from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import init_db
from api.routes.keys import router as keys_router
from api.routes.tasks import router as tasks_router, review_router, test_router, rules_router
from api.routes.repos import ws_router, repo_router
from api.routes.slack import router as slack_router
from api.routes.linear import router as linear_api_router
from api.routes.automations import router as automations_router
from github_app.webhooks import router as github_router
from linear_app.webhooks import linear_router
from services.automation_engine import AutomationEngine

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
    AutomationEngine().schedule_all()


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


app.include_router(keys_router)
app.include_router(tasks_router)
app.include_router(review_router)
app.include_router(test_router)
app.include_router(rules_router)
app.include_router(ws_router)
app.include_router(repo_router)
app.include_router(slack_router)
app.include_router(github_router)
app.include_router(linear_api_router)
app.include_router(linear_router)
app.include_router(automations_router)

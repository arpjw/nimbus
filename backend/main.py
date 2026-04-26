from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from starlette.responses import HTMLResponse

from config import settings
from database import init_db
from api.routes.auth import router as auth_router
from api.routes.keys import router as keys_router
from api.routes.tasks import router as tasks_router, review_router, test_router, rules_router
from api.routes.repos import ws_router, repo_router
from api.routes.slack import router as slack_router
from api.routes.linear import router as linear_api_router
from api.routes.automations import router as automations_router
from api.routes.skills import router as skills_router
from api.routes.prism import router as prism_router
from api.routes.agents import router as agents_router
from api.routes.pipelines import router as pipelines_router
from api.routes.marketplace import router as marketplace_router
from github_app.webhooks import router as github_router
from linear_app.webhooks import linear_router
from services.automation_engine import AutomationEngine
from services.skills import SkillsService

app = FastAPI(
    title="Nimbus API",
    description="Autonomous software engineering infrastructure.",
    version="1.1.0",
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui():
    html = get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Nimbus API",
        swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
    )
    custom = """
    <link href="https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@300;400;500&display=swap" rel="stylesheet">
    <style>
      /* Base */
      body { background: #14120c !important; font-family: 'Inter', sans-serif; }

      /* Hide default topbar */
      .swagger-ui .topbar { display: none !important; }

      /* Custom header */
      #nimbus-header {
        background: #14120c;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        padding: 16px 32px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        position: sticky;
        top: 0;
        z-index: 100;
      }
      #nimbus-header a {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-size: 22px;
        color: #edecec;
        text-decoration: none;
      }
      #nimbus-header span {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: rgba(255,255,255,0.3);
        letter-spacing: 0.06em;
        text-transform: uppercase;
      }

      /* Main wrapper */
      .swagger-ui { background: #14120c; }
      .swagger-ui .wrapper { padding: 0 32px; }

      /* Info section */
      .swagger-ui .info { margin: 40px 0 28px; }
      .swagger-ui .info .title {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        font-size: 36px;
        font-weight: 400;
        color: #edecec;
      }
      .swagger-ui .info .description p {
        color: rgba(255,255,255,0.4);
        font-family: 'Inter', sans-serif;
        font-size: 15px;
      }
      .swagger-ui .info .base-url {
        font-family: 'JetBrains Mono', monospace;
        color: rgba(255,255,255,0.3);
        font-size: 12px;
      }

      /* Scheme container */
      .swagger-ui .scheme-container {
        background: #14120c;
        border-bottom: 1px solid rgba(255,255,255,0.06);
        box-shadow: none;
        padding: 16px 0;
      }
      .swagger-ui .servers-title { color: rgba(255,255,255,0.4); font-family: 'Inter', sans-serif; font-size: 12px; }
      .swagger-ui .servers { background: #1a1710; border: 1px solid rgba(255,255,255,0.06); border-radius: 8px; padding: 10px 14px; }
      .swagger-ui .servers select { background: #201d15; border: 1px solid rgba(255,255,255,0.1); color: #edecec; font-family: 'JetBrains Mono', monospace; font-size: 12px; border-radius: 5px; }

      /* Operation blocks */
      .swagger-ui .opblock {
        background: #1a1710;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 8px;
        margin-bottom: 8px;
        box-shadow: none;
      }
      .swagger-ui .opblock:hover { border-color: rgba(255,255,255,0.1); }
      .swagger-ui .opblock.is-open { border-color: rgba(255,255,255,0.1); }
      .swagger-ui .opblock-summary { border-bottom: none; }
      .swagger-ui .opblock.is-open .opblock-summary { border-bottom: 1px solid rgba(255,255,255,0.06); }

      /* HTTP method badges */
      .swagger-ui .opblock-summary-method {
        border-radius: 5px;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 600;
        font-size: 11px;
        min-width: 70px;
        text-align: center;
      }
      .swagger-ui .opblock.opblock-get .opblock-summary-method { background: #6aab7a; }
      .swagger-ui .opblock.opblock-post .opblock-summary-method { background: #c4a96a; }
      .swagger-ui .opblock.opblock-delete .opblock-summary-method { background: #e05c5c; }
      .swagger-ui .opblock.opblock-patch .opblock-summary-method { background: #7c8cf8; }
      .swagger-ui .opblock.opblock-put .opblock-summary-method { background: #7c8cf8; }

      /* Color left borders on opblocks */
      .swagger-ui .opblock.opblock-get { border-left: 3px solid #6aab7a; }
      .swagger-ui .opblock.opblock-post { border-left: 3px solid #c4a96a; }
      .swagger-ui .opblock.opblock-delete { border-left: 3px solid #e05c5c; }
      .swagger-ui .opblock.opblock-patch { border-left: 3px solid #7c8cf8; }
      .swagger-ui .opblock.opblock-put { border-left: 3px solid #7c8cf8; }

      /* Path and description */
      .swagger-ui .opblock-summary-path {
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        color: #edecec;
      }
      .swagger-ui .opblock-summary-path__deprecated { color: rgba(255,255,255,0.3); }
      .swagger-ui .opblock-summary-description {
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        color: rgba(255,255,255,0.4);
      }

      /* Opblock body */
      .swagger-ui .opblock-body { background: #14120c; }
      .swagger-ui .opblock-section-header {
        background: #1a1710;
        border-bottom: 1px solid rgba(255,255,255,0.06);
      }
      .swagger-ui .opblock-section-header h4 {
        color: rgba(255,255,255,0.4);
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }

      /* Parameters */
      .swagger-ui table thead tr th {
        color: rgba(255,255,255,0.3);
        font-family: 'Inter', sans-serif;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        border-bottom: 1px solid rgba(255,255,255,0.06);
      }
      .swagger-ui .parameter__name {
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        color: #edecec;
      }
      .swagger-ui .parameter__name.required::after { color: #e05c5c; }
      .swagger-ui .parameter__type {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #c4a96a;
      }
      .swagger-ui .parameter__in {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: rgba(255,255,255,0.25);
      }
      .swagger-ui .parameter__deprecated { color: rgba(255,255,255,0.3); }
      .swagger-ui .markdown p, .swagger-ui .markdown li {
        color: rgba(255,255,255,0.4);
        font-family: 'Inter', sans-serif;
        font-size: 13px;
      }

      /* Inputs */
      .swagger-ui input, .swagger-ui textarea, .swagger-ui select {
        background: #201d15;
        border: 1px solid rgba(255,255,255,0.1);
        color: #edecec;
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        border-radius: 6px;
      }
      .swagger-ui input:focus, .swagger-ui textarea:focus {
        border-color: #c4a96a;
        outline: none;
        box-shadow: 0 0 0 2px rgba(196,169,106,0.1);
      }
      .swagger-ui input[type="checkbox"] { accent-color: #c4a96a; }

      /* Buttons */
      .swagger-ui .btn {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 13px;
        border-radius: 7px;
        transition: all 0.15s;
      }
      .swagger-ui .btn.execute {
        background: #edecec;
        color: #14120c;
        border: none;
      }
      .swagger-ui .btn.execute:hover { background: #fff; }
      .swagger-ui .btn.cancel {
        background: transparent;
        border: 1px solid rgba(255,255,255,0.15);
        color: rgba(255,255,255,0.4);
      }
      .swagger-ui .btn.authorize {
        background: transparent;
        border: 1px solid #c4a96a;
        color: #c4a96a;
      }
      .swagger-ui .btn.authorize svg { fill: #c4a96a; }
      .swagger-ui .btn.btn-clear {
        background: transparent;
        border: 1px solid rgba(255,255,255,0.1);
        color: rgba(255,255,255,0.4);
      }

      /* Response section */
      .swagger-ui .responses-wrapper { background: #14120c; }
      .swagger-ui .response-col_status {
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        color: #edecec;
        font-weight: 600;
      }
      .swagger-ui .response-col_description {
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        color: rgba(255,255,255,0.4);
      }
      .swagger-ui .response-col_links { color: rgba(255,255,255,0.3); }
      .swagger-ui table.responses-table tbody tr td { border-color: rgba(255,255,255,0.06); }

      /* Code blocks */
      .swagger-ui .highlight-code > .microlight {
        background: #0e0c08 !important;
        border-radius: 6px;
        border: 1px solid rgba(255,255,255,0.06);
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        color: rgba(255,255,255,0.6);
        padding: 14px;
      }
      .swagger-ui .copy-to-clipboard { background: #201d15; border: 1px solid rgba(255,255,255,0.1); }
      .swagger-ui .copy-to-clipboard:hover { background: #2a2518; }

      /* Models section */
      .swagger-ui section.models {
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 10px;
        margin-top: 24px;
      }
      .swagger-ui section.models h4 {
        color: #edecec;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
      }
      .swagger-ui .model-box {
        background: #1a1710;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 6px;
      }
      .swagger-ui .model {
        color: rgba(255,255,255,0.5);
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
      }
      .swagger-ui .model-title {
        font-family: 'Inter', sans-serif;
        color: #edecec;
        font-weight: 500;
      }
      .swagger-ui .prop-type { color: #c4a96a; font-family: 'JetBrains Mono', monospace; }
      .swagger-ui .prop-format { color: rgba(255,255,255,0.3); font-family: 'JetBrains Mono', monospace; }

      /* Tags (section headers) */
      .swagger-ui .opblock-tag {
        font-family: 'Inter', sans-serif;
        font-size: 16px;
        font-weight: 500;
        color: #edecec;
        border-bottom: 1px solid rgba(255,255,255,0.06);
      }
      .swagger-ui .opblock-tag:hover { background: rgba(255,255,255,0.02); }
      .swagger-ui .opblock-tag small { color: rgba(255,255,255,0.3); font-family: 'Inter', sans-serif; }

      /* Auth modal */
      .swagger-ui .dialog-ux .modal-ux {
        background: #1a1710;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
      }
      .swagger-ui .dialog-ux .modal-ux-header { border-bottom: 1px solid rgba(255,255,255,0.06); }
      .swagger-ui .dialog-ux .modal-ux-header h3 {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        color: #edecec;
        font-weight: 400;
      }
      .swagger-ui .dialog-ux .modal-ux-content p,
      .swagger-ui .dialog-ux .modal-ux-content label {
        color: rgba(255,255,255,0.5);
        font-family: 'Inter', sans-serif;
      }

      /* SVG icons */
      .swagger-ui svg { fill: rgba(255,255,255,0.4); }
      .swagger-ui .expand-methods svg, .swagger-ui .expand-operation svg { fill: rgba(255,255,255,0.4); }

      /* Tab bar */
      .swagger-ui .tab { border-bottom: 1px solid rgba(255,255,255,0.06); }
      .swagger-ui .tab li {
        color: rgba(255,255,255,0.4);
        font-family: 'Inter', sans-serif;
        font-size: 13px;
      }
      .swagger-ui .tab li.active {
        color: #edecec;
        border-bottom: 2px solid #c4a96a;
      }

      /* Loading */
      .swagger-ui .loading-container .loading::after { border-color: #c4a96a transparent; }

      /* Scrollbar */
      ::-webkit-scrollbar { width: 5px; height: 5px; }
      ::-webkit-scrollbar-track { background: #14120c; }
      ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 3px; }
      ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }
    </style>
    <script>
      window.addEventListener('load', () => {
        const header = document.createElement('div');
        header.id = 'nimbus-header';
        header.innerHTML = '<a href="https://get-nimbus.com">Nimbus</a><span>API Reference v1.1.0</span>';
        document.body.insertBefore(header, document.body.firstChild);
      });
    </script>
    """
    modified = html.body.decode().replace("</head>", custom + "</head>")
    return HTMLResponse(modified)


@app.on_event("startup")
async def startup():
    init_db()
    from services.skills import migrate_skills_table
    migrate_skills_table()
    SkillsService().seed_builtins()
    AutomationEngine().schedule_all()


@app.get("/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


app.include_router(auth_router)
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
app.include_router(skills_router)
app.include_router(prism_router)
app.include_router(agents_router)
app.include_router(pipelines_router)
app.include_router(marketplace_router)

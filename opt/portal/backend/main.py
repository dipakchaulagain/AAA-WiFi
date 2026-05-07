from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .auth import require_auth
from .database import close_db_pool, init_db_pool
from .rate_limit import limiter
from .routers import accounting, auth, dashboard, diagnostics, policy, sessions, setup, users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db_pool()
    yield
    await close_db_pool()


app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://localhost", "https://127.0.0.1"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_gate(request: Request, call_next):
    path = request.url.path
    if path.startswith("/api/v1/") and not (
        path.startswith("/api/v1/setup/")
        or path == "/api/v1/auth/login"
        or path == "/api/v1/setup/status"
    ):
        request.state.user = await require_auth(request)
    return await call_next(request)


@app.get("/api/health")
async def health():
    return {"ok": True}


app.include_router(setup.router, prefix="/api/v1/setup", tags=["setup"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(sessions.router, prefix="/api/v1/sessions", tags=["sessions"])
app.include_router(accounting.router, prefix="/api/v1/accounting", tags=["accounting"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(policy.router, prefix="/api/v1", tags=["policy"])
app.include_router(diagnostics.router, prefix="/api/v1/diagnostics", tags=["diagnostics"])


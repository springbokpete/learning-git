"""
Private 5G NOC Dashboard — FastAPI application entry point.
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

# In production, set ALLOWED_ORIGINS to a comma-separated list of trusted
# domains, e.g. "https://noc.example.com,https://admin.example.com".
# Defaults to "*" for local development convenience only.
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
ALLOWED_ORIGINS = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]

app = FastAPI(
    title="Private 5G NOC Dashboard",
    description=(
        "Backend API for the MK LAB Private 5G Network Operations Centre. "
        "Provides real-time KPIs, alarms, device inventory and topology for "
        "RAN, core, infrastructure and network domains."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

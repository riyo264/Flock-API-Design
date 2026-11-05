from fastapi import FastAPI
from fastapi.responses import RedirectResponse

app = FastAPI(
    title="Urja Meter Ops API",
    description="A clean API wrapper for the legacy Urja Meter Ops portal.",
    version="1.0.0"
)

@app.get("/", include_in_schema=False)
async def root():
    # Redirect base URL to the auto-generated Swagger UI docs
    return RedirectResponse(url="/docs")

@app.get("/api/v1/health")
async def health_check():
    # Health check to verify API is running
    return {"status": "healthy", "service": "flock-api-wrapper"}
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
from typing import List, Optional
from pydantic import BaseModel
from .client import LegacyPortalClient

class Meter(BaseModel):
    meterId: str
    serialNo: str
    make: str
    phaseType: str
    installStatus: Optional[str] = "Unknown"

class Transformer(BaseModel):
    code: str
    name: str
    feederCode: str
    capacityKva: float

db_cache = {
    "meters": [],
    "transformers": []
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting data ingestion from legacy portal...")
    portal_client = LegacyPortalClient()
    
    try:
        await portal_client.login()
        
        raw_meters = await portal_client.fetch_all_meters()
        raw_transformers = await portal_client.fetch_transformers()
        
        # ingest the data into our local cache
        db_cache["meters"] = raw_meters
        db_cache["transformers"] = raw_transformers
        
        print(f"Ready: Cached {len(raw_meters)} meters and {len(raw_transformers)} transformers.")
    except Exception as e:
        print(f"Error during startup data ingestion: {e}")
    finally:
        await portal_client.client.aclose()
        
    # Yield control back to FastAPI to start accepting incoming requests
    yield 
    
    print("Shutting down API and clearing cache...")
    db_cache.clear()


# API Initialization
app = FastAPI(
    title="Flock Energy - Clean API Wrapper",
    description="Programmatic access to Urja Meter Ops network and consumption data.",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", include_in_schema=False)
async def root():
    # Redirect base URL to the auto-generated Swagger UI docs
    return RedirectResponse(url="/docs")

@app.get("/api/v1/health")
async def health_check():
    # Verify the API wrapper is running
    return {"status": "healthy", "service": "flock-api-wrapper"}

@app.get("/api/v1/meters", response_model=List[Meter])
async def get_meters(status: Optional[str] = None):
    meters = db_cache["meters"]
    
    if status:
        # Perform local filtering in memory
        meters = [
            m for m in meters 
            if (m.get("installStatus") or "Unknown").lower() == status.lower()
        ]
        
    return meters

@app.get("/api/v1/transformers", response_model=List[Transformer])
async def get_transformers():
    return db_cache["transformers"]

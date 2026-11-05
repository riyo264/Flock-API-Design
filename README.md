# Flock-API-Design

This repository contains a clean, documented REST API service built over the legacy Urja Meter Ops portal. It provides programmatic access to meter details and transformer network hierarchy data without requiring direct interaction with the legacy web interface.

## Quickstart (Zero Configuration)

This service is fully containerized. You do not need to install Python or any dependencies locally.

1. **Clone the repository:**
   ```bash
   git clone https://github.com/riyo264/Flock-API-Design.git
   cd Flock-API-Design
   ```

2. **Start the API using Docker:**
   ```bash
   docker-compose up --build
   ```

3. **Explore the API:**
   Open your browser and navigate to **[http://localhost:8000](http://localhost:8000)**. 
   You will be automatically redirected to the interactive Swagger UI documentation where you can explore and execute the endpoints.

## Example Request

You can hit the clean API using `curl`:

```bash
# Get all meters
curl -X 'GET' 'http://localhost:8000/api/v1/meters' -H 'accept: application/json'

# Get meters filtered by status
curl -X 'GET' 'http://localhost:8000/api/v1/meters?status=Faulty' -H 'accept: application/json'
```

## Repository Structure & Deliverables

* `api/main.py`: The FastAPI application and clean routing layer.
* `api/client.py`: The `LegacyPortalClient` that handles legacy session authentication and cryptographic request signing.
* `PROTOCOL.md`: A detailed write-up of how the legacy portal works under the hood, including authentication and data shapes.
* `openapi.json`: The standard OpenAPI 3.x specification for this clean wrapper.

## Design Decisions & Architecture

**1. In-Memory Startup Caching (Local Index)**
Instead of querying the legacy portal on-the-fly per request, this API fetches the complete dataset during the server's startup (`lifespan`) event and stores it in memory. 
* *Trade-off:* This increases the initial boot time of the API by a few seconds. 
* *Benefit:* It completely shields the legacy system from being overwhelmed by programmatic traffic, allows for instant filtering/querying locally, and drops response times to milliseconds.

**2. State-ful HTTP Client**
I utilized `httpx.AsyncClient` to maintain a persistent connection pool that automatically handles the `__Secure-better-auth.session_token` cookie across requests, separating authentication logic from data extraction logic.

**3. What was intentionally left out:** 
I skipped implementing a persistent database (like SQLite or PostgreSQL). Given the size of the data (hundreds of records), an in-memory dictionary is vastly faster and avoids adding unnecessary complexity or infrastructure requirements for the reviewer.

---

## Reflection

**What assumptions did I make?**

I assumed that the utility network data (meters and transformers) is relatively slow-moving and does not change minute-by-minute. This assumption justified building an in-memory cache on startup rather than fetching data live on every single request, prioritizing API speed and legacy server stability over real-time absolute freshness.

**Which part was the most difficult?**

The most difficult part was bypassing the bulk export security. The `/portal/export` endpoint kept failing programmatic requests. I got unstuck by abandoning text searches in the minified JS and instead using the DevTools Network "Initiator" call stack. This led me to a specific WebCrypto block that concatenated the HTTP method, path, query, and a timestamp, and signed it using HMAC-SHA256. I replicated this exact payload construction in Python to bypass the browser.

**If you had another day, what would you improve?**

I would implement asynchronous background polling to handle cache freshness. Using `asyncio.create_task()` to silently fetch data from the legacy portal on a set interval guarantees data freshness without exposing the API consumer to the legacy system's extreme pagination latency.

**What mistake did you make while solving this (there's always one)?**

I initially assumed the "bulk export path" I found in the network traffic contained the primary meter dataset. Later, I realized the export button was actually located on the Distribution Transformer Station (DTS) page, meaning it exported the network hierarchy, not the meters. I had to pivot my architecture to paginate through the meters endpoint while reserving the HMAC-signed bulk path for the transformers.

**If you were reviewing your own submission, what would you criticise?**

I would criticize the tight coupling of the data ingestion to the server startup lifecycle. If the legacy Urja portal is down or times out exactly when my wrapper boots up, my FastAPI server will fail its startup sequence. A more resilient design would allow the server to boot with an empty cache and trigger the legacy ingestion via a background worker, returning a "503 Service Unavailable - Ingesting Data" to consumers in the interim.

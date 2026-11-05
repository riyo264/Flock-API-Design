# Urja Meter Ops - Internal Protocol Investigation

This document records the internal workings of the legacy Urja Meter Ops web portal, discovered via network traffic inspection. The portal operates as a client-side application that fetches JSON data from internal endpoints.

## Authentication & Access
The portal uses cookie-based authentication. 

When a user logs in, the server sets a session cookie named `__Secure-better-auth.session_token`. 
*   **Mechanism:** All subsequent requests to the internal API must include this cookie in the `Cookie` request header.
*   **Format Example:** `__Secure-better-auth.session_token=rN1Lr3gr...`
*   **Security:** The `__Secure-` prefix indicates it requires a secure (HTTPS) connection.

## Discovered Endpoints

All API endpoints appear to be nested under the `/portal/` base path.

### 1. Meter Search & Listing
*   **Endpoint:** `GET /portal/meters/search`
*   **Purpose:** Retrieves a list of meters, optionally filtered by a search query.
*   **Query Parameters:**
    *   `q` (string): The search term. Can be empty (`q=`) for a default list.
    *   `page` (integer): The page number to fetch (e.g., `page=1`).

**Response Shape:**
The endpoint returns a JSON object containing metadata and an array of meter objects.
```json
{
  "data": [
    {
      "meterId": "J100000",
      "serialNo": "SE33962",
      "make": "HPL",
      "phaseType": "single",
      "installStatus": "Installed" 
    }
  ],
  "page": 1,
  "pageSize": 20,
  "total": 403
}
```

### 2. Network Hierarchy (DTS)
*   **Endpoint:** `GET /portal/dts`
*   **Purpose:** Retrieves a list of Distribution Transformer Stations (DTS) to establish the electrical grid network hierarchy.
*   **Query Parameters:**
    *   `page` (integer): The page number to fetch (e.g., `page=1`).

 **Response Shape:**
```json
{
  "data": [
    {
      "code": "DT-001",
      "name": "Malviya Nagar DT 1",
      "feederCode": "F-001",
      "capacityKva": 100
    }
  ],
  "page": 1,
  "pageSize": 20,
  "total": 40
}
```

### 3. Bulk Data Export (Protected Path)
The portal supports bulk data extraction via `/portal/export`, which transfers significantly larger payloads than standard page requests. However, this path is protected by a time-bound cryptographic signature to prevent unauthorized scraping.

**Step 1: Obtain the Signing Secret**
*   **Endpoint:** `GET /portal/keys`
*   **Purpose:** A metadata endpoint that returns a temporary `signingSecret` required for authorizing the export payload.

**Step 2: Generate the HMAC-SHA256 Signature**
Before requesting the export data, the client must generate a 64-character hexadecimal signature. This is done by concatenating specific request variables separated by newline characters (`\n`):
1. HTTP Method (`GET`)
2. Path (`/portal/export`)
3. Query String (`page=1`)
4. Current Unix Timestamp in seconds (e.g., `1730799200`)

This concatenated string is then hashed using HMAC-SHA256, utilizing the `signingSecret` as the cryptographic key.

**Step 3: Execute the Request**
*   **Endpoint:** `GET /portal/export?page=1`
*   **Headers Required:**
    *   `X-Timestamp`: The Unix timestamp generated in Step 2.
    *   `X-Signature`: The generated HMAC-SHA256 hash.
*   **Pagination:** A fresh timestamp and a newly calculated signature must be generated for every subsequent page request (e.g., `page=2`).


## Data Schema & Types

From the `/search` payload, we can infer the `Meter` entity schema:
*   `meterId` (String): A unique identifier (e.g., "J100000").
*   `serialNo` (String): The hardware serial number.
*   `make` (String): Manufacturer (Observed values: "HPL", "L&T", "Genus", "Allied", "Secure").
*   `phaseType` (String): Either "single" or "three".
*   `installStatus` (String, Optional/Nullable): Indicates current status (e.g., "Installed", "Faulty"). 

From the `/dts` payload, we can infer the `Transformer` entity schema:
*   `code` (String): The transformer identifier (e.g., "DT-001").
*   `name` (String): The localized name of the transformer station.
*   `feederCode` (String): The relational link to the upstream feeder (e.g., "F-001"), necessary for mapping the network hierarchy.
*   `capacityKva` (Number): The capacity rating of the transformer.

# Urja Meter Ops - Internal Protocol Discovery

This document outlines the internal workings of the legacy Urja Meter Ops web portal, discovered via network traffic inspection. The portal operates as a client-side application that fetches JSON data from internal endpoints.

## Authentication & Access
The portal uses cookie-based authentication. 

When a user logs in, the server sets a session cookie named `__Secure-better-auth.session_token`. 
*   **Mechanism:** All subsequent requests to the internal API must include this cookie in the `Cookie` request header.
*   **Format Example:** `__Secure-better-auth.session_token=rN1Lr3gr...`
*   **Security:** The `__Secure-` prefix indicates it requires a secure (HTTPS) connection.

To build our API wrapper, we will need to programmatically submit the login credentials, capture this specific cookie from the `Set-Cookie` response header, and inject it into all downstream API requests.

## Discovered Endpoints

All API endpoints appear to be nested under the `/portal/` base path.

### 1. Meter Search & Listing
*   **Endpoint:** `GET /portal/meters/search`
*   **Purpose:** Retrieves a paginated list of meters, optionally filtered by a search query.
*   **Query Parameters:**
    *   `q` (string): The search term. Can be empty (`q=`) for a default list.
    *   `page` (integer): The page number to fetch (e.g., `page=1`).

**Response Shape:**
The endpoint returns a JSON object containing pagination metadata and an array of meter objects.
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

### 2. Other Observed Endpoints (Requires Further Inspection)
Based on initial network traces, the following endpoints also exist and use the same pagination (`page=X`) scheme:
*   `GET /portal/dts`: Likely fetches Distribution Transformer Station (network hierarchy) data.
*   `GET /portal/export`: A bulk data path. Transfers significantly larger payloads (~232kB) than standard paginated requests.
*   `GET /portal/keys`: A small metadata or configuration endpoint.

## Data Schema & Types

From the `/search` payload, we can infer the `Meter` entity schema:
*   `meterId` (String): A unique identifier (e.g., "J100000").
*   `serialNo` (String): The hardware serial number.
*   `make` (String): Manufacturer (Observed values: "HPL", "L&T", "Genus", "Allied", "Secure").
*   `phaseType` (String): Either "single" or "three".
*   `installStatus` (String, Optional/Nullable): Indicates current status (e.g., "Installed", "Faulty"). 

## Quirks & Surprises

1.  **Sparse Data / Optional Fields:** In the `search` response, the `installStatus` field is completely missing from several objects (e.g., meters `J100000` and `J100003`). Our wrapper API must handle missing keys gracefully, either by mapping them to `null` or assigning a default "Unknown" value.
2.  **Pagination Constants:** The system hardcodes a `pageSize` of 20 for the search endpoint. To fetch all 403 records without using the bulk `/export` path, a client would need to make 21 sequential requests.
3.  **Path Routing:** The frontend application routes the user to `/meters`, but the background data fetch calls `/portal/meters/search`. It's important to differentiate the UI routes from the API routes when building the wrapper.
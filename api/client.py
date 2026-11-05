import httpx
import time
import hmac
import hashlib

class LegacyPortalClient:
    def __init__(self):
        self.base_url = "https://urja-ops.flockenergy.tech"
        self.client = httpx.AsyncClient(base_url=self.base_url)

    async def login(self):
        payload = {
            "email": "operator@urja.local", 
            "password": "urja-ops-2026"
        }
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Origin": self.base_url,
            "Referer": f"{self.base_url}/login"
        }

        response = await self.client.post("/api/auth/sign-in/email", json=payload, headers=headers)
        response.raise_for_status()


    def generate_signature(self, method: str, path: str, query: str, secret: str) -> dict:
        timestamp = str(int(time.time()))
        payload = f"{method}\n{path}\n{query}\n{timestamp}"
        
        signature = hmac.new(
            key=secret.encode('utf-8'),
            msg=payload.encode('utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return {"timestamp": timestamp, "signature": signature}
    

    async def fetch_all_meters(self) -> list:
        all_meters = []
        current_page = 1
        
        while True:
            response = await self.client.get(f"/portal/meters/search?q=&page={current_page}")
            response.raise_for_status()
            
            payload = response.json()
            data = payload.get("data", [])
            
            if not data:
                break
                
            all_meters.extend(data)
            
            # Stops requesting if all records are fetched
            total_records = payload.get("total", 0)
            if len(all_meters) >= total_records:
                break
                
            current_page += 1
            
        return all_meters
    

    async def fetch_transformers(self) -> list:
        all_transformers = []
        current_page = 1
        
        keys_response = await self.client.get("/portal/keys")
        keys_response.raise_for_status()
        secret = keys_response.json().get("data", {}).get("signingSecret")
        
        if not secret:
            raise ValueError("Failed to retrieve signingSecret from /portal/keys")
            
        while True:
            method = "GET"
            path = "/portal/export"
            query = f"page={current_page}"
            
            # Generate a fresh signature for this specific page request
            auth_headers = self.generate_signature(method, path, query, secret)

            response = await self.client.get(
                f"{path}?{query}",
                headers={
                    "x-timestamp": auth_headers["timestamp"],
                    "x-signature": auth_headers["signature"]
                }
            )
            response.raise_for_status()
            
            payload = response.json()
            data = payload.get("data", [])
            
            if not data:
                break
                
            all_transformers.extend(data)
            
            total_records = payload.get("total", 0)
            if len(all_transformers) >= total_records:
                break
                
            current_page += 1
            
        return all_transformers
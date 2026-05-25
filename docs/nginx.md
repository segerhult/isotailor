[Browser] 
   │
   ├─ GET /          → NGINX (serves /usr/share/nginx/html/index.html)
   ├─ GET /assets/... → NGINX (serves static assets)
   ├─ GET /api/...   → NGINX proxies to http://backend:8000/api/...
   ├─ GET /docs      → NGINX proxies to http://backend:8000/docs (FastAPI Swagger UI)
   └─ GET /* (SPA)  → NGINX serves /index.html (fallback for client-side routing)

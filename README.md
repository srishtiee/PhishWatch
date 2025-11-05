# PhishWatch
## Backend (FastAPI)

Backend for classifying email headers/.eml files as phishing or genuine.

### Stack
- FastAPI, Auth0 (JWT), MongoDB (Motor + GridFS)
- AES-GCM application-level encryption for user data

### Setup
1. Create and activate a Python 3.11+ virtualenv.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with:
   - `AUTH0_DOMAIN=your-tenant.us.auth0.com`
   - `AUTH0_AUDIENCE=your-api-identifier`
   - `MONGODB_URI=mongodb://localhost:27017`
   - `MONGODB_DB=phishwatch`
   - `ENCRYPTION_KEY_B64=$(openssl rand -base64 32)`

### Run
```bash
uvicorn app.main:app --reload --port 8000
```

### Endpoints
- `GET /health` - health check
- `POST /analysis/header` - body: `{ "header_text": "..." }` (Auth required)
- `POST /analysis/file` - form-data file: `.eml` (Auth required)
- `GET /analysis/` - list analyses for user (Auth required)
- `GET /analysis/{id}` - get one analysis (Auth required)

Authorization: `Authorization: Bearer <JWT>` from Auth0.

### Notes
- Text and files are encrypted before storage. Files use GridFS with per-file nonce metadata.
- Analysis calls are stubbed; integrate with the ML service later in `app/services/analysis_client.py`.

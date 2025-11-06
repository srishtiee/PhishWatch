# PhishWatch Backend API Contracts

Base URL: `http://localhost:8000`

All endpoints except `/health` require authentication via Auth0 JWT token.

## Authentication

All protected endpoints require:
```
Authorization: Bearer <JWT_TOKEN>
```

The JWT token must:
- Be issued by Auth0 (domain configured in `AUTH0_DOMAIN`)
- Have audience matching `AUTH0_AUDIENCE`
- Be signed with RS256 algorithm

---

## Endpoints

### 1. Health Check

**GET** `/health`

No authentication required.

**Response:**
```json
{
  "status": "ok"
}
```

**Status Codes:**
- `200 OK` - Service is healthy

---

### 2. Submit Email Header

**POST** `/analysis/header`

Submit email header text for phishing analysis.

**Authentication:** Required

**Request Body:**
```json
{
  "header_text": "Received: from mail.example.com..."
}
```

**Request Schema:**
- `header_text` (string, required): Email header text to analyze

**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user_sub": "auth0|123456789",
  "header_enc": {
    "nonce_b64": "base64-encoded-nonce",
    "ciphertext_b64": "base64-encoded-ciphertext"
  },
  "eml_file_id": null,
  "status": "completed",
  "result": {
    "is_phishing": false,
    "confidence": 0.5,
    "source": "stub"
  }
}
```

**Response Schema:**
- `_id` (string): MongoDB ObjectId as string
- `user_sub` (string): Auth0 user identifier
- `header_enc` (object, optional): Encrypted header data
  - `nonce_b64` (string): Base64-encoded nonce
  - `ciphertext_b64` (string): Base64-encoded ciphertext
- `eml_file_id` (string, optional): GridFS file ID if file was uploaded
- `status` (string): `"pending"` | `"completed"` | `"failed"`
- `result` (object, optional): ML analysis result
  - `is_phishing` (boolean): Classification result
  - `confidence` (number): Confidence score (0.0-1.0)
  - `source` (string): Source of analysis (e.g., "stub", "ml-service")

**Status Codes:**
- `200 OK` - Analysis completed successfully
- `400 Bad Request` - Missing or invalid `header_text`
- `401 Unauthorized` - Missing or invalid JWT token
- `500 Internal Server Error` - Server error during processing

---

### 3. Upload .eml File

**POST** `/analysis/file`

Upload an email file (.eml) for phishing analysis.

**Authentication:** Required

**Request:**
- Content-Type: `multipart/form-data`
- Form field: `file` (required)
  - Type: File upload
  - Accepts: `.eml` files (or any file type)

**Example (curl):**
```bash
curl -X POST http://localhost:8000/analysis/file \
  -H "Authorization: Bearer <TOKEN>" \
  -F "file=@sample.eml"
```

**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439012",
  "user_sub": "auth0|123456789",
  "header_enc": null,
  "eml_file_id": "507f1f77bcf86cd799439013",
  "status": "completed",
  "result": {
    "is_phishing": true,
    "confidence": 0.8,
    "source": "stub"
  }
}
```

**Response Schema:** Same as `/analysis/header` endpoint

**Status Codes:**
- `200 OK` - File uploaded and analyzed successfully
- `401 Unauthorized` - Missing or invalid JWT token
- `422 Unprocessable Entity` - Missing or invalid file field
- `500 Internal Server Error` - Server error during processing

---

### 4. List Analyses

**GET** `/analysis/`

Get all analyses for the authenticated user, sorted by most recent first.

**Authentication:** Required

**Response:**
```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "user_sub": "auth0|123456789",
    "header_enc": {
      "nonce_b64": "...",
      "ciphertext_b64": "..."
    },
    "eml_file_id": null,
    "status": "completed",
    "result": {
      "is_phishing": false,
      "confidence": 0.5,
      "source": "stub"
    }
  },
  {
    "_id": "507f1f77bcf86cd799439012",
    "user_sub": "auth0|123456789",
    "header_enc": null,
    "eml_file_id": "507f1f77bcf86cd799439013",
    "status": "completed",
    "result": {
      "is_phishing": true,
      "confidence": 0.8,
      "source": "stub"
    }
  }
]
```

**Response Schema:** Array of `Analysis` objects (same schema as above)

**Status Codes:**
- `200 OK` - Success (returns empty array `[]` if no analyses found)
- `401 Unauthorized` - Missing or invalid JWT token

---

### 5. Get Analysis by ID

**GET** `/analysis/{analysis_id}`

Get a specific analysis by its ID. Users can only access their own analyses.

**Authentication:** Required

**Path Parameters:**
- `analysis_id` (string, required): MongoDB ObjectId of the analysis

**Response:**
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user_sub": "auth0|123456789",
  "header_enc": {
    "nonce_b64": "...",
    "ciphertext_b64": "..."
  },
  "eml_file_id": null,
  "status": "completed",
  "result": {
    "is_phishing": false,
    "confidence": 0.5,
    "source": "stub"
  }
}
```

**Response Schema:** Same as `/analysis/header` endpoint

**Status Codes:**
- `200 OK` - Analysis found and returned
- `401 Unauthorized` - Missing or invalid JWT token
- `404 Not Found` - Analysis not found or doesn't belong to user

---

## Error Responses

All endpoints may return standard error responses:

**401 Unauthorized:**
```json
{
  "detail": "Missing Authorization header"
}
```
or
```json
{
  "detail": "Invalid token"
}
```

**404 Not Found:**
```json
{
  "detail": "Not found"
}
```

**422 Unprocessable Entity:**
```json
{
  "detail": [
    {
      "loc": ["body", "header_text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error"
}
```

---

## Data Models

### AnalysisCreate
```typescript
{
  header_text?: string  // Optional, required for /header endpoint
}
```

### Analysis
```typescript
{
  _id: string                    // MongoDB ObjectId as string
  user_sub: string              // Auth0 user identifier
  header_enc?: EncryptedText     // Encrypted header (if header submitted)
  eml_file_id?: string          // GridFS file ID (if file uploaded)
  status: "pending" | "completed" | "failed"
  result?: {
    is_phishing: boolean
    confidence: number          // 0.0-1.0
    source: string
    // ... additional ML model fields
  }
}
```

### EncryptedText
```typescript
{
  nonce_b64: string             // Base64-encoded 12-byte nonce
  ciphertext_b64: string        // Base64-encoded AES-GCM ciphertext
}
```

---

## Notes

1. **User Isolation:** All queries are automatically filtered by `user_sub` from the JWT token. Users can only access their own analyses.

2. **Encryption:** All user data (headers and files) is encrypted with AES-GCM before storage. The encryption key is configured via `ENCRYPTION_KEY_B64` environment variable.

3. **File Storage:** Uploaded `.eml` files are stored in MongoDB GridFS with encryption. The file ID is stored in `eml_file_id` field.

4. **ML Integration:** The `result` field currently contains stub data. Replace the `AnalysisClient` implementation in `app/services/analysis_client.py` to integrate with the ML service.

5. **Status Values:**
   - `pending`: Analysis is queued/processing
   - `completed`: Analysis finished successfully
   - `failed`: Analysis encountered an error


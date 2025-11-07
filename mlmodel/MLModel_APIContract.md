# API Contract: Phishing Detection Service

**Base URL:** `[Your_API_Base_URL]/v1` (e.g., `https://api.example.com/v1`)

**Service Description:** This service provides an endpoint to analyze the content of a raw email and return a probability score for it being a phishing attempt.

---

## Endpoint: POST /predict

Analyzes a single raw email string (including all headers and body) and returns a phishing probability score.

### Request

* **Method:** `POST`
* **Path:** `/predict`
* **Headers:**
    * `Content-Type: application/json`
    * `Accept: application/json`

### Request Body

* **Type:** `object`
* **Properties:**
    * `raw_email`
        * **Type:** `string`
        * **Description:** The full, raw text of an email, including all headers (From, Received, Subject, etc.) and the full body.
        * **Required:** `true`

#### Example Request Body

```json
{
  "raw_email": "Return-Path: <user@example.com>\nFrom: sender@spam.com\nTo: victim@example.com\nSubject: Urgent: Account Update!\n\nClick here now: [http://fake-link.com](http://fake-link.com)"
}
# Isotailor API

This document describes the API endpoints for the Isotailor tool.

## Endpoints

### `/api/uploads`

**Method:** `POST`

**Description:** Uploads an ISO image.

**Request Body:**

*   `iso`: (file) The ISO image to upload.

**Response:**

*   **201 Created:** Successful upload. Returns a JSON object containing the upload ID.
*   **400 Bad Request:** Invalid request.  Returns a JSON object with an error message.

### `/api/uploads/{upload_id}`

**Method:** `GET`

**Description:** Retrieves details of a specific upload.

**Response:**

*   **200 OK:** Returns a JSON object containing the upload details, including the ISO filename and software list.
*   **404 Not Found:** Upload not found. Returns a JSON object with an error message.

### `/api/uploads/{upload_id}`

**Method:** `PUT`

**Description:** Updates the software list for a specific upload.

**Request Body:**

*   `software`: (array of strings) A list of software packages to include in the tailored ISO.  Can also accept a single string.

**Response:**

*   **200 OK:** Software list updated successfully. Returns a JSON object indicating success.
*   **400 Bad Request:** Invalid request, e.g., invalid software names.  Returns a JSON object with an error message.
*   **404 Not Found:** Upload not found.  Returns a JSON object with an error message.

### `/api/uploads/{upload_id}/tailor`

**Method:** `POST`

**Description:** Starts the tailoring process for a specific upload.

**Response:**

*   **202 Accepted:** Tailoring process initiated successfully. Returns a JSON object containing the job ID.
*   **404 Not Found:** Upload not found. Returns a JSON object with an error message.

### `/api/tailoring/{job_id}`

**Method:** `GET`

**Description:** Retrieves the status of a tailoring job.

**Response:**

*   **200 OK:** Returns a JSON object containing the job status (e.g., "pending", "running", "completed", "failed") and any relevant messages.
*   **404 Not Found:** Job not found. Returns a JSON object with an error message.
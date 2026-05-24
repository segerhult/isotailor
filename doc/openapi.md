# Isotailor API

This document describes the API endpoints for the Isotailor tool.

## Endpoints

### `/api/uploads`

**Method:** `POST`

**Description:** Uploads an ISO image.

**Request Body:**

*   `iso`: (file) The ISO image to upload.

**Response:**

*   **201 Created:** A JSON object containing the upload ID.
*   **400 Bad Request:** If the upload fails due to an invalid file type or other error.

### `/api/uploads/{upload_id}`

**Method:** `GET`

**Description:** Retrieves information about a specific upload.

**Response:**

*   **200 OK:** A JSON object containing the upload details, including the upload ID, filename, upload timestamp, and selected software.
*   **404 Not Found:** If the upload ID does not exist.

### `/api/uploads/{upload_id}/software`

**Method:** `POST`

**Description:** Updates the selected software for a specific upload.

**Request Body:**

*   `software`: (array) A list of software packages to include in the tailored ISO.

**Response:**

*   **200 OK:** A JSON object confirming the update.
*   **404 Not Found:** If the upload ID does not exist.
*   **400 Bad Request:** If the software list is invalid.

### `/api/uploads`

**Method:** `GET`

**Description:** Lists all available uploads.

**Response:**

*   **200 OK:** A JSON object containing a list of upload IDs and their respective filenames.
# isotailor
Easy iso image tailor tool

isotailor is a tool that allows users to upload ISO images and select software to be included in the tailored ISO. The software can be chosen from a default list or provided as custom entries.

## Usage
1.  Navigate to the root directory of the isotailor repository.
2.  Run the server using `python server.py`.
3.  Access the isotailor web interface in your browser at `http://localhost:8000`.

## Features

*   **ISO Upload:** Upload ISO files to be tailored.
*   **Software Selection:** Choose from a predefined list of software packages or enter custom packages.
*   **Existing Uploads:** View and manage previously uploaded ISOs.
*   **Install Script Generation:** Generate a shell script to install selected software on a target system.
*   **ISO Info Endpoint:** Retrieve metadata and optional SHA-256 checksum of uploaded ISOs.
*   **Repository Statistics:** Get summary statistics including upload count and total ISO storage used.

## Data Storage

Data, including uploaded ISOs and configuration, is stored locally in the `./data` directory. It’s recommended to back up this directory to prevent loss of data.

## API
For developers, the isotailor API is available at `/api`.

### Additional API Endpoints

*   `GET /api/stats`: Returns upload count and total ISO storage usage.
    ```json
    {
      "uploads_count": 5,
      "total_iso_bytes": 1234567890,
      "time": "2025-04-05T12:34:56Z"
    }
    ```

*   `GET /api/uploads/:id/install-script`: Returns a shell install script for the selected software.

*   `GET /api/uploads/:id/info`: Returns metadata and ISO file details.
    - Query parameter `sha256=1` (or `true`/`yes`) includes SHA-256 hash if available.

### Updated API Response Headers
All API responses now include the `Access-Control-Allow-Origin: *` header and support additional HTTP methods: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`, `HEAD`.

## Documentation

- [Requirements](docs/requirements.md)
- [Environment Variables](docs/environment.md)
- [API Reference](docs/api.md)
- [Architecture Overview](docs/architecture.md)
- [Security Considerations](docs/security.md)
- [Deployment Guide](docs/deployment.md)
- [OpenAPI](docs/OPENAPI.md)
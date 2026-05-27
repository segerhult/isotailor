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
*   **Installation Script Generation:** Generate a shell script to install selected software.

## Data Storage

Data, including uploaded ISOs and configuration, is stored locally in the `./data` directory. It’s recommended to back up this directory to prevent loss of data.

## API
For developers, the isotailor API is available at `/api`.

### Endpoints

*   `GET /api/health`: Health check.
*   `GET /api/default-software`: Get the list of default software packages.
*   `GET /api/stats`: Get statistics about uploads (count and total size of ISOs).
*   `GET /api/uploads`: List all previously uploaded ISOs.
*   `POST /api/uploads`: Upload a new ISO file.
*   `GET /api/uploads/{id}`: Get details about a specific upload, including software and installation manifest.
*   `GET /api/uploads/{id}/install-script`: Get the installation script for a specific upload.
*   `GET /api/uploads/{id}/info`: Get detailed information about a specific upload, including ISO details (path, existence, size, and optional SHA256 hash).

## Documentation

- [API Reference](docs/api.md)
- [CI/CD Pipelines](docs/pipelines.md)
- [Docker Configuration](docs/docker.md)
- [Nginx Configuration](docs/nginx.md)
- [OpenAPI](docs/OPENAPI.md)
- [Deployment Guide](docs/deployment.md)
- [Requirements](docs/requirements.md)
- [Environment Variables](docs/environment.md)
- [Architecture Overview](docs/architecture.md)
- [Security Considerations](docs/security.md)
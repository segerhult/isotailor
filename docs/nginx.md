# Nginx

## Configuration File

The primary Nginx configuration file is located at `web/nginx.conf`. This file configures Nginx as a reverse proxy, forwarding requests to the backend application.

## Usage

The `nginx.conf` file defines how Nginx handles incoming requests. It includes directives for:

*   **Reverse Proxying:**  Directing traffic to the backend application.
*   **Static Content Serving:** Serving static assets.

## Running Nginx

Nginx is run as part of the Docker Compose setup defined in `docker-compose.yml`. Instructions for running the application locally can be found in the [README.md](README.md).  CI/CD workflows are defined in `.github/workflows/main.yml`.

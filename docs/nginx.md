# Nginx Configuration

This document describes the Nginx configuration used within the project.

## Configuration File

The primary Nginx configuration file is located at `web/nginx.conf`.  This file configures Nginx as a reverse proxy and static file server for the frontend application.

## Usage

The `nginx.conf` file serves the static assets of the frontend application and proxies requests to the Python server.

## Local Development and CI

Refer to the `docker-compose.yml` file for instructions on running the application with Nginx locally.  The CI workflow defined in `.github/workflows/main.yml` also utilizes Nginx for serving the application during builds and tests.

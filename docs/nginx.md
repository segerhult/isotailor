# Nginx Configuration

This document details the Nginx configuration used within the project.

## Configuration File

The primary Nginx configuration file is located at: `web/nginx.conf`. This file defines how Nginx serves the web application. Refer to the file itself for detailed configuration specifics.

## Usage

The `web/nginx.conf` file configures Nginx as a reverse proxy, forwarding requests to the web application running on port 8000. It also serves static files.

## Local Development and CI

To run Nginx locally, refer to the instructions in the [README.md](README.md) file, which outlines the process for building and running the application and its associated services (including Nginx). Continuous Integration (CI) builds and tests also utilize this configuration.
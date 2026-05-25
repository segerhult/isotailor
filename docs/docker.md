# Docker

## Overview
This repository includes a `Dockerfile` for the backend and a `Dockerfile` within the `web/` directory for the frontend. A `docker-compose.yml` file is provided to orchestrate both containers.

## Install
- Docker Desktop / Engine: https://docs.docker.com/get-docker/
- Docker Compose: https://docs.docker.com/compose/

## Image Details

### Backend
- Base image: `python:3.11-slim`

#### System Packages
- `curl`
- `git`
- `htop`
- `nano`
- `openssh-server`
- `python3`
- `rsync`
- `sudo`
- `vim`
- `wget`

### Frontend
See `web/Dockerfile` for details.

## Build

To build the application, run the following command from the root of the repository: